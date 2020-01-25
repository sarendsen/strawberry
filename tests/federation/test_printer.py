import textwrap
import typing

import strawberry
from strawberry.printer import print_type


def test_print_type_with_key():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str
        name: typing.Optional[str]
        price: typing.Optional[int]
        weight: typing.Optional[int]

    expected_representation = """
        type Product @key(fields: "upc") {
          upc: String!
          name: String
          price: Int
          weight: Int
        }
    """

    assert print_type(Product) == textwrap.dedent(expected_representation).strip()


def test_print_type_with_multiple_keys():
    @strawberry.federation.type(keys=["upc", "sku"])
    class Product:
        upc: str
        sku: str
        name: typing.Optional[str]
        price: typing.Optional[int]
        weight: typing.Optional[int]

    expected_representation = """
        type Product @key(fields: "upc") @key(fields: "sku") {
          upc: String!
          sku: String!
          name: String
          price: Int
          weight: Int
        }
    """

    assert print_type(Product) == textwrap.dedent(expected_representation).strip()
