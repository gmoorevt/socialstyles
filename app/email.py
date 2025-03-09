from flask import render_template, current_app
from flask_mail import Message
from threading import Thread
from . import mail
import boto3
from botocore.exceptions import ClientError
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)
# Configure logging to print to console
logging.basicConfig(level=logging.INFO)

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
    
    # Debug logging
    logger.info(f"Email configuration: USE_SES={app.config.get('USE_SES')}")
    logger.info(f"AWS_REGION={app.config.get('AWS_REGION')}")
    logger.info(f"AWS_ACCESS_KEY_ID={app.config.get('AWS_ACCESS_KEY_ID', 'Not set')[:4]}...")
    logger.info(f"MAIL_DEFAULT_SENDER={app.config.get('MAIL_DEFAULT_SENDER')}")
    
    # Check if AWS SES should be used
    if app.config.get('USE_SES', False):
        logger.info("Attempting to send email using AWS SES")
        # Send email using AWS SES
        send_email_ses(to, subject, text_body, html_body, app)
    else:
        logger.info("Falling back to Flask-Mail for email delivery")
        # Send email using Flask-Mail
        msg = Message(subject, recipients=[to])
        msg.body = text_body
        msg.html = html_body
        Thread(target=send_async_email, args=(app, msg)).start()

def send_email_ses(to, subject, text_body, html_body, app):
    """Send email using AWS SES."""
    try:
        # Create a new SES resource
        logger.info(f"Creating SES client with region={app.config['AWS_REGION']}")
        client = boto3.client(
            'ses',
            region_name=app.config['AWS_REGION'],
            aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY']
        )
        
        # Try to send the email
        logger.info(f"Sending email via SES to {to}")
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
        logger.info("Falling back to Flask-Mail for email delivery")
        msg = Message(subject, recipients=[to])
        msg.body = text_body
        msg.html = html_body
        Thread(target=send_async_email, args=(app, msg)).start()
    except Exception as e:
        logger.error(f"Unexpected error sending email via SES: {str(e)}")
        # Fall back to Flask-Mail for any other errors
        logger.info("Falling back to Flask-Mail for email delivery")
        msg = Message(subject, recipients=[to])
        msg.body = text_body
        msg.html = html_body
        Thread(target=send_async_email, args=(app, msg)).start() 