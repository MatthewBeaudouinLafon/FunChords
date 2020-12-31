"""
This file contains all of the chord modifier functions. Each modifier takes a FunChord, and returns
a new FunChord. There's also colors for modifiers/groups of modifiers in here.
"""

from typing import Callable, List
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
        additions=new_additions,
        omissions=new_omissions)

Sus2 = FunMod('Sus2', sus2)
Sus4 = FunMod('Sus4', sus4)

sus_color = 'purple'
mod_color_map[Sus2] = sus_color
mod_color_map[Sus4] = sus_color


# Alternate Triad
def are_tones_major_triad(tones: List[int]) -> bool:
    root = tones[0]
    third_interval = tones[1] - root
    return third_interval == 4

def are_tones_minor_triad(tones: List[int]) -> bool:
    root = tones[0]
    third_interval = tones[1] - root
    return third_interval == 3

def diminished(chord: FunChord) -> FunChord:
    raise NotImplementedError

def augmented(chord: FunChord) -> FunChord:
    raise NotImplementedError

# TODO: implement augmented <-> diminished
def parallel(chord: FunChord) -> FunChord:
    new_additions = chord.copy_additions()
    new_omissions = chord.copy_omissions()

    tones = chord.tones()
    if are_tones_major_triad(tones):
        new_additions.add('b3')
        new_omissions.add(3)
    elif are_tones_minor_triad(tones):
        new_additions.add('#3')
        new_omissions.add(3)

    return FunChord(
        chord.get_scale_name(),
        chord.root_degree().get_name(),
        additions=new_additions,
        omissions=new_omissions)

Parallel = FunMod('Parallel', parallel)
mod_color_map[Parallel] = 'orange'

# Extensions
def extend(chord: FunChord, extended_note: List[int], omissions=[]) -> FunChord:
    new_additions = chord.copy_additions()
    new_omissions = chord.copy_omissions()

    for note in extended_note:
        new_additions.add(note)

    for note in omissions:
        new_omissions.add(note)

    return FunChord(
        chord.get_scale_name(),
        chord.root_degree().get_name(),
        additions=new_additions,
        omissions=new_omissions)

def add7(chord: FunChord) -> FunChord:
    return extend(chord, [7])

def add6(chord: FunChord) -> FunChord:
    return extend(chord, [6], omissions=[7])

def add9(chord: FunChord) -> FunChord:
    return extend(chord, [7, 9])

def add11(chord: FunChord) -> FunChord:
    return extend(chord, [7, 9, 11])

Add6 = FunMod('Add6', add6)
Add7 = FunMod('Add7', add7)
Add9 = FunMod('Add9', add9)
Add11 = FunMod('Add11', add11)

extension_color = 'blue'
for extension_mod in [Add6, Add7, Add9, Add11]:
    mod_color_map[extension_mod] = extension_color

# Borrowed scale
def seconday_fifth(chord: FunChord) -> FunChord:
    new_additions = chord.copy_additions()
    new_omissions = chord.copy_omissions()

    new_scale = 0

    return FunChord(
        chord.get_scale_name(),
        chord.root_degree().get_name(),
        additions=new_additions,
        omissions=new_omissions)
