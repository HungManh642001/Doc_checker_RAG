from flask import Flask
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Check which API to use (RAG Simplified by default)
    use_rag = os.getenv('USE_RAG_API', 'true').lower() == 'true'
    
    if use_rag:
        print("[Flask] Using RAG Simplified API")
        try:
            from app.api_simplified import api_bp
            app.register_blueprint(api_bp)
        except ImportError as e:
            print(f"[Flask] Warning: RAG API import failed: {e}")
            print("[Flask] Falling back to legacy API")
            from app.api import api_bp
            app.register_blueprint(api_bp)
    else:
        print("[Flask] Using Legacy API")
        from app.api import api_bp
        app.register_blueprint(api_bp)
    
    return app
