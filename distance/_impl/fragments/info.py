
from distance.bytes import Magic
from distance.classes import CollectorGroup


Classes = CollectorGroup()


register = Classes.fragments.add_tag
register('VirusSpiritSpawner', Magic[2], 0x3a)
register('WingCorruptionZone', Magic[2], 0x53)
register('CheckpointLogic', Magic[2], 0x19)
register('SphericalGravity', Magic[2], 0x5f)
register('TrackAttachment', Magic[2], 0x68)
register('TurnLightOnNearCar', Magic[2], 0x70)


# vim:set sw=4 et:
