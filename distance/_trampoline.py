"""A yield-based trampoline."""


class TailCall(BaseException):
    "Raised to signal a tail call to trampoline()."

    def __init__(self, gen):
        self.gen = gen


def trampoline(init):
    stack = [init]
    retval = None
    exception = None
    while stack:
        try:
            if exception is not None:
                ex, exception = exception, None
                res = stack[-1].throw(ex)
            elif retval is None:
                # We need to differentiate between None and Non-None,
                # because generators can only be started with next().
                res = next(stack[-1])
            else:
                value, retval = retval, None
                res = stack[-1].send(value)
            stack.append(res)
        except TailCall as e:
            stack[-1] = e.gen
        except StopIteration as e:
            stack.pop()
            retval = e.value
        except BaseException as e:
            stack.pop()
            exception = e
    if exception is not None:
        raise exception
    return retval


# vim:set sw=4 et:
