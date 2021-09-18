This is a very simple MVP of a restaurant online ordering portal. Users can place items with customizations in their cart, then proceed to checkout where they can select a tip amount and pickup time, then pay via Stripe. Once paid, an email notification is sent to the restaurant where it is printed and sent to the kitchen. SMS notifications are also sent to the managers.

This backend API has the following functionality:
  - Cart items update based on state of cart from UI
  - Cart ID stored in Cookie so that the order is remembered
  - Clear cart 
  - Pay cart 
  - Email notification sent to user

Technical Features:
  - Email notifications via SES
  - SMS notifications via Twilio
  - Deployed using Elastic Beanstalk
  - All data stored in DynamoDB (See models/cart.py)
