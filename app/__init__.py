from flask import Flask

# Initialize the Flask application
application = Flask(__name__)

# Import routes to associate them with the application
from app import routes
