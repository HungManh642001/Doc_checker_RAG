"""
Simplified API endpoints for RAG-based document analysis
No preview step - direct upload to analysis
"""

from flask import Blueprint, request, jsonify, send_file
import os
import uuid
from werkzeug.utils import secure_filename
from app.rag_analyzer import make_analyzer
from app.document_processor import DocumentProcessor

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Store session metadata
_sessions = {}

ALLOWED_EXTENSIONS = {'docx', 'doc', 'pdf', 'html'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@api_bp.route('/upload', methods=['POST'])
def upload_and_analyze():
    """
    Upload documents and run analysis immediately
    
    Files expected:
    - mainDocument: DOCX file to analyze
    - referenceDocuments: DOCX files for building knowledge base
    - ruleDocuments: DOCX files with regulations
    """
    try:
        # Validate main document
        if 'mainDocument' not in request.files:
            return jsonify({'error': 'Main document (mainDocument) is required'}), 400
        
        main_doc = request.files['mainDocument']
        if not main_doc.filename or not allowed_file(main_doc.filename):
            return jsonify({'error': 'Main document must be .docx format'}), 400
        
        # Get reference and rule documents
        reference_docs = request.files.getlist('referenceDocuments')
        rule_docs = request.files.getlist('ruleDocuments')
        
        # Combine reference and rule docs
        all_ref_docs = reference_docs + rule_docs
        
        if not all_ref_docs:
            return jsonify({
                'warning': 'No reference documents provided. Analysis may be less accurate.'
            }), 400
        
        # Create session directory
        session_id = str(uuid.uuid4())
        upload_dir = os.path.join(
            os.path.dirname(__file__), '..', 'uploads', session_id
        )
        os.makedirs(upload_dir, exist_ok=True)
        
        try:
            # Save main document
            main_filename = secure_filename(main_doc.filename or 'main.docx')
            main_path = os.path.join(upload_dir, main_filename)
            main_doc.save(main_path)
            print(f"[API] Saved main document: {main_filename}")
            
            # Save reference documents
            ref_paths = []
            for ref_doc in all_ref_docs:
                if ref_doc and ref_doc.filename and allowed_file(ref_doc.filename):
                    ref_filename = secure_filename(ref_doc.filename)
                    ref_path = os.path.join(upload_dir, f'ref_{len(ref_paths)}_{ref_filename}')
                    ref_doc.save(ref_path)
                    ref_paths.append(ref_path)
                    print(f"[API] Saved reference: {ref_filename}")
            
            # Tạo analyzer riêng cho session này và dựng index từ sở cứ upload
            print("[API] Đang dựng index từ sở cứ...")
            analyzer = make_analyzer()

            if not analyzer.initialize_rag_system(ref_paths):
                return jsonify({
                    'error': 'Failed to initialize RAG system. Check logs for details.'
                }), 500
            
            # Run analysis
            print("[API] Running document analysis...")
            errors = analyzer.analyze_document(main_path)
            
            # Lưu session, kèm analyzer để cleanup sau
            _sessions[session_id] = {
                'main_path': main_path,
                'ref_paths': ref_paths,
                'upload_dir': upload_dir,
                'analyzer': analyzer,
                'errors': errors,
                'error_count': len(errors)
            }
            
            print(f"[API] Analysis complete: {len(errors)} errors found")
            
            return jsonify({
                'success': True,
                'sessionId': session_id,
                'message': 'Document analyzed successfully',
                'results': {
                    'errorCount': len(errors),
                    'errors': errors
                }
            }), 200
        
        except Exception as e:
            print(f"[API] Error during analysis: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': f'Analysis failed: {str(e)}'
            }), 500
    
    except Exception as e:
        print(f"[API] Upload error: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/session/<session_id>', methods=['GET'])
def get_session_results(session_id):
    """
    Get analysis results for a session
    """
    if session_id not in _sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = _sessions[session_id]
    return jsonify({
        'sessionId': session_id,
        'results': {
            'errorCount': session['error_count'],
            'errors': session['errors']
        }
    }), 200


@api_bp.route('/session/<session_id>/apply-suggestions', methods=['POST'])
def apply_suggestions(session_id):
    """
    Áp dụng các gợi ý được chấp nhận vào tài liệu và xuất file DOCX đã sửa.

    Expected JSON:
    {
        "updates": [
            {
                "errorId": "error_c0_1",
                "action": "accept" | "reject" | "custom",
                "fixedValue": "..."   // tuỳ chọn: giá trị người dùng tự nhập
            }
        ]
    }

    Response:
    {
        "success": true,
        "appliedCount": 3,
        "downloadUrl": "/api/session/<id>/download"
    }
    """
    try:
        if session_id not in _sessions:
            return jsonify({'error': 'Session not found'}), 404

        data = request.get_json()
        if not data or 'updates' not in data:
            return jsonify({'error': 'Trường "updates" là bắt buộc'}), 400

        session = _sessions[session_id]
        errors_by_id = {e['id']: e for e in session.get('errors', [])}
        updates = data['updates']

        # Xây danh sách thay thế text cho các lỗi được chấp nhận
        text_corrections = []
        for update in updates:
            if update.get('action') == 'reject':
                continue

            error = errors_by_id.get(update.get('errorId'))
            if not error:
                continue

            original_text = error.get('original_text', '').strip()
            if not original_text:
                continue

            # Ưu tiên: giá trị người dùng nhập tay > suggestion của AI
            new_text = (
                update.get('fixedValue')
                or update.get('customSuggestion')
                or error.get('suggestion', '')
            ).strip()

            if new_text:
                text_corrections.append({
                    'original_text': original_text,
                    'new_text': new_text,
                })

        if not text_corrections:
            return jsonify({
                'success': True,
                'appliedCount': 0,
                'message': 'Không có sửa lỗi nào được chấp nhận.',
            }), 200

        # Áp dụng vào file DOCX
        main_path = session['main_path']
        base_name = os.path.splitext(os.path.basename(main_path))[0]
        corrected_path = os.path.join(session['upload_dir'], f'{base_name}_corrected.docx')

        processor = DocumentProcessor()
        applied = processor.apply_text_corrections(main_path, corrected_path, text_corrections)

        session['corrected_path'] = corrected_path
        print(f"[API] Đã áp dụng {applied} sửa lỗi → {corrected_path}")

        return jsonify({
            'success': True,
            'appliedCount': applied,
            'downloadUrl': f'/api/session/{session_id}/download',
        }), 200

    except Exception as e:
        print(f"[API] Lỗi apply suggestions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/session/<session_id>/download', methods=['GET'])
def download_corrected(session_id):
    """Tải về file DOCX đã được sửa lỗi."""
    if session_id not in _sessions:
        return jsonify({'error': 'Session not found'}), 404

    session = _sessions[session_id]
    corrected_path = session.get('corrected_path')

    if not corrected_path or not os.path.exists(corrected_path):
        return jsonify({
            'error': 'Chưa có file đã sửa. Hãy gọi apply-suggestions trước.'
        }), 404

    download_name = os.path.basename(corrected_path)
    return send_file(corrected_path, as_attachment=True, download_name=download_name)


@api_bp.route('/session/<session_id>/cleanup', methods=['DELETE'])
def cleanup_session(session_id):
    """
    Clean up session resources
    """
    if session_id in _sessions:
        session = _sessions.pop(session_id)

        # Đóng Qdrant client của session này
        analyzer = session.get('analyzer')
        if analyzer:
            analyzer.cleanup()

        # Xoá thư mục upload
        import shutil
        if os.path.exists(session['upload_dir']):
            try:
                shutil.rmtree(session['upload_dir'])
                print(f"[API] Đã xoá session {session_id}")
            except Exception:
                pass
    
    return jsonify({'success': True, 'message': 'Session cleaned up'}), 200


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'sessions': len(_sessions)
    }), 200
