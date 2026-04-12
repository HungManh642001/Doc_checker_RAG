"""
Simplified API endpoints for RAG-based document analysis
No preview step - direct upload to analysis
"""

from flask import Blueprint, request, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
from app.rag_analyzer import get_rag_analyzer, reset_rag_analyzer

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
            
            # Initialize RAG system with reference documents
            print("[API] Initializing RAG system...")
            analyzer = get_rag_analyzer()
            
            if not analyzer.initialize_rag_system(ref_paths):
                return jsonify({
                    'error': 'Failed to initialize RAG system. Check logs for details.'
                }), 500
            
            # Run analysis
            print("[API] Running document analysis...")
            errors = analyzer.analyze_document(main_path)
            
            # Store session data
            _sessions[session_id] = {
                'main_path': main_path,
                'ref_paths': ref_paths,
                'upload_dir': upload_dir,
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
    Apply user-approved suggestions to document
    
    Expected JSON:
    {
        'updates': [
            {
                'errorId': 'error_...',
                'action': 'accept' | 'reject' | 'custom',
                'customSuggestion': '...'  # if action is 'custom'
            }
        ]
    }
    """
    try:
        if session_id not in _sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json()
        if not data or 'updates' not in data:
            return jsonify({'error': 'Updates data is required'}), 400
        
        session = _sessions[session_id]
        updates = data['updates']
        
        # Track which errors are accepted
        accepted_errors = []
        for update in updates:
            if update.get('action') == 'accept':
                accepted_errors.append(update.get('errorId'))
        
        # Update session
        session['accepted_updates'] = updates
        
        return jsonify({
            'success': True,
            'message': f'Applied {len(accepted_errors)} suggestions',
            'acceptedCount': len(accepted_errors)
        }), 200
    
    except Exception as e:
        print(f"[API] Error applying suggestions: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/session/<session_id>/cleanup', methods=['DELETE'])
def cleanup_session(session_id):
    """
    Clean up session resources
    """
    if session_id in _sessions:
        session = _sessions[session_id]
        
        # Clean up uploaded files
        import shutil
        if os.path.exists(session['upload_dir']):
            try:
                shutil.rmtree(session['upload_dir'])
                print(f"[API] Cleaned up session {session_id}")
            except:
                pass
        
        # Remove from memory
        del _sessions[session_id]
    
    # Reset analyzer
    reset_rag_analyzer()
    
    return jsonify({'success': True, 'message': 'Session cleaned up'}), 200


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'sessions': len(_sessions)
    }), 200
