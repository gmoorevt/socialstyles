from flask_socketio import emit, join_room
from flask import request
from . import socketio

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    pass

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    pass

@socketio.on('join')
def handle_join(data):
    """Handle client joining a specific room"""
    room = data.get('room')
    if room:
        join_room(room)
        emit('status', {'message': 'Joined room: ' + room}, room=room)

def broadcast_new_assessment(team_id, user_id, user_name, assertiveness_score, responsiveness_score):
    """Broadcast new assessment results to all clients in the team room"""
    socketio.emit('new_assessment_result', {
        'team_id': team_id,
        'user_id': user_id,
        'user_name': user_name,
        'assertiveness_score': assertiveness_score,
        'responsiveness_score': responsiveness_score
    }, room=f'team_{team_id}') 