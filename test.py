from api.models.cart import Cart
import json

print(json.dumps(Cart.get_paid_today(as_dict=True)))
# print(Cart.get(15).send_order_confirmations())

for item in c.items:
  for option in item.options.as_dict():
    print(o for o in item.options[option])