from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import io
import traceback
import signal
import contextlib

app = Flask(__name__)
CORS(app)

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Code execution timed out")

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
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)
        
        try:
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                exec_globals = {
                    '__builtins__': __builtins__,
                    'print': print,
                }
                
                exec(code, exec_globals)
            
            signal.alarm(0)
            
            output = stdout_capture.getvalue()
            errors = stderr_capture.getvalue()
            
            return jsonify({
                'output': output,
                'error': errors if errors else None,
                'success': True
            })
            
        except TimeoutException:
            signal.alarm(0)
            return jsonify({
                'output': '',
                'error': 'Code execution timed out (max 5 seconds)',
                'success': False
            })
        except Exception as e:
            signal.alarm(0)
            error_msg = traceback.format_exc()
            return jsonify({
                'output': stdout_capture.getvalue(),
                'error': error_msg,
                'success': False
            })
            
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}',
            'success': False
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Code execution server is running'})

if __name__ == '__main__':
    print("Starting code execution server...")
    print("Server will run on https://water-filter-app.onrender.com")
    print("Available endpoints:")
    print("  POST /execute - Execute code")
    print("  GET  /health  - Health check")
    app.run(debug=True, host='0.0.0.0', )