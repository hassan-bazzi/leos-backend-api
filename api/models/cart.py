import simplejson as json
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute, ListAttribute, MapAttribute
)
from api.models.next_ids import NextIds


class ItemMap(MapAttribute):
    pass


class Cart(Model):
    class Meta:
        table_name = 'cart'

    id = NumberAttribute(hash_key=True)
    items = ListAttribute(of=ItemMap)
    totalPrice = UnicodeAttribute()

    def as_json(self):
        return json.loads(json.dumps({
          "id": self.id,
          "items": [item.as_dict() for item in self.items if self.items],
          "totalPrice": self.totalPrice
        }))

    @staticmethod
    def add_new_cart():
        cart = Cart()
        cart.id = NextIds.get_next_id(Cart.Meta.table_name)
        cart.save()

        return cart

    @staticmethod
    def get_cart(cart_id):
        return Cart.get(int(cart_id))
