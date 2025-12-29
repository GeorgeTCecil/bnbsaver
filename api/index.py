"""
StayScout - Vercel Serverless Entry Point
"""
import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application import app

# Vercel expects the WSGI app to be named 'app'
# This is already named 'app' in application.py, so we just import and expose it
