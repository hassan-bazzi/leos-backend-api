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
from ..services.notifications import send_text, send_email, send_html_email
from .model import Model
from ..models.next_ids import NextIds
from ..lib.config import env, order_recipients, order_sms_recipients

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
    tip = UnicodeAttribute(null=True)


class PaymentLogMap(MapAttribute):
    transactionId = UnicodeAttribute(null=True)
    status = UnicodeAttribute(null=True)
    created_at = UTCDateTimeAttribute(null=True)


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
    pickupTime = UnicodeAttribute(default='ASAP (15-20 minutes)')
    paymentLog = ListAttribute(of=PaymentLogMap, default=[])
    status = UnicodeAttribute(default=STATUS_NEW)
    statusIndex = StatusIndex()
    transactionId = UnicodeAttribute(null=True)
    transactionIdIndex = TransactionIdIndex()

    def as_json(self):
        billingDetails = self.billingDetails.as_dict() if self.billingDetails else {}
        # billingDetails['taxHuman']
        # TODO ^
        return json.loads(json.dumps({
            "id": self.id,
            "items": [item.as_dict() for item in self.items if self.items],
            "billingDetails": billingDetails,
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

    def add_tip(self, tip):
        self.update(actions=[
            Cart.totalPrice.set(
                str(
                    int(float(
                        int(self.totalPrice) + int(tip)))
                )
            )
        ])

    def update_items(self, items):
        self.update(actions=[
            Cart.items.set(items),
            Cart.totalPrice.set(_calc_total(items))
        ])

    def _calc_total(self, newItems=[]):
        items_list = newItems
        if not newItems:
            items_list = self.items

        total = 0
        for item in items_list:
            total += int(self.item.totalPrice) * self.item.quantity

        return total

    def capture_payment(self, payment_method_id, billing_details, pickup_time):
        self.update(actions=[
            Cart.billingDetails.set(billing_details),
            Cart.pickupTime.set(pickup_time)
        ])

        if not self.paymentLog:
            self.add_tax()

            if billing_details.get('tip'):
                self.add_tip(billing_details.get('tip'))

        logger.info(f'Charging {self.totalPrice} for cart #{self.id}')
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(self.totalPrice),
                currency='usd',
                payment_method=payment_method_id,
                confirm=True,
            )
            self.update(actions=[
                Cart.paymentLog.set(
                    Cart.paymentLog.append([{
                        'status': 'success',
                        'created_at': datetime.now(),
                        'transactionId': intent.id

                    }])
                )
            ])
        except stripe.error.CardError as e:
            print(str(e))
            self.update(actions=[
                Cart.paymentLog.set(
                    Cart.paymentLog.append([{
                        'status': 'declined',
                        'created_at': datetime.now(),
                        'transactionId': 'n/a'
                    }])
                )
            ])
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
        try:
            send_text(self.generate_receipt(), self.billingDetails.phone)
        except:
            logger.error(
                f'could not send text for {self.billingDetails.phone} {self.id}')

        send_email(
            f"Leo's Coney Island Order Confirmation (Order #{self.id})",
            "Thank you for your order! We're making your food now, please call us if you have any questions. \n"
            + self.generate_receipt(),
            self.billingDetails.email
        )
        for email in order_recipients:
            send_html_email(
                f"Leo's Coney Island Order Confirmation (Order #{self.id})",
                self.generate_html_receipt(),
                email
            )
        for phone in order_sms_recipients:
            send_text(self.generate_receipt(), phone)

    def generate_receipt(self):
        items_list = ''
        for item in self.items:
            items_list += \
                f'{item.quantity} - {item.name} - ' + \
                "${:0.2f}".format(item.price / 100) + \
                "\n"
            if item.options:
                for option in item.options:
                    items_list += f"    {option}: {str(item.options[option]).strip('[]')} \n"

            if item.notes:
                items_list += f"    Notes: {item.notes} \n"

        if self.billingDetails.tip:
            items_list += "\nTip: ${:0.2f}\n".format(
                int(self.billingDetails.tip) / 100)

        items_list += "\nTotal Price: ${:0.2f}".format(
            int(self.totalPrice) / 100)
        return f"""-------------------------
Order # {self.id}
Pickup Time: {self.pickupTime}
-------------------------
{items_list}
-------------------------
We have received your payment. Your order will be ready for pickup at your selected pickup time.

Leo's Coney Island
4895 Carroll Lake Rd, Commerce Charter Twp, MI 48382
(248) 366-8360
"""

    def generate_html_receipt(self):
        items_list = ''
        for item in self.items:
            items_list += \
                f'<h4>{item.quantity} - {item.name} - ' + \
                "${:0.2f}".format(item.price / 100) + \
                "</h4><ul>"
            if item.options:
                for option in item.options:
                    items_list += f"<li style='margin-left: 25px'><h5>{option}: {str(item.options[option]).strip('[]')} </h5></li>"

            if item.notes:
                items_list += f"<li style='margin-left: 25px'><h5>Notes: {item.notes} </h5></li>"

            items_list += '</ul>'
        if self.billingDetails.tip:
            items_list += "<br />Tip: <b>${:0.2f}</b><br />".format(
                int(self.billingDetails.tip) / 100)

        items_list += "<br />Total Price: <b>${:0.2f}</b><br />".format(
            int(self.totalPrice) / 100)
        return f"""<html>-------------------------<br />
<h5>Order # {self.id}</h5>
<h5>{self.billingDetails.name}</h5>
<h5>Pickup Time: {self.pickupTime}</h5>
-------------------------<br />
{items_list}
</html>
"""

    @staticmethod
    def get_paid_today(as_dict=False):
        carts = []
        for cart in Cart.statusIndex.query(hash_key=Cart.STATUS_PAID, range_key_condition=(
            Cart.updated_at >= datetime.today().replace(hour=0, minute=0, second=0)
        ), scan_index_forward=False):
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
                cart[key] = [item.as_dict()
                             for item in self.attribute_values[key]]
            elif isinstance(self.attribute_values[key], datetime):
                cart[key] = self.attribute_values[key]. \
                    astimezone(pytz.timezone('US/Eastern')) \
                    .strftime("%m/%d/%Y %H:%M:%S")
            else:
                cart[key] = self.attribute_values[key]

        return cart
