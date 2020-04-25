import simplejson as json
from flywheel import Model, Field, STRING, NUMBER
from api.models.next_ids import NextIds
import app

class Cart(Model):
    __metadata__ = {
      '_name': 'cart',
    }

    id = Field(type=NUMBER, hash_key=True)
    items = Field(type=list)
    totalPrice = Field(type=STRING)

    def as_json(self):
      return json.loads(json.dumps(self.ddb_dump_(), use_decimal=True))

    def add_new_cart():
      cart = Cart()
      cart.id = NextIds.get_next_id(cart.__metadata__.get('_name'))
      app.dynamo.sync(cart)

      return cart


    def get_cart(cart_id):
      return app.dynamo.query(Cart).filter(id=cart_id).first()


# app.dynamo.register(Cart)