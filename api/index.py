from flask import Flask, request

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return f'''
    <h1>StayScout Test</h1>
    <p>Flask is working!</p>
    <p>Path: /{path}</p>
    <p>Request method: {request.method}</p>
    '''

# Vercel serverless handler
def handler(event, context):
    return app(event, context)
