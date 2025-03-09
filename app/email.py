from flask import render_template, current_app
from flask_mail import Message
from threading import Thread
from . import mail
import boto3
from botocore.exceptions import ClientError
import logging

# Set up logging
logger = logging.getLogger(__name__)

def send_async_email(app, msg):
    """Send email asynchronously."""
    with app.app_context():
        mail.send(msg)

def send_email(to, subject, template, **kwargs):
    """Send an email."""
    app = current_app._get_current_object()
    
    # Render the email templates
    text_body = render_template(f'{template}.txt', **kwargs)
    html_body = render_template(f'{template}.html', **kwargs)
    
    # Check if AWS SES should be used
    if app.config.get('USE_SES', False):
        # Send email using AWS SES
        send_email_ses(to, subject, text_body, html_body, app)
    else:
        # Send email using Flask-Mail
        msg = Message(subject, recipients=[to])
        msg.body = text_body
        msg.html = html_body
        Thread(target=send_async_email, args=(app, msg)).start()

def send_email_ses(to, subject, text_body, html_body, app):
    """Send email using AWS SES."""
    try:
        # Create a new SES resource
        client = boto3.client(
            'ses',
            region_name=app.config['AWS_REGION'],
            aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY']
        )
        
        # Try to send the email
        response = client.send_email(
            Destination={
                'ToAddresses': [to],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': 'UTF-8',
                        'Data': html_body,
                    },
                    'Text': {
                        'Charset': 'UTF-8',
                        'Data': text_body,
                    },
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': subject,
                },
            },
            Source=app.config['MAIL_DEFAULT_SENDER'],
        )
        logger.info(f"Email sent via SES! Message ID: {response['MessageId']}")
    except ClientError as e:
        logger.error(f"Error sending email via SES: {e.response['Error']['Message']}")
        # Fall back to Flask-Mail if SES fails
        msg = Message(subject, recipients=[to])
        msg.body = text_body
        msg.html = html_body
        Thread(target=send_async_email, args=(app, msg)).start()
        logger.info("Falling back to Flask-Mail for email delivery")
    except Exception as e:
        logger.error(f"Unexpected error sending email via SES: {str(e)}")
        # Fall back to Flask-Mail for any other errors
        msg = Message(subject, recipients=[to])
        msg.body = text_body
        msg.html = html_body
        Thread(target=send_async_email, args=(app, msg)).start()
        logger.info("Falling back to Flask-Mail for email delivery") 