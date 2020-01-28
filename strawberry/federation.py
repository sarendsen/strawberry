from graphql import GraphQLScalarType, GraphQLUnionType

from .field import strawberry_field
from .printer import print_schema
from .schema import Schema as BaseSchema
from .type import _process_type


def type(cls=None, *args, **kwargs):
    def wrap(cls):
        keys = kwargs.pop("keys", [])
        extend = kwargs.pop("extend", False)

        wrapped = _process_type(cls, *args, **kwargs)
        wrapped._federation_keys = keys
        wrapped._federation_extend = extend

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
    def __init__(self, query, *args, **kwargs):
        @type(name="_Service")
        class Service:
            sdl: str

        @type
        class Query(query):
            @field(name="_service")
            def service(self, info) -> Service:
                return Service(sdl=print_schema(info.schema))

        super().__init__(Query, *args, **kwargs)

        for type_ in self.get_additional_types():
            self.type_map[type_.name] = type_

    def get_additional_types(self):
        types = [GraphQLScalarType("_Any")]

        federation_key_types = []

        for graphql_type in self.type_map.values():
            if hasattr(graphql_type, "_strawberry_type"):
                if graphql_type._strawberry_type and getattr(
                    graphql_type._strawberry_type, "_federation_keys", []
                ):
                    federation_key_types.append(graphql_type)

        if federation_key_types:
            types += [GraphQLUnionType("_Entity", federation_key_types)]

        return types
