from flask_socketio import SocketIO

socketio = SocketIO()

def init_websockets(app):
    """Initialize the WebSocket functionality"""
    socketio.init_app(app, cors_allowed_origins="*")
    
    from . import events 