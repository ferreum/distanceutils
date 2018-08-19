

from distance.bytes import Section, Magic
from distance.base import Fragment


class BaseCarScreenTextDecodeTrigger(Fragment):

    class_tag = 'CarScreenTextDecodeTrigger'

    base_container = Section.base(Magic[2], 0x57)

    is_interesting = True

    per_char_speed = None
    clear_on_finish = None
    clear_on_trigger_exit = None
    destroy_on_trigger_exit = None
    static_time_text = None
    delay = None
    announcer_action = None

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if self.text is not None:
            p(f"Text: {self.text!r}")
        if self.per_char_speed is not None:
            p(f"Per char speed: {self.per_char_speed}")
        if self.clear_on_finish is not None:
            p(f"Clear on finish: {self.clear_on_finish and 'yes' or 'no'}")
        if self.clear_on_trigger_exit is not None:
            p(f"Clear on trigger exit: {self.clear_on_trigger_exit and 'yes' or 'no'}")
        if self.destroy_on_trigger_exit is not None:
            p(f"Destroy on trigger exit: {self.destroy_on_trigger_exit and 'yes' or 'no'}")
        if self.time_text:
            p(f"Time text: {self.time_text!r}")
        if self.static_time_text is not None:
            p(f"Static time text: {self.static_time_text and 'yes' or 'no'}")
        if self.delay is not None:
            p(f"Delay: {self.delay}")
        if self.announcer_action is not None:
            p(f"Announcer action: {self.announcer_action}")


class BaseInfoDisplayLogic(Fragment):

    class_tag = 'InfoDisplayLogic'

    base_container = Section.base(Magic[2], 0x4a)

    is_interesting = True

    fadeout_time = None
    texts = ()
    per_char_speed = None
    destroy_on_trigger_exit = None
    random_char_count = None

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        for i, text in enumerate(self.texts):
            if text:
                p(f"Text {i}: {text!r}")
        if self.per_char_speed is not None:
            p(f"Per char speed: {self.per_char_speed}")
        if self.destroy_on_trigger_exit is not None:
            p(f"Destroy on trigger exit: {self.destroy_on_trigger_exit and 'yes' or 'no'}")
        if self.fadeout_time is not None:
            p(f"Fade out time: {self.fadeout_time}")
        if self.random_char_count is not None:
            p(f"Random char count: {self.random_char_count}")


class BaseTeleporterEntrance(Fragment):

    class_tag = 'TeleporterEntrance'

    base_container = Section.base(Magic[2], 0x3e)

    is_interesting = True

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if self.destination is not None:
            p(f"Teleports to: {self.destination}")


class BaseTeleporterExit(Fragment):

    class_tag = 'TeleporterExit'

    base_container = Section.base(Magic[2], 0x3f)

    is_interesting = True

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if self.link_id is not None:
            p(f"Link ID: {self.link_id}")


class BaseInterpolateToPositiononTrigger(Fragment):

    class_tag = 'InterpolateToPositionOnTrigger'

    base_container = Section.base(Magic[2], 0x43)


# vim:set sw=4 ts=8 sts=4 et:
