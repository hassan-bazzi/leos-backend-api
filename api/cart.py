from flask import Blueprint, request, jsonify, make_response
from flask_cors import CORS
from api.models.cart import Cart
import app

cart = Blueprint('cart', __name__)
CORS(cart, supports_credentials=True)

@cart.route('/cart', methods=['GET', 'POST'])
def cart_controller():
  if request.method == 'GET':
    if not request.cookies.get('cart_id'):
        cart = Cart.add_new_cart()
    else:
        cart_id = request.cookies.get('cart_id')
        cart = Cart.get_cart(cart_id)
        if not cart:
          cart = Cart.add_new_cart()

    res = jsonify(cart.ddb_dump_())
    res.set_cookie('cart_id', f'{cart.id}', max_age=60*60*24*7)

    return res
  elif request.method == 'POST':
    cart_id = request.cookies.get('cart_id')
    cart = Cart.get_cart(int(cart_id))

    if not cart_id:
      return '', 400

    new_cart = request.json
    cart.items = new_cart.get('items', [])
    cart.totalPrice = str(new_cart.get('totalPrice'))
    app.dynamo.sync(cart)
    return jsonify(cart.as_json())

def _normalize_price(price):
  if type(price) is int:
    price = str(price)
    leng = len(price)
    price = price[:leng-2] + '.' + price[leng-2:]
  return str(float(price))