"""
StayScout - Vercel Serverless Entry Point
"""
import sys
import os

# Add parent directory to path so we can import our modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Change working directory to parent so Flask can find templates
os.chdir(parent_dir)

try:
    from application import app
except Exception as e:
    # Fallback: create a simple Flask app to show the error
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route('/')
    def error():
        return jsonify({
            'error': 'Import failed',
            'message': str(e),
            'path': sys.path,
            'cwd': os.getcwd()
        }), 500

# Vercel expects the WSGI app to be named 'app'
