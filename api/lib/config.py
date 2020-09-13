import os

env = os.getenv('DEPLOY_ENV', 'development')

if env == 'prod':
    order_recipients = [
        'leoscommerceorders@gmail.com',
        'me@hassanb.com',
        'commerceleos@yahoo.com'
    ]
    order_sms_recipients = [
        '313-516-8908',
        '313-414-1412',
        '313-330-0900'
    ]
else:
    order_recipients = [
        'me@hassanb.com'
    ]
    order_sms_recipients = [
        '313-516-8908'
    ]
