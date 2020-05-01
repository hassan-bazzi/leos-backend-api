from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute, ListAttribute, MapAttribute
)


class NextIds(Model):
    class Meta:
        table_name = 'next_ids'

    table_name = UnicodeAttribute(hash_key=True)
    next_id = NumberAttribute

    def get_next_id(table):
        next_id = NextIds.get(table)

        if not next_id:
            next_id = NextIds(table_name=table, next_id=1)
            next_id.save()

        next_id.update(actions=[
            NextIds.next_id + 1
        ])

        return next_id.next_id

