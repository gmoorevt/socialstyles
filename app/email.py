from flask import render_template, current_app
from threading import Thread
from . import mail
import boto3
from botocore.exceptions import ClientError
import logging
import os
import sys
import dotenv

dotenv.load_dotenv()




logger = logging.getLogger(__name__)
# Configure logging to print to console
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def send_email(to, subject, template, **kwargs):
    """Send an email."""
     # Get configuration from environment variables
    aws_region = os.environ.get('AWS_REGION')
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    sender_email = os.environ.get('MAIL_DEFAULT_SENDER')    
    
    # Render the email templates
    text_body = render_template(f'{template}.txt', **kwargs)
    html_body = render_template(f'{template}.html', **kwargs)
   

    logger.info("Attempting to send email using AWS SES")
    # Send email using AWS SES
    try:
        
        client = boto3.client(
            'ses',
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
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
            Source=sender_email,
        )
        logger.info(f"Email sent via SES! Message ID: {response['MessageId']}")
        return True
    except ClientError as e:
        logger.error(f"Error sending email via SES: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email via SES: {str(e)}")
        return False



