from typing import Tuple, List, Type
import copy
import threading

import note_util
from fun_chord import FunChord
from chord_mod import FunMod, mod_color_map, Sus2, Sus4
from push2_python import constants

class FunPad(object):
    """
    This class represents a pad on push.
    """

    def __init__(self, pad_ij):
        # APIs
        self.pad_ij = pad_ij
        self.is_pressed = False
        self.is_highlighted = False
        self._registry_id = self.set_registry_id()

    def __repr__(self):
        return str(type(self)) + " at " + str(self.pad_ij)
    
    def _change_color(self, push, color):
        push.pads.set_pad_color(self.pad_ij, color)

    def _update_color(self, push):
        if self.is_pressed:
            self._change_color(push, self.press_color())
        elif self.is_highlighted:
            self._change_color(push, self.highlight_color())
        else:
            self._change_color(push, self.default_color())

    def on_press(self, push):
        """
        What to do when the pad is pressed. If a pad overwrites this function to do extra stuff,
        it should call the super anyway.
        """
        self.is_pressed = True
        self._update_color(push)
    
    def on_release(self, push):
        """
        What to do when the pad is released. If a pad overwrites this function to do extra stuff,
        it should call the super anyway.
        """
        self.is_pressed = False
        self._update_color(push)

    def highlight(self, push):
        """
        Allows pad to be lit up differently through the Registry.
        Eg. when Cmaj is played, notes C, E, and G are highlighted.
        """
        self.is_highlighted = True
        self._update_color(push)

    def release_highlight(self, push):
        self.is_highlighted = False
        self._update_color(push)

    def get_registry_id(self):
        return self._registry_id

    def set_registry_id(self, **kwargs):
        """
        Compute ID to use in the pad registry such that other functions can find this pad.
        Should be unique per pad in the grid - and probably a simple name.
        """
        raise NotImplementedError

    def press_color(self):
        return 'green'

    def highlight_color(self):
        return 'turquoise'

    def default_color(self):
        """
        Display color when not pressed. This should be overwritten.
        """
        raise NotImplementedError

    def get_note(self):
        return None

    def get_chord(self):
        return None

    def get_modifier(self):
        return None

    def delete(self) -> None:
        """
        Up to the pad to determine what this means.
        Eg. Bank pads will clear themselves.
        """
        pass

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
        tonic_color = 'purple'
        subdominant_color = 'pink'
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

        # Harmony
        self.chord_pad = None
        self.modifier_pads = []

        super(BankPad, self).__init__(pad_ij)
    
    def is_empty(self) -> bool:
        return self.chord_pad is None and len(self.modifier_pads) == 0

    def set_registry_id(self):
        # TODO: maybe have the registry update based on what's stored in the chord
        # such that playing the chord+mods stored lights this up.
        return None

    def on_press(self, push, chord_pad, modifier_pads, is_recording, is_delete_held):
        # Returns whether the value was successfully changed
        super(BankPad, self).on_press(push)

        if is_delete_held:
            self.chord_pad = None
            self.modifier_pads = []

        # TODO?: Could also store just modifiers in the bank? Need to think design, might need color
        elif self.is_empty() and chord_pad:
            self.chord_pad = chord_pad
            self.modifier_pads = copy.deepcopy(modifier_pads)

    def on_release(self, push):
        super(BankPad, self).on_release(push)

    def press_color(self):
        if self.is_empty():
            return 'orange'
        else:
            return super(BankPad, self).press_color()

    def default_color(self):
        if self.is_empty():
            return 'blue'
        else:
            return 'yellow'

    def get_chord(self) -> FunChord:
        if self.chord_pad is None:
            return None
        return self.chord_pad.get_chord()

    def get_modifier(self) -> List[FunMod]:
        return [mod.get_modifier() for mod in self.modifier_pads]

    def delete(self):
        self.chord_pad = None
        self.modifier_pads = None
    
    def update(self, pad: FunPad):
        """
        Change stored pads. Replace ChordPad, toggle ModPads.
        """
        if type(pad) is ChordPad:
            self.chord_pad = pad
        elif type(pad) is ModPad:
            for idx, local_mod_pad in enumerate(self.modifier_pads):
                if pad.get_registry_id() == local_mod_pad.get_registry_id():
                    self.modifier_pads.pop(idx)
                    return

            # If no pad is removed, add it
            self.modifier_pads.append(pad)

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
