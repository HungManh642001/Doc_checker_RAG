from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Debug is OFF by default. Enable ONLY in local dev via FLASK_DEBUG=1.
    # Never enable in production: the Werkzeug debugger allows remote code execution.
    debug = os.environ.get('FLASK_DEBUG', '0').strip() in ('1', 'true', 'True')
    app.run(debug=debug, host='0.0.0.0', port=port)
