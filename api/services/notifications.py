import boto3
from twilio.rest import Client
import logging
import os

logger = logging.getLogger(__name__)


def send_email(subject, message, recipient):
    client = boto3.client('ses', region_name='us-east-1')

    return client.send_email(
        Source="Leo's Commerce NOREPLY <mail@leoscommerce.com>",
        Destination={
            'ToAddresses': [
                recipient
            ]
        },
        Message={
            'Subject': {
                'Data': subject
            },
            'Body': {
                'Text': {
                    'Data': message
                },
            }
        }
    )


def send_text(message, recipient):
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')

    phone = '+1' + recipient.replace('-', '').replace('_', '').strip()
    logger.info('sending twilio SMS to: ' + phone)

    print(phone)

    client = Client(account_sid, auth_token)

    message = client.messages \
                    .create(
                        body=message,
                        from_='+12485745237',
                        to=phone
                    )

    logger.info('twilio response: ' + str(message))

    return message.sid
