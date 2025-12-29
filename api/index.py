from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'StayScout Test - Flask is working!'

@app.route('/<path:path>')
def catch_all(path):
    return f'Path: {path}'
