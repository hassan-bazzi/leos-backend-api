import logging
import os
from flask import Blueprint, request, jsonify, make_response
from flask_cors import CORS

from ..api.models.cart import Cart

logger = logging.getLogger(__name__)
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
        if not cart or cart.status == Cart.STATUS_PAID:
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
  payment_method_id = request.json.get('payment_method_id')
  logger.debug(str(request.json))
  billing_details = {
    "name": f"{request.json.get('first_name')} {request.json.get('last_name')}",
    "email": request.json.get('email'),
    "phone": request.json.get('phone'),
    "address": {
      "line1": request.json.get("street_address"),
      "city": request.json.get('city'),
      "state": request.json.get('state'),
      "postal_code": request.json.get('zip'),
    }
  }

  if not cart_id:
    return 'No cart', 400

  if not payment_method_id:
    return 'Invalid payment method', 400

  cart = Cart.get_cart(cart_id)

  payment = cart.capture_payment(payment_method_id, billing_details)

  if payment:
    # Handle post-payment fulfillment
    res = jsonify({'success': True})
    # Remove cookie so they can get a new cart
    res.set_cookie('cart_id', '', max_age=60*60*24*7)
    return res
  else:
    # Any other status would be unexpected, so error
    return jsonify({'error': 'Invalid PaymentIntent status'}), 500


@cart_bp.route('/cart/stripe-keys', methods=['GET'])
def stripe_keys():
  return jsonify({'publishableKey': os.getenv('STRIPE_PUBLISHABLE_KEY')})


def _normalize_price(price):
  if type(price) is int:
    price = str(price)
    leng = len(price)
    price = price[:leng-2] + '.' + price[leng-2:]
  return str(float(price))
