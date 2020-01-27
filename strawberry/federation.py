from graphql import GraphQLUnionType

from .field import strawberry_field
from .schema import Schema as BaseSchema
from .type import _process_type


TYPES_WITH_KEY = []


def type(cls=None, *args, **kwargs):
    def wrap(cls):
        keys = kwargs.pop("keys", [])
        extend = kwargs.pop("extend", False)

        wrapped = _process_type(cls, *args, **kwargs)
        wrapped._federation_keys = keys
        wrapped._federation_extend = extend

        if keys:
            TYPES_WITH_KEY.append(wrapped)

        return wrapped

    if cls is None:
        return wrap

    return wrap(cls)


def strawberry_federation_field(*args, **kwargs):
    provides = kwargs.pop("provides", "")
    requires = kwargs.pop("requires", "")
    external = kwargs.pop("external", False)

    metadata = kwargs.get("metadata") or {}
    metadata["federation"] = {
        "provides": provides,
        "external": external,
        "requires": requires,
    }
    kwargs["metadata"] = metadata

    field = strawberry_field(*args, **kwargs)

    return field


def field(wrap=None, *args, **kwargs):
    field = strawberry_federation_field(*args, **kwargs)

    if wrap is None:
        return field

    return field(wrap)


class Schema(BaseSchema):
    def get_additional_types(self):
        if TYPES_WITH_KEY:
            return [GraphQLUnionType("_Entity", [t.field for t in TYPES_WITH_KEY])]

        return []
