
from distance.bytes import Magic
from distance.prober import CollectorGroup


Probers = CollectorGroup()


register = Probers.fragments.add_tag
register('VirusSpiritSpawner', Magic[2], 0x3a)
register('EventTrigger', Magic[2], 0x89)
register('WingCorruptionZone', Magic[2], 0x53)
register('CheckpointLogic', Magic[2], 0x19)
register('SphericalGravity', Magic[2], 0x5f)


# vim:set sw=4 et:
