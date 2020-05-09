import os
import stripe
import logging
import pytz
from datetime import datetime
import simplejson as json
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute, ListAttribute, MapAttribute
)
from ..services.notifications import send_text, send_email
from .model import Model
from ..models.next_ids import NextIds
from ..lib.config import env

logger = logging.getLogger(__name__)


class ItemMap(MapAttribute):
    name = UnicodeAttribute()  # "Leo's Famous Greek Salad"
    # {Size Choice: ["Medium"], Dressing Substitution: ["Substitute Ranch Dressing"]}
    options = MapAttribute(attr_name='options')
    notes = UnicodeAttribute()  # Extra toasted bun
    price = NumberAttribute()  # int
    quantity = NumberAttribute()


class BillingDetailsMap(MapAttribute):
    name = UnicodeAttribute(null=True)
    address = MapAttribute(attr_name='address', null=True)
    email = UnicodeAttribute(null=True)
    phone = UnicodeAttribute(null=True)


class TransactionIdIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'transactionIdIndex'
        read_capacity_units = 2
        write_capacity_units = 1
        projection = AllProjection()

    transactionId = UnicodeAttribute(null=True, hash_key=True)


class StatusIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'statusIndex'
        read_capacity_units = 2
        write_capacity_units = 1
        projection = AllProjection()

    status = UnicodeAttribute(hash_key=True)
    updated_at = UTCDateTimeAttribute(range_key=True)


class Cart(Model):
    class Meta:
        table_name = f'{env}-cart'
        timestamps = True

    STATUS_NEW = 'new_order'
    STATUS_PAID = 'paid'
    STATUS_PAYMENT_FAILED = 'payment_failed'

    id = NumberAttribute(hash_key=True)
    items = ListAttribute(of=ItemMap, default=[])
    totalPrice = UnicodeAttribute(default='0')
    billingDetails = BillingDetailsMap(null=True)
    status = UnicodeAttribute(default=STATUS_NEW)
    statusIndex = StatusIndex()
    transactionId = UnicodeAttribute(null=True)
    transactionIdIndex = TransactionIdIndex()

    def as_json(self):
        return json.loads(json.dumps({
          "id": self.id,
          "items": [item.as_dict() for item in self.items if self.items],
          "totalPrice": self.totalPrice
        }))

    def add_tax(self):
        self.update(actions=[
            Cart.totalPrice.set(
                str(
                    int(float(
                        int(self.totalPrice) * 1.06
                    ))
                )
            )
        ])

    def capture_payment(self, payment_method_id, billing_details):
        self.update(actions=[
            Cart.billingDetails.set(billing_details)
        ])
        self.add_tax()
        logger.info(f'Charging {self.totalPrice} for cart #{self.id}')
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

    def send_order_confirmations(self):
        send_text(self.generate_receipt(), self.billingDetails.phone)
        send_email(
            f"Leo's Coney Island Order Confirmation (Order #{self.id})",
            self.generate_receipt(),
            self.billingDetails.email
        )

    def generate_receipt(self):
        items_list = ''
        for item in self.items:
            items_list += \
                f'{item.quantity} - {item.name} - ' + \
                "${:0.2f}".format(item.price / 100) + \
                "\n"
            for option in self.items.options:
                items_list += f"    {option}: {self.items.options[option]} \n"

            if item.notes:
                items_list += f"    Notes: {item.notes} \n"

        items_list += "\nTotal Price: ${:0.2f}".format(int(self.totalPrice) / 100)
        return f"""-------------------------
Order # {self.id}
-------------------------
{items_list}
-------------------------
We have received your payment. Please pick up your order in 20-30 minutes.

Leo's Coney Island
4895 Carroll Lake Rd, Commerce Charter Twp, MI 48382
(248) 366-8360
"""

    @staticmethod
    def get_paid_today(as_dict=False):
        carts = []
        for cart in Cart.statusIndex.query(hash_key=Cart.STATUS_PAID, range_key_condition=(
            Cart.updated_at >= datetime.today().replace(hour=0, minute=0, second=0)
        )):
            if as_dict:
                carts.append(cart.as_dict())
            else:
                carts.append(cart)

        return carts

    @staticmethod
    def get_by_transactionid(transaction_id):
        for cart in Cart.transactionIdIndex.query(transaction_id):
            return cart

    @staticmethod
    def add_new_cart():
        cart = Cart()
        cart.id = NextIds.get_next_id(Cart.Meta.table_name)
        cart.save()

        return cart

    @staticmethod
    def get_cart(cart_id):
        return Cart.get(int(cart_id))

    def as_dict(self):
        cart = {}
        for key in self.attribute_values:
            if isinstance(self.attribute_values[key], MapAttribute):
                cart[key] = self.attribute_values[key].as_dict()
            elif isinstance(self.attribute_values[key], list):
                cart[key] = [item.as_dict() for item in self.attribute_values[key]]
            elif isinstance(self.attribute_values[key], datetime):
                cart[key] = self.attribute_values[key]. \
                    astimezone(pytz.timezone('US/Eastern')) \
                    .strftime("%m/%d/%Y %H:%M:%S")
            else:
                cart[key] = self.attribute_values[key]

        return cart