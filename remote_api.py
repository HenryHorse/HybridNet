from flask import Flask, request, jsonify
from server_launcher import launch_server
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_TOKEN = os.getenv('REMOTE_SERVER_TOKEN')
app = Flask(__name__)

@app.route('/start', methods=['POST'])
def start():
    auth = request.headers.get("Authorization")
    if auth != f"Bearer {SECRET_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 403
    launch_server()
    return jsonify({'status': 'started'}), 200

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9998)