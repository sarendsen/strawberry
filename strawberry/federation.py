from graphql import (
    GraphQLField,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
)

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._extend_query_type()

        for type_ in self.get_additional_types():
            self.type_map[type_.name] = type_

    def _extend_query_type(self):
        @type(name="_Service")
        class Service:
            sdl: str

        fields = {
            "_service": GraphQLField(
                GraphQLNonNull(Service.field),
                resolve=lambda _, info: Service(sdl=print_schema(info.schema)),
            )
        }

        self.type_map["_Any"] = GraphQLScalarType("_Any")
        self.type_map["_Service"] = Service.field

        fields.update(self.query_type.fields)

        self.query_type = GraphQLObjectType(
            name=self.query_type.name,
            description=self.query_type.description,
            fields=fields,
        )

        self.type_map[self.query_type.name] = self.query_type

    def get_additional_types(self):
        types = []

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
