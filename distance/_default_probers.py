"""A hack for our modules to register their objects on shared probers."""


class DefaultProbers(object):

    """Provides all probers that objects need internally.

    Existing attributes cannot be overwritten. Use a new instance instead.

    """

    # prober_class injected by prober module

    def __setattr__(self, name, value):

        """Disallows overwriting any existing attributes.

        If a module were to replace existing probers, we would lose all
        previous registrations on it by other modules.

        """

        if hasattr(self, name):
            raise AttributeError(
                "DefaultProbers attributes cannot be overwritten."
                " Use copy() to create a modified instance.")

        super().__setattr__(name, value)

    def get_or_create(self, name):
        try:
            return getattr(self, name)
        except AttributeError:
            prober = self.prober_class()
            setattr(self, name, prober)
            return prober

    def copy(self, **probers):
        new = type(self)()
        probers.update((name, prober) for name, prober in self.__dict__.items()
                       if name not in probers)
        for name, prober in probers.items():
            setattr(new, name, prober)
        return new


DefaultProbers = DefaultProbers()


# vim:set sw=4 ts=8 sts=4 et:
