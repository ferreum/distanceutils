"""A hack for our modules to register their objects on shared probers."""


from .prober import BytesProber


class DefaultProbers(object):

    """Provides all probers that objects need internally.

    Existing attributes should not be overwritten. Use a subclass instead.

    """

    prober_class = BytesProber

    @classmethod
    def get_or_create(cls, name):
        try:
            return getattr(cls, name)
        except AttributeError:
            prober = cls.prober_class()
            setattr(cls, name, prober)
            return prober


# vim:set sw=4 ts=8 sts=4 et:
