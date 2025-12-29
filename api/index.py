"""
StayScout - Vercel Serverless Entry Point
"""
from flask import Flask, jsonify
import sys
import os

# Simple test app to verify deployment works
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'alive',
        'message': 'StayScout test deployment',
        'python_version': sys.version,
        'cwd': os.getcwd(),
        'files': os.listdir('.')[:20]
    })

@app.route('/test-import')
def test_import():
    errors = []
    imports = {}

    # Test each import
    try:
        import demo_results
        imports['demo_results'] = 'OK'
    except Exception as e:
        imports['demo_results'] = str(e)
        errors.append(f'demo_results: {e}')

    try:
        from application import app as main_app
        imports['application'] = 'OK'
    except Exception as e:
        imports['application'] = str(e)
        errors.append(f'application: {e}')

    return jsonify({
        'imports': imports,
        'errors': errors,
        'sys_path': sys.path[:5]
    })
