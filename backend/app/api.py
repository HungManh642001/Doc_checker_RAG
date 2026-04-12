from flask import Blueprint, request, jsonify, send_file
from app.document_processor import DocumentProcessor
from app.ai_simulator import AISimulator
import os
import uuid

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/upload', methods=['POST'])
def upload_documents():
    """
    Upload documents: main document, reference documents, and regulations
    """
    try:
        if 'mainDocument' not in request.files:
            return jsonify({'error': 'Main document is required'}), 400
        
        main_doc = request.files['mainDocument']
        reference_docs = request.files.getlist('referenceDocuments')
        regulations = request.files.getlist('regulations')
        
        if not main_doc.filename.endswith('.docx'):
            return jsonify({'error': 'Main document must be .docx format'}), 400
        
        # Generate unique ID for this session
        session_id = str(uuid.uuid4())
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', session_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save main document
        main_path = os.path.join(upload_dir, 'main.docx')
        main_doc.save(main_path)
        
        # Save reference documents
        ref_docs_paths = []
        for ref_doc in reference_docs:
            if ref_doc.filename and ref_doc.filename.endswith('.docx'):
                ref_path = os.path.join(upload_dir, f'ref_{len(ref_docs_paths)}.docx')
                ref_doc.save(ref_path)
                ref_docs_paths.append(ref_path)
        
        # Save regulations
        reg_paths = []
        for reg_doc in regulations:
            if reg_doc.filename and reg_doc.filename.endswith('.docx'):
                reg_path = os.path.join(upload_dir, f'reg_{len(reg_paths)}.docx')
                reg_doc.save(reg_path)
                reg_paths.append(reg_path)
        
        # Process documents
        processor = DocumentProcessor()
        main_content = processor.extract_text_with_positions(main_path)
        
        return jsonify({
            'sessionId': session_id,
            'message': 'Documents uploaded successfully',
            'documentsCount': {
                'reference': len(ref_docs_paths),
                'regulations': len(reg_paths)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/document/<session_id>', methods=['GET'])
def get_document_preview(session_id):
    """
    Get document content for preview (text extraction with paragraph/table info)
    """
    try:
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', session_id)
        main_path = os.path.join(upload_dir, 'main.docx')
        
        if not os.path.exists(main_path):
            return jsonify({'error': 'Document not found'}), 404
        
        processor = DocumentProcessor()
        content = processor.extract_text_with_positions(main_path)
        
        return jsonify({
            'sessionId': session_id,
            'content': content
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/references/<session_id>', methods=['GET'])
def get_references(session_id):
    """
    Get content from reference documents and regulations for citation
    """
    try:
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', session_id)
        processor = DocumentProcessor()
        
        references_data = {
            'regulations': [],
            'references': []
        }
        
        # Extract regulations
        for i in range(10):  # Check up to 10 files
            reg_path = os.path.join(upload_dir, f'reg_{i}.docx')
            if os.path.exists(reg_path):
                content = processor.extract_text_with_positions(reg_path)
                text_summary = ' '.join([p['text'] for p in content.get('paragraphs', [])])[:500]
                references_data['regulations'].append({
                    'id': f'reg_{i}',
                    'name': f'Quy định {i+1}',
                    'preview': text_summary
                })
        
        # Extract reference documents
        for i in range(10):  # Check up to 10 files
            ref_path = os.path.join(upload_dir, f'ref_{i}.docx')
            if os.path.exists(ref_path):
                content = processor.extract_text_with_positions(ref_path)
                text_summary = ' '.join([p['text'] for p in content.get('paragraphs', [])])[:500]
                references_data['references'].append({
                    'id': f'ref_{i}',
                    'name': f'Văn bản sở cứ {i+1}',
                    'preview': text_summary
                })
        
        return jsonify({
            'sessionId': session_id,
            'data': references_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/analyze/<session_id>', methods=['POST'])
def analyze_document(session_id):
    """
    Analyze the main document and return errors with suggestions
    """
    try:
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', session_id)
        main_path = os.path.join(upload_dir, 'main.docx')
        
        if not os.path.exists(main_path):
            return jsonify({'error': 'Document not found'}), 404
        
        # Extract content
        processor = DocumentProcessor()
        content = processor.extract_text_with_positions(main_path)
        
        # Simulate AI analysis
        ai = AISimulator()
        errors = ai.analyze_document(content)
        
        return jsonify({
            'sessionId': session_id,
            'errors': errors
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/apply-suggestions/<session_id>', methods=['POST'])
def apply_suggestions(session_id):
    """
    Apply accepted suggestions to the document and generate corrected version
    Filters out rejected errors and uses custom values or suggestions
    """
    try:
        data = request.get_json()
        accepted_suggestions = data.get('acceptedSuggestions', [])
        
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', session_id)
        main_path = os.path.join(upload_dir, 'main.docx')
        output_path = os.path.join(upload_dir, 'main_corrected.docx')
        
        # Transform accepted suggestions to corrections format
        # Skip rejected errors and use fixedValue if available
        corrections = []
        for suggestion in accepted_suggestions:
            # Skip rejected suggestions (if status is included)
            if suggestion.get('status') == 'rejected':
                continue
            
            # Use fixedValue if available (from manual edit), otherwise use suggestion
            fixed_value = suggestion.get('fixedValue', suggestion.get('suggestion'))
            
            correction = {
                'elementId': suggestion.get('elementId'),
                'type': suggestion.get('elementType', 'text'),
                'oldText': suggestion.get('errorText'),
                'newText': fixed_value
            }
            corrections.append(correction)
        
        # Apply corrections to the document
        processor = DocumentProcessor()
        processor.apply_corrections(main_path, output_path, corrections)
        
        return jsonify({
            'message': 'Corrections applied successfully',
            'downloadUrl': f'/api/download/{session_id}/main_corrected.docx',
            'appliedCount': len(corrections)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/download/<session_id>/<filename>', methods=['GET'])
def download_file(session_id, filename):
    """
    Download the corrected document
    """
    try:
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', session_id)
        file_path = os.path.join(upload_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/save-and-reupload/<session_id>', methods=['POST'])
def save_and_reupload(session_id):
    """
    Save modified document with all updates and prepare for re-analysis
    Preserves original DOCX format with all formatting
    """
    try:
        data = request.get_json()
        content_updates = data.get('contentUpdates', {})
        
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', session_id)
        main_path = os.path.join(upload_dir, 'main.docx')
        updated_path = os.path.join(upload_dir, 'main_updated.docx')
        
        if not os.path.exists(main_path):
            return jsonify({'error': 'Document not found'}), 404
        
        # Transform content updates to corrections format
        processor = DocumentProcessor()
        corrections = []
        
        # Process each element ID that has updates
        for element_id, updates in content_updates.items():
            if not updates:
                continue
            
            # If there's a 'manual' update, use that (free-form content edit)
            if 'manual' in updates:
                corrections.append({
                    'elementId': element_id,
                    'type': 'text',
                    'newText': updates['manual']
                })
            else:
                # Otherwise apply error-based updates
                # Just use the last update (or could merge all)
                last_update = list(updates.values())[-1] if updates else None
                if last_update:
                    corrections.append({
                        'elementId': element_id,
                        'type': 'text',
                        'newText': last_update
                    })
        
        # Apply all corrections to create updated document
        processor.apply_corrections(main_path, updated_path, corrections)
        
        # Re-extract content for re-analysis
        new_content = processor.extract_text_with_positions(updated_path)
        
        # Re-run analysis
        ai = AISimulator()
        new_errors = ai.analyze_document(new_content)
        
        return jsonify({
            'message': 'Document saved and ready for re-review',
            'updatedPath': updated_path,
            'sessionId': session_id,
            'content': new_content,
            'errors': new_errors,
            'updateCount': len(corrections)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200
