import os
import stripe
import logging

import simplejson as json
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute, ListAttribute, MapAttribute
)
from ..models.next_ids import NextIds
from ...lib.config import env

logger = logging.getLogger(__name__)


class ItemMap(MapAttribute):
    name = UnicodeAttribute()  # "Leo's Famous Greek Salad"
    # {Size Choice: ["Medium"], Dressing Substitution: ["Substitute Ranch Dressing"]}
    options = MapAttribute(attr_name='options')
    price = NumberAttribute()  # int
    quantity = NumberAttribute()


class BillingDetailsMap(MapAttribute):
    name = UnicodeAttribute(null=True)
    address = MapAttribute(attr_name='address', null=True)
    email = UnicodeAttribute(null=True)
    phone = UnicodeAttribute(null=True)


class Cart(Model):
    class Meta:
        table_name = f'{env}-cart'

    STATUS_NEW = 'new_order'
    STATUS_PAID = 'paid'
    STATUS_PAYMENT_FAILED = 'payment_failed'

    id = NumberAttribute(hash_key=True)
    items = ListAttribute(of=ItemMap, default=[])
    totalPrice = UnicodeAttribute(default='0')
    billingDetails = BillingDetailsMap(null=True)
    status = UnicodeAttribute(default=STATUS_NEW)
    transactionId = UnicodeAttribute(null=True)

    def as_json(self):
        return json.loads(json.dumps({
          "id": self.id,
          "items": [item.as_dict() for item in self.items if self.items],
          "totalPrice": self.totalPrice
        }))

    def capture_payment(self, payment_method_id, billing_details):
        logger.debug(str(billing_details))
        self.update(actions=[
            Cart.billingDetails.set(billing_details)
        ])

        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(self.totalPrice),
                currency='usd',
                payment_method=payment_method_id,
                confirm=True,
            )
            logger.error(str(intent))
            print(str(intent))
        except stripe.error.CardError:
            self.update(actions=[
                Cart.status.set(Cart.STATUS_PAYMENT_FAILED)
            ])
            return False

        # Handle post-payment fulfillment
        self.update(actions=[
            Cart.status.set(Cart.STATUS_PAID),
            Cart.transactionId.set(intent.id)
        ])

        return self


    @staticmethod
    def add_new_cart():
        cart = Cart()
        cart.id = NextIds.get_next_id(Cart.Meta.table_name)
        cart.save()

        return cart

    @staticmethod
    def get_cart(cart_id):
        return Cart.get(int(cart_id))
