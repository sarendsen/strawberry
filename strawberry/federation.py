from .field import strawberry_field
from .type import _process_type


def type(cls=None, *args, **kwargs):
    def wrap(cls):
        keys = kwargs.pop("keys", [])
        extends = kwargs.pop("extends", False)

        wrapped = _process_type(cls, *args, **kwargs)
        wrapped._federation_keys = keys
        wrapped._federation_extends = extends

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
