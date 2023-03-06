from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['CORS_ALLOWED_ORIGINS'] = ['http://localhost:3001']  # Add your client domain/port here
app.config['CORS_SUPPORTS_CREDENTIALS'] = True
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3001")

@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)
    emit('recommendations', generate_recommendations(message))



def generate_recommendations(message):
    # Your code to generate food recommendations goes here
    return 'Recommendations generated successfully'

if __name__ == '__main__':
    socketio.run(app, port=5001, debug=True)
