from typing import Dict, List, Union

import dataclasses
from graphql.language import print_ast
from graphql.language.block_string import print_block_string
from graphql.type import (
    DEFAULT_DEPRECATION_REASON,
    GraphQLArgument,
    GraphQLDirective,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLNamedType,
    GraphQLObjectType,
    GraphQLString,
    is_object_type,
)
from graphql.utilities.ast_from_value import ast_from_value
from graphql.utilities.schema_printer import print_type as original_print_type


def print_description(
    def_: Union[GraphQLArgument, GraphQLDirective, GraphQLEnumValue, GraphQLNamedType],
    indentation="",
    first_in_block=True,
) -> str:
    description = def_.description
    if description is None:
        return ""

    prefer_multiple_lines = len(description) > 70
    block_string = print_block_string(description, "", prefer_multiple_lines)

    prefix = "\n" + indentation if indentation and not first_in_block else indentation

    return prefix + block_string.replace("\n", "\n" + indentation) + "\n"


def print_implemented_interfaces(
    type_: Union[GraphQLObjectType, GraphQLInterfaceType]
) -> str:
    interfaces = type_.interfaces
    return " implements " + " & ".join(i.name for i in interfaces) if interfaces else ""


def print_input_value(name: str, arg: GraphQLArgument) -> str:
    default_ast = ast_from_value(arg.default_value, arg.type)
    arg_decl = f"{name}: {arg.type}"
    if default_ast:
        arg_decl += f" = {print_ast(default_ast)}"
    return arg_decl


def print_args(args: Dict[str, GraphQLArgument], indentation="") -> str:
    if not args:
        return ""

    # If every arg does not have a description, print them on one line.
    if not any(arg.description for arg in args.values()):
        return (
            "("
            + ", ".join(print_input_value(name, arg) for name, arg in args.items())
            + ")"
        )

    return (
        "(\n"
        + "\n".join(
            print_description(arg, f"  {indentation}", not i)
            + f"  {indentation}"
            + print_input_value(name, arg)
            for i, (name, arg) in enumerate(args.items())
        )
        + f"\n{indentation})"
    )


def print_deprecated(field_or_enum_value: Union[GraphQLField, GraphQLEnumValue]) -> str:
    if not field_or_enum_value.is_deprecated:
        return ""
    reason = field_or_enum_value.deprecation_reason
    reason_ast = ast_from_value(reason, GraphQLString)
    if not reason_ast or reason == DEFAULT_DEPRECATION_REASON:
        return " @deprecated"
    return f" @deprecated(reason: {print_ast(reason_ast)})"


def print_block(items: List[str]) -> str:
    return " {\n" + "\n".join(items) + "\n}" if items else ""


def print_federation_field_directive(strawberry_field):
    out = ""

    if "federation" in strawberry_field.metadata:
        federation = strawberry_field.metadata["federation"]

        provides = federation.get("provides", "")
        requires = federation.get("requires", "")
        external = federation.get("external", False)

        if provides:
            out += f' @provides(fields: "{provides}")'

        if requires:
            out += f' @requires(fields: "{requires}")'

        if external:
            out += f" @external"

    return out


def print_fields(strawberry_type) -> str:
    # TODO: support for custom names
    strawberry_fields = {
        field.name: field for field in dataclasses.fields(strawberry_type)
    }

    fields = [
        print_description(field, "  ", not i)
        + f"  {name}"
        + print_args(field.args, "  ")
        + f": {field.type}"
        + print_federation_field_directive(strawberry_fields[name])
        + print_deprecated(field)
        for i, (name, field) in enumerate(strawberry_type.field.fields.items())
    ]
    return print_block(fields)


def print_federation_key_directive(strawberry_type):
    keys = getattr(strawberry_type, "_federation_keys", [])

    parts = []

    for key in keys:
        parts.append(f'@key(fields: "{key}")')

    return " " + " ".join(parts)


def print_object(strawberry_type) -> str:
    type_ = strawberry_type.field

    return (
        print_description(type_)
        + f"type {type_.name}"
        + print_federation_key_directive(strawberry_type)
        + print_implemented_interfaces(type_)
        + print_fields(strawberry_type)
    )


def print_type(strawberry_type) -> str:
    """Returns a string representation of a strawberry type"""

    if is_object_type(strawberry_type.field):
        return print_object(strawberry_type)

    return original_print_type(strawberry_type.field)
