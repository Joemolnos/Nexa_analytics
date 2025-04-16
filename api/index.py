from flask import Flask, Response
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app from app.py
from app import app

# WSGI handler
def application(environ, start_response):
    return app(environ, start_response)
