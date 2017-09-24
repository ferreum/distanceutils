"""Handling of *args and **kw."""


class ArgTaker(object):

    def __init__(self, *args, **kw):
        self.args = args
        self.kwargs = kw
        self.maxarg = 0

    def __call__(self, index, kwname):
        maxarg = self.maxarg
        if index > maxarg:
            self.maxarg = index
        args = self.args
        if index < len(args):
            return args[index]
        else:
            try:
                return self.kwargs.pop(kwname)
            except KeyError:
                raise ValueError(f"missing argument: {kwname!r}")

    def verify(self):
        if len(self.args) > self.maxarg + 1:
            raise ValueError(f"too many arguments (expected {self.maxarg})")
        if self.kwargs:
            raise ValueError(f"invalid kwargs: {self.kwargs}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
