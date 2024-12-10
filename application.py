from app import application  # Import the Flask instance 'application' from app/__init__.py

if __name__ == "__main__":
    application.run(debug=True)  # Use 'application' instead of 'app'
