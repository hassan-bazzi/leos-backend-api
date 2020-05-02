import simplejson as json
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute, ListAttribute, MapAttribute
)
from ..models.next_ids import NextIds


class ItemMap(MapAttribute):
    name = UnicodeAttribute() # "Leo's Famous Greek Salad"
    options = MapAttribute(attr_name='options') # {Size Choice: ["Medium"], Dressing Substitution: ["Substitute Ranch Dressing"]}
    price = NumberAttribute() # int
    quantity = NumberAttribute()

class Cart(Model):
    class Meta:
        table_name = 'cart'

    id = NumberAttribute(hash_key=True)
    items = ListAttribute(of=ItemMap, default=[])
    totalPrice = UnicodeAttribute(null=True)

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
