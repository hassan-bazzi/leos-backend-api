from api.models.cart import Cart
import json

print(json.dumps(Cart.get_paid_today(as_dict=True)))
# print(Cart.get(15).send_order_confirmations())