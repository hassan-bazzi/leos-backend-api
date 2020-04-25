from flywheel import Model, Field, STRING, NUMBER
import app


class NextIds(Model):
    __metadata__ = {
      '_name': 'next_ids',
    }

    table_name = Field(hash_key=True, type=STRING)
    next_id = Field(type=NUMBER)

    def get_next_id(table):
        next_id = app.dynamo.query(NextIds).filter(table_name=table)
        next_id = next_id.first()

        if not next_id:
          next_id = NextIds(table_name=table, next_id=1)
          app.dynamo.save(next_id)

        next_id.incr_(next_id=1)
        next_id.sync()

        return next_id.next_id


