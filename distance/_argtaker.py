"""Handling of *args and **kw."""


DO_THROW = object()


class ArgTaker(object):

    def __init__(self, *args, **kw):
        self._args = args
        self._kwargs = kw
        self._maxarg = 0
        self._fallback_obj = None

    def __call__(self, index, kwname, default=DO_THROW):
        maxarg = self._maxarg
        if index is not None and index > maxarg:
            self._maxarg = index
        args = self._args
        if index is not None and index < len(args):
            return args[index]
        else:
            try:
                return self._kwargs.pop(kwname)
            except KeyError:
                try:
                    return getattr(self._fallback_obj, kwname)
                except AttributeError:
                    if default == DO_THROW:
                        raise TypeError(f"missing argument: {kwname!r}")
                    else:
                        return default

    def fallback_object(self, obj):
        self._fallback_obj = obj

    def verify(self):
        if len(self._args) > self._maxarg + 1:
            raise TypeError(f"too many arguments (expected {self.maxarg})")
        if self._kwargs:
            raise TypeError(f"invalid kwargs: {self.kwargs}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
