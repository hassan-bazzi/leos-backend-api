import os

env = os.getenv('DEPLOY_ENV', 'development')

if env == 'prod':
  order_recipients = [
    'me@hassanb.com',
    'leos@hassanb.com',
    'commerceleos@yahoo.com'
  ]
else:
  order_recipients = [
  'me@hassanb.com'
]