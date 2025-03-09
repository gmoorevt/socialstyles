from flask import render_template, current_app
from flask_mail import Message
from threading import Thread
from . import mail
import boto3
from botocore.exceptions import ClientError
import logging
import os
import sys

# Set up logging
logger = logging.getLogger(__name__)
# Configure logging to print to console
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

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
    logger.info(f"AWS_ACCESS_KEY_ID={app.config.get('AWS_ACCESS_KEY_ID', 'Not set')[:4] if app.config.get('AWS_ACCESS_KEY_ID') else 'Not set'}...")
    logger.info(f"MAIL_DEFAULT_SENDER={app.config.get('MAIL_DEFAULT_SENDER')}")
    
    # Force using AWS SES if configured
    use_ses = app.config.get('USE_SES', False)
    if use_ses:
        logger.info("Attempting to send email using AWS SES")
        # Send email using AWS SES
        success = send_email_ses(to, subject, text_body, html_body, app)
        if not success:
            logger.warning("SES failed, but USE_SES is True. Not falling back to Flask-Mail.")
            return False
        return True
    else:
        logger.info("Using Flask-Mail for email delivery")
        # Send email using Flask-Mail
        try:
            msg = Message(subject, recipients=[to])
            msg.body = text_body
            msg.html = html_body
            Thread(target=send_async_email, args=(app, msg)).start()
            return True
        except Exception as e:
            logger.error(f"Error sending email via Flask-Mail: {str(e)}")
            return False

def send_email_ses(to, subject, text_body, html_body, app):
    """Send email using AWS SES."""
    try:
        # Create a new SES resource
        logger.info(f"Creating SES client with region={app.config['AWS_REGION']}")
        
        # Check if all required AWS SES configuration is present
        if not app.config.get('AWS_REGION'):
            logger.error("AWS_REGION is not set")
            return False
        if not app.config.get('AWS_ACCESS_KEY_ID'):
            logger.error("AWS_ACCESS_KEY_ID is not set")
            return False
        if not app.config.get('AWS_SECRET_ACCESS_KEY'):
            logger.error("AWS_SECRET_ACCESS_KEY is not set")
            return False
        if not app.config.get('MAIL_DEFAULT_SENDER'):
            logger.error("MAIL_DEFAULT_SENDER is not set")
            return False
            
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
        return True
    except ClientError as e:
        logger.error(f"Error sending email via SES: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email via SES: {str(e)}")
        return False 