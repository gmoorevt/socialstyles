from flask import render_template, current_app
from flask_mail import Message
from threading import Thread
from . import mail

def send_async_email(app, msg):
    """Send email asynchronously."""
    with app.app_context():
        mail.send(msg)

def send_email(to, subject, template, **kwargs):
    """Send an email."""
    app = current_app._get_current_object()
    msg = Message(subject, recipients=[to])
    msg.body = render_template(f'{template}.txt', **kwargs)
    msg.html = render_template(f'{template}.html', **kwargs)
    
    # Send email asynchronously
    Thread(target=send_async_email, args=(app, msg)).start() 