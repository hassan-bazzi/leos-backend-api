from datetime import datetime
from pynamodb.constants import META_CLASS_NAME
from pynamodb.models import Model as PynamoDbModel, MetaModel as PynamoDbMetaModel
from pynamodb.attributes import UTCDateTimeAttribute


class MetaModel(PynamoDbMetaModel):
    def __init__(self, name, bases, attrs):

        if META_CLASS_NAME in attrs and hasattr(attrs[META_CLASS_NAME], "timestamps"):
            self.has_timestamps = True
            setattr(Model, "created_at", UTCDateTimeAttribute())
            setattr(Model, "updated_at", UTCDateTimeAttribute())
        else:
            self.has_timestamps = False

        super().__init__(name, bases, attrs)


class Model(PynamoDbModel, metaclass=MetaModel):

    def save(self, condition=None, conditional_operator=None, **expected_values):
        if(self.has_timestamps):
            timestamp = datetime.utcnow()
            self.created_at = timestamp
            self.updated_at = timestamp
        super().save(condition, **expected_values)

    def update(self, attributes=None, actions=None, condition=None, conditional_operator=None, **expected_values):
        if(self.has_timestamps):
            actions.append(Model.updated_at.set(datetime.utcnow()))

        super().update(actions, condition, **expected_values)
