"""Common utility functions."""


def set_default_attrs(attrs):

    def decorate(cls):
        for name, value in attrs.items():
            setattr(cls, name, value)
        return cls

    return decorate


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
