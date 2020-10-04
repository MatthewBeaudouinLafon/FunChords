from typing import Tuple
from fun_chord import FunChord
from chord_mod import FunMod, mod_color_map, Sus2, Sus4

class FunPad(object):
    """
    This class represents a pad on push.
    """

    def __init__(self, pad_ij):
        # APIs
        self.pad_ij = pad_ij

    def __repr__(self):
        return str(type(self)) + " at " + str(self.pad_ij)

    def on_press(self, push):
        push.pads.set_pad_color(self.pad_ij, self.press_color())

    def on_release(self, push):
        push.pads.set_pad_color(self.pad_ij, self.release_color())

    def press_color(self):
        raise NotImplementedError

    def default_color(self):
        raise NotImplementedError

    def release_color(self):
        return self.default_color()

    def get_note(self):
        return None

    def get_chord(self):
        return None

    def get_modifier(self):
        return None


class ChordPad(FunPad):
    """
    This pad plays chords.
    """
    def __init__(self, pad_ij, scale, root_degree):
        # APIs
        super(ChordPad, self).__init__(pad_ij)

        # Model
        self.chord = FunChord(scale, root_degree)

    def default_color(self):
        tonic_color = 'turquoise'
        subdominant_color = 'purple'
        dominant_color = 'red'
        chord_root_degree = self.chord.root_degree()
        if self.chord.scale_quality == 'maj':
            if chord_root_degree in (1, 6):
                return tonic_color
            elif chord_root_degree in (2, 3, 4):
                return subdominant_color
            elif chord_root_degree in (5, 7):
                return dominant_color

        elif self.chord.scale_quality == 'min':
            if chord_root_degree in (1, 3, 6):
                return tonic_color
            elif chord_root_degree in (2, 4):
                return subdominant_color
            elif chord_root_degree in (5, 7):
                return dominant_color

        return 'white'  # Something went wrong, default to white
        
    def press_color(self):
        return 'green'

    def get_chord(self):
        return self.chord

class ModPad(FunPad):
    """
    Modifies chords.
    """
    def __init__(self, pad_ij: Tuple[int], mod: FunMod):
        super(ModPad, self).__init__(pad_ij)
        self.mod = mod

    def default_color(self):
        if self.mod in mod_color_map:
            return mod_color_map[self.mod]
        return 'white'

    def press_color(self):
        return 'green'

    def get_modifier(self):
        return self.mod.get_func()
