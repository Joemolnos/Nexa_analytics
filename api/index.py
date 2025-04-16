from flask import Flask, Response
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app from app.py
from app import app

# Vercel serverless function handler
def handler(request):
    return app(request.environ, lambda status, headers, exc_info=None: Response(None, status, headers))
