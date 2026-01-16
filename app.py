from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import io
import traceback
import contextlib
import threading

app = Flask(__name__)
CORS(app)

class TimeoutException(Exception):
    pass

def run_with_timeout(code, timeout=5):
    """Run code with a timeout using threading"""
    result = {'output': '', 'error': None, 'success': False, 'timed_out': False}
    
    def target():
        try:
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                exec_globals = {
                    '__builtins__': __builtins__,
                    'print': print,
                }
                exec(code, exec_globals)
            
            result['output'] = stdout_capture.getvalue()
            result['error'] = stderr_capture.getvalue()
            result['success'] = True
            
        except Exception as e:
            result['error'] = traceback.format_exc()
            result['success'] = False
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        result['timed_out'] = True
        result['error'] = 'Code execution timed out (max 5 seconds)'
        result['success'] = False
    
    return result

@app.route('/execute', methods=['POST'])
def execute_code():
    try:
        data = request.get_json()
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        if language.lower() != 'python':
            return jsonify({'error': f'Language {language} not supported. Only Python is supported.'}), 400
        
        result = run_with_timeout(code, timeout=5)
        
        return jsonify({
            'output': result['output'],
            'error': result['error'] if result['error'] else None,
            'success': result['success']
        })
            
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}',
            'success': False
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Code execution server is running'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Multi-Language Code Runner API',
        'endpoints': {
            '/health': 'GET - Health check',
            '/execute': 'POST - Execute Python code'
        }
    })

if __name__ == '__main__':
    print("Starting code execution server...")
    print("Server will run on http://localhost:5000")
    print("Available endpoints:")
    print("  POST /execute - Execute code")
    print("  GET  /health  - Health check")
    app.run(debug=True, host='0.0.0.0', port=5000)
