from typing import Dict, List, Union

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


def print_fields(type_: Union[GraphQLObjectType, GraphQLInterfaceType]) -> str:
    fields = [
        print_description(field, "  ", not i)
        + f"  {name}"
        + print_args(field.args, "  ")
        + f": {field.type}"
        + print_deprecated(field)
        for i, (name, field) in enumerate(type_.fields.items())
    ]
    return print_block(fields)


def print_federation_key_directive(keys=None):
    if not keys:
        return ""

    parts = []

    for key in keys:
        parts.append(f'@key(fields: "{key}")')

    return " " + " ".join(parts)


def print_object(type_: GraphQLObjectType, keys=None) -> str:
    return (
        print_description(type_)
        + f"type {type_.name}"
        + print_federation_key_directive(keys)
        + print_implemented_interfaces(type_)
        + print_fields(type_)
    )


def print_type(type_) -> str:
    """Returns a string representation of a strawberry type"""

    graphql_type = type_.field

    if is_object_type(graphql_type):
        return print_object(graphql_type, keys=getattr(type_, "_federation_keys"))

    return original_print_type(type_.field)
