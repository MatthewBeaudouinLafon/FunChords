from fun_chord import FunChord

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
        return 'turquoise' if self.chord.is_root() else 'white'
        
    def press_color(self):
        return 'green'

    def get_chord(self):
        return self.chord
