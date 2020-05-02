import os
from flask import Blueprint, request, jsonify, make_response
from flask_cors import CORS
import stripe

from ..api.models.cart import Cart

cart_bp = Blueprint('cart', __name__)
CORS(cart_bp, supports_credentials=True)


@cart_bp.route('/cart', methods=['GET', 'POST'])
def cart_controller():
  if request.method == 'GET':
    if not request.cookies.get('cart_id'):
        cart = Cart.add_new_cart()
    else:
        cart_id = request.cookies.get('cart_id')
        cart = Cart.get_cart(cart_id)
        if not cart:
          cart = Cart.add_new_cart()

    res = jsonify(cart.as_json())
    res.set_cookie('cart_id', f'{cart.id}', max_age=60*60*24*7)

    return res
  elif request.method == 'POST':
    cart_id = request.cookies.get('cart_id')
    cart = Cart.get_cart(int(cart_id))

    if not cart_id:
      return '', 400

    new_cart = request.json
    cart.update(actions=[
      Cart.items.set(new_cart.get('items', [])),
      Cart.totalPrice.set(str(new_cart.get('totalPrice')))
    ])
    return jsonify(cart.as_json())


@cart_bp.route('/cart/pay', methods=['POST'])
def pay():
  cart_id = request.cookies.get('cart_id')
  if not cart_id:
    return 'No cart', 400

  cart = Cart.get_cart(cart_id)
  stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

  intent = stripe.PaymentIntent.create(
    amount=int(cart.totalPrice),
    currency='usd',
    # Verify your integration in this guide by including this parameter
    metadata={'integration_check': 'accept_a_payment'},
  )

  try:
    # Send publishable key and PaymentIntent details to client
    return jsonify({'publishableKey': os.getenv('STRIPE_PUBLISHABLE_KEY'), 'clientSecret': intent.client_secret})
  except Exception as e:
      return jsonify(error=str(e)), 403


def _normalize_price(price):
  if type(price) is int:
    price = str(price)
    leng = len(price)
    price = price[:leng-2] + '.' + price[leng-2:]
  return str(float(price))
