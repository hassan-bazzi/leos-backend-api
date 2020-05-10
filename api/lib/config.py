import os

env = os.getenv('DEPLOY_ENV', 'development')

if env == 'prod':
  order_recipients = [
    'leoscommerceorders@gmail.com',
    'me@hassanb.com',
    'commerceleos@yahoo.com'
  ]
else:
  order_recipients = [
  'me@hassanb.com'
]