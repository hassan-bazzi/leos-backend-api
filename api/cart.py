import logging
import os
from flask import Blueprint, request, jsonify, make_response
from flask_cors import CORS

from api.models.cart import Cart

logger = logging.getLogger(__name__)
cart_bp = Blueprint('cart', __name__)
CORS(cart_bp, supports_credentials=True)


@cart_bp.route('/cart', methods=['GET', 'POST'])
def cart_controller():
    if request.method == 'GET':
        logger.info('new cart request')
        if not request.cookies.get('cart_id'):
            return jsonify({})
        else:
            cart_id = request.cookies.get('cart_id')
            cart = Cart.get_cart(cart_id)
            if not cart or cart.status == Cart.STATUS_PAID:
                cart = Cart.add_new_cart()

        return jsonify(cart.as_json())
    elif request.method == 'POST':
        cart_id = request.cookies.get('cart_id')

        if not cart_id:
            cart = Cart.add_new_cart()
        else:
            cart = Cart.get_cart(int(cart_id))

        new_cart = request.json
        cart.update(actions=[
            Cart.items.set(new_cart.get('items', [])),
            Cart.totalPrice.set(str(new_cart.get('totalPrice')))
        ])

        res = jsonify(cart.as_json())
        res.set_cookie('cart_id', f'{cart.id}', max_age=60*60*24*7)

        return res


@cart_bp.route('/cart/list', methods=['GET'])
def cart_list_controller():
    return jsonify(Cart.get_paid_today(True))


@cart_bp.route('/cart/pay', methods=['POST'])
def pay():
    cart_id = request.cookies.get('cart_id')
    payment_method_id = request.json.get('payment_method_id')
    pickup_time = request.json.get('pickup_time', 'ASAP (15-20 minutes)')
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
    if request.json.get('tip'):
        try:
            tip = int(float(request.json.get('tip')) * 100)
            billing_details['tip'] = str(tip)
        except:
            logger.error(f'error converting tip: {request.json.get("tip")}')
            pass

    if not cart_id:
        return 'No cart', 400

    if not payment_method_id:
        return 'Invalid payment method', 400

    cart = Cart.get_cart(cart_id)

    payment = cart.capture_payment(
        payment_method_id, billing_details, pickup_time)

    if payment:
        # Handle post-payment fulfillment
        res = jsonify({'success': True})
        # Remove cookie so they can get a new cart
        res.set_cookie('cart_id', '', max_age=60*60*24*7)
        return res
    else:
        # Any other status would be unexpected, so error
        return jsonify({'error': 'Invalid PaymentIntent status'}), 500


@cart_bp.route('/cart/clear', methods=['GET'])
def clear_cart():
    cart = Cart.add_new_cart()

    res = jsonify(cart.as_json())
    res.set_cookie('cart_id', f'{cart.id}', max_age=60*60*24*7)

    return res


@cart_bp.route('/cart/stripe-keys', methods=['GET'])
def stripe_keys():
    return jsonify({'publishableKey': os.getenv('STRIPE_PUBLISHABLE_KEY')})


@cart_bp.route('/cart/stripe-hook', methods=['POST'])
def stripe_hook():
    data = request.json.get('data')
    logger.info('stripe hook initiated')
    logger.info(f'stripe data: {str(data)}')

    transaction_id = data.get('object', {}).get('id')
    # transaction_id = 'pi_1Gevu4IYFNyZvHf3wEXlePaj'

    if not transaction_id:
        return

    cart = Cart.get_by_transactionid(transaction_id)
    cart.send_order_confirmations()

    return ''
