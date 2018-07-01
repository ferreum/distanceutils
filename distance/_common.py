"""Common utility functions."""


from collections import OrderedDict


def set_default_attrs(attrs):

    def decorate(cls):
        for name, value in attrs.items():
            setattr(cls, name, value)
        return cls

    return decorate


class ModesMapperProperty(object):

    def __init__(self, attr):
        self.attr = attr

    @staticmethod
    def to_map(value):
        d = OrderedDict()
        for elem in value:
            d[elem.mode] = elem.enabled
        return d

    def __get__(self, inst, objtype=None):
        return self.to_map(getattr(inst, self.attr))

    def __set__(self, inst, value):
        from construct import Container, ListContainer
        l = [Container(mode=k, enabled=v) for k, v in value.items()]
        setattr(inst, self.attr, ListContainer(l))


class MedalTimesMapperProperty(object):

    def __init__(self, attr):
        self.attr = attr

    def __get__(self, inst, objtype=None):
        return [m.time for m in getattr(inst, self.attr)]

    def __set__(self, inst, value):
        from construct import Container, ListContainer
        if len(value) != 4:
            raise ValueError("Need four medal times")
        l = [Container(time = t, score = m.score)
             for t, m in zip(value, inst.medal_list)]
        setattr(inst, self.attr, ListContainer(l))


class MedalScoresMapperProperty(object):

    def __init__(self, attr):
        self.attr = attr

    def __get__(self, inst, objtype=None):
        return [m.score for m in getattr(inst, self.attr)]

    def __set__(self, inst, value):
        from construct import Container, ListContainer
        if len(value) != 4:
            raise ValueError("Need four medal scores")
        l = [Container(time = m.time, score = s)
             for m, s in zip(self.medal_list, value)]
        setattr(inst, self.attr, ListContainer(l))


# vim:set sw=4 ts=8 sts=4 et:
