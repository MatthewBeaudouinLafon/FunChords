"""
This file contains all of the chord modifier functions. Each modifier takes a FunChord, and returns
a new FunChord. There's also colors for modifiers/groups of modifiers in here.
"""

from typing import Callable
from fun_chord import FunChord, ScaleNote

mod_color_map = {}  # FunMod -> 'color'

ModFunc = Callable[[FunChord], FunChord]
class FunMod(object):
    def __init__(self, name: str, function: ModFunc):
        self._name = name
        self.function = function

    def __repr__(self) -> str:
        return self._name

    def __eq__(self, other) -> bool:
        return self._name == other._name

    def __hash__(self):
        return self._name.__hash__()

    def get_func(self):
        return self.function

# Sus
sus_color = 'blue'
def sus2(chord: FunChord) -> FunChord:
    if ScaleNote(3) not in chord.triad_notes():
        # Only sus if there's a 3 to substitute
        return chord

    new_additions = chord.copy_additions()
    new_omissions = chord.copy_omissions()

    new_additions.add(2)
    new_omissions.add(3)

    return FunChord(
        chord.get_scale_name(),
        chord.root_degree().get_name(),
        octave=chord._octave,
        additions=new_additions,
        omissions=new_omissions)

def sus4(chord: FunChord) -> FunChord:
    if ScaleNote(3) not in chord.triad_notes():
        # Only sus if there's a 3 to substitute
        return chord

    new_additions = chord.copy_additions()
    new_omissions = chord.copy_omissions()

    new_additions.add(4)
    new_omissions.add(3)

    return FunChord(
        chord.get_scale_name(),
        chord.root_degree().get_name(),
        octave=chord._octave,
        additions=new_additions,
        omissions=new_omissions)

Sus2 = FunMod('Sus2', sus2)
Sus4 = FunMod('Sus4', sus4)

sus_color = 'purple'
mod_color_map[Sus2] = sus_color
mod_color_map[Sus4] = sus_color
