import os
import boto3
from botocore.exceptions import ClientError
import logging
import sys
from dotenv import load_dotenv

# Set up logging
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

def test_ses_connection():
    """Test AWS SES connection and send a test email."""
    # Get configuration from environment variables
    aws_region = os.environ.get('AWS_REGION')
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    sender_email = os.environ.get('MAIL_DEFAULT_SENDER')
    recipient_email = input("Enter recipient email address: ")
    
    # Log configuration
    logger.info(f"AWS SES Configuration:")
    logger.info(f"AWS_REGION: {aws_region}")
    logger.info(f"AWS_ACCESS_KEY_ID: {aws_access_key_id[:4] if aws_access_key_id else 'Not set'}...")
    logger.info(f"MAIL_DEFAULT_SENDER: {sender_email}")
    
    # Check if all required configuration is present
    if not aws_region:
        logger.error("AWS_REGION is not set")
        return False
    if not aws_access_key_id:
        logger.error("AWS_ACCESS_KEY_ID is not set")
        return False
    if not aws_secret_access_key:
        logger.error("AWS_SECRET_ACCESS_KEY is not set")
        return False
    if not sender_email:
        logger.error("MAIL_DEFAULT_SENDER is not set")
        return False
    
    try:
        # Create a new SES resource
        logger.info(f"Creating SES client with region={aws_region}")
        client = boto3.client(
            'ses',
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        # Try to send the email
        logger.info(f"Sending test email via SES to {recipient_email}")
        response = client.send_email(
            Destination={
                'ToAddresses': [recipient_email],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': 'UTF-8',
                        'Data': '<h1>Test Email</h1><p>This is a test email sent from AWS SES.</p>',
                    },
                    'Text': {
                        'Charset': 'UTF-8',
                        'Data': 'Test Email\n\nThis is a test email sent from AWS SES.',
                    },
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': 'AWS SES Test Email',
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

if __name__ == "__main__":
    success = test_ses_connection()
    if success:
        print("\nSUCCESS: Test email sent successfully via AWS SES!")
    else:
        print("\nFAILURE: Failed to send test email via AWS SES. Check the logs above for details.") 