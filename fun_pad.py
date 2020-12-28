from typing import Tuple, List, Type
import copy

import note_util
from fun_chord import FunChord
from chord_mod import FunMod, mod_color_map, Sus2, Sus4

class FunPad(object):
    """
    This class represents a pad on push.
    """

    def __init__(self, pad_ij):
        # APIs
        self.pad_ij = pad_ij
        self.is_pressed = False
        self._registry_id = self.set_registry_id()

    def __repr__(self):
        return str(type(self)) + " at " + str(self.pad_ij)

    def highlight(self, push):
        # NOTE: This function should only change the pad's color
        push.pads.set_pad_color(self.pad_ij, self.press_color())

    def release_highlight(self, push):
        # NOTE: This function should only change the pad's color
        push.pads.set_pad_color(self.pad_ij, self.release_color())

    def registry_highlight(self, push):
        """ Used by the Registry to safely highlight the pad. """
        self.highlight(push)
    
    def registry_release_highlight(self, push):
        """ Used by the Registry to safely release highlight on the pad. """
        # Don't un-highlight a pad if it is pressed but something tries to un-highlight through
        # the registry.
        if not self.is_pressed:
            self.release_highlight(push)

    def on_press(self, push):
        """
        What to do when the pad is pressed. If a pad overwrites this function to do extra stuff,
        it should call the super anyway.
        """
        self.is_pressed = True
        self.highlight(push)

    def on_release(self, push):
        """
        What to do when the pad is released. If a pad overwrites this function to do extra stuff,
        it should call the super anyway.
        """
        self.is_pressed = False
        self.release_highlight(push)

    def get_registry_id(self):
        return self._registry_id

    def set_registry_id(self, **kwargs):
        """
        Compute ID to use in the pad registry such that other functions can find this pad.
        Should be unique per pad in the grid - and probably a simple name.
        """
        raise NotImplementedError

    def press_color(self):
        # Default to green
        return 'green'

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

    def get_highlight_pad_requests(self) -> str:
        """
        Get list of Registry IDs that should be lit up on button press and .
        """
        return []


class PianoNotePad(FunPad):
    def __init__(self, pad_ij, tone):
        self.tone = tone

        # APIs (last such that the set_registry has everything it needs)
        super(PianoNotePad, self).__init__(pad_ij)

    def set_registry_id(self):
        return 'Note: ' + note_util.number_to_name[self.tone]

    def default_color(self):
        if self.tone in note_util.RELATIVE_KEY_DICT['maj']:
            return 'white'
        else:
            return 'light_gray'

    # TODO: Determine mechanism for multiple scale notes to highlight a chord.

class ChordPad(FunPad):
    """
    This pad plays chords.
    """
    def __init__(self, pad_ij, scale, root_degree):
        # Model
        self.chord = FunChord(scale, root_degree)

        # APIs (last such that the set_registry has everything it needs)
        super(ChordPad, self).__init__(pad_ij)

    def set_registry_id(self):
        return 'Chord: ' + str(self.chord)

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

    def get_chord(self):
        return self.chord


class ModPad(FunPad):
    """
    Modifies chords.
    """
    def __init__(self, pad_ij: Tuple[int], mod: FunMod):
        self.mod = mod
        super(ModPad, self).__init__(pad_ij)

    def set_registry_id(self):
        return 'Mod: ' + str(self.mod)

    def default_color(self):
        if self.mod in mod_color_map:
            return mod_color_map[self.mod]
        return 'white'

    def get_modifier(self):
        return self.mod.get_func()

class BankPad(FunPad):
    """
    Stores a chord and modifiers.
    """
    def __init__(self, pad_ij: Tuple[int]):
        self.recording_tap = False

        self.chord = None
        self.modifiers = None

        super(BankPad, self).__init__(pad_ij)

    def set_registry_id(self):
        # TODO: maybe have the registry update based on what's stored in the chord
        # such that playing the chord+mods stored lights this up.
        return None

    def on_press(self, push, chord, modifiers):
        super(BankPad, self).on_press(push)

        self.recording_tap = False
        if chord is not None:
            self.recording_tap = True
            self.chord = chord
            self.modifiers = copy.deepcopy(modifiers)

    def default_color(self):
        if self.chord is None:
            return 'blue'
        else:
            return 'yellow'

    def get_chord(self) -> FunChord:
        # Don't return chord if we just recorded the pad
        if self.recording_tap:
            return None

        return self.chord

    def get_modifier(self) -> List[FunMod]:
        # Don't return chord if we just recorded the pad
        if self.recording_tap:
            return None

        return self.modifiers


##################################################
#                    Registry                    #
##################################################

class PadRegistry(object):
    """
    Registry of pads to keep track of which pads are active.

    It's effectively a dictionary mapping "Registry IDs" to the Pad objects. This allows pads
    to act on other pads via a simple ID. For example, a chord can highlight note pads on the piano.
    Registry IDs are strings unique to each pad and should be easy to compute based on the purpose
    of the pad. For example, the ID for C on the pad piano is 'Note: C'.
    """
    def __init__(self, pad_grid):
        self._registry = dict()
        for row in pad_grid:
            for pad in row:
                if pad is None or pad.get_registry_id() is None:
                    continue
                
                rid = pad.get_registry_id()
                assert rid not in self._registry, "Pad RID ({}) already in registry.".format(rid)

                self._registry[rid] = pad

    def __getitem__(self, key: str) -> FunPad:
        try:
            return self._registry[key]
        except KeyError:
            print("Warning: key ({}) not found in registry.".format(key))

    def highlight_pad(self, pad_rid: str):
        self._registry[pad_rid].highlight()

    def release_pad_highlight(self, pad_rid: str):
        self._registry[pad_rid].release_highlight()
