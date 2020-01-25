from .type import _process_type


def type(cls=None, *args, **kwargs):
    def wrap(cls):
        keys = kwargs.pop("keys", [])

        wrapped = _process_type(cls, *args, **kwargs)
        wrapped._federation_keys = keys

        return wrapped

    if cls is None:
        return wrap

    return wrap(cls)
