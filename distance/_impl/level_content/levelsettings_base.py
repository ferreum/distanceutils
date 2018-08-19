

from distance.base import Fragment
from distance.constants import Difficulty, Mode, AbilityOption
from distance.printing import format_duration


class BaseLevelSettings(Fragment):

    _fields_ = dict(
        version = None,
        name = None,
        description = None,
        author_name = None,
        skybox_name = None,
        modes = (),
        medal_times = (),
        medal_scores = (),
        background_layer = None,
        abilities = (),
        difficulty = None,
    )

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if self.name is not None:
            p(f"Level name: {self.name!r}")
        if self.skybox_name is not None:
            p(f"Skybox name: {self.skybox_name!r}")
        if self.background_layer is not None:
            p(f"Background layer: {self.background_layer!r}")
        if self.medal_times:
            medal_str = ', '.join(format_duration(t) for t in self.medal_times)
            p(f"Medal times: {medal_str}")
        if self.medal_scores:
            medal_str = ', '.join(str(s) for s in self.medal_scores)
            p(f"Medal scores: {medal_str}")
        if self.modes:
            modes_str = ', '.join(Mode.to_name(mode)
                                  for mode, value in sorted(self.modes.items())
                                  if value)
            p(f"Level modes: {modes_str or 'None'}")
        if self.abilities:
            ab_str = ', '.join(AbilityOption.to_name_for_value(toggle, value)
                               for toggle, value in enumerate(self.abilities)
                               if value != 0)
            if not ab_str:
                ab_str = "All"
            p(f"Abilities: {ab_str}")
        if self.difficulty is not None:
            p(f"Difficulty: {Difficulty.to_name(self.difficulty)}")
        if self.author_name:
            p(f"Author: {self.author_name!r}")
        if self.description and 'description' in p.flags:
            p(f"Description: {self.description}")


# vim:set sw=4 et:
