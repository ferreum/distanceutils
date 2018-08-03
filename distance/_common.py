"""Common utility functions."""


from collections import OrderedDict


def ModesMapperProperty(attr):
    def fget(obj):
        return modes_to_map(getattr(obj, attr))
    def fset(obj, value):
        from construct import Container, ListContainer
        l = [Container(mode=k, enabled=v) for k, v in value.items()]
        setattr(obj, attr, ListContainer(l))
    return property(fget=fget, fset=fset)


def modes_to_map(value):
    d = OrderedDict()
    for elem in value:
        d[elem.mode] = elem.enabled
    return d


def MedalTimesMapperProperty(attr):
    def fget(obj):
        return [m.time for m in getattr(obj, attr)]
    def fset(obj, value):
        from construct import Container, ListContainer
        if len(value) != 4:
            raise ValueError("Need four medal times")
        l = [Container(time = t, score = m.score)
                for t, m in zip(value, getattr(obj, attr))]
        setattr(obj, attr, ListContainer(l))
    return property(fget, fset)


def MedalScoresMapperProperty(attr):
    def fget(obj):
        return [m.score for m in getattr(obj, attr)]
    def fset(obj, value):
        from construct import Container, ListContainer
        if len(value) != 4:
            raise ValueError("Need four medal scores")
        l = [Container(time = m.time, score = s)
                for m, s in zip(getattr(obj, attr), value)]
        setattr(obj, attr, ListContainer(l))
    return property(fget, fset)


class classproperty(object):

    def __init__(self, func):
        self.func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, obj, objtype=None):
        if obj is not None:
            objtype = type(obj)
        return self.func(objtype)

    def __set__(self, obj, value):
        raise AttributeError("can't set attribute")


# vim:set sw=4 ts=8 sts=4 et:
