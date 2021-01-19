import time
import numpy as np
from typing import List, Tuple
from copy import deepcopy

import push2_python
import mido
import push2_python.constants

from fun_chord import FunChord
from fun_pad import PadRegistry, ChordPad, ModPad, BankPad, PianoNotePad, FunPad
from chord_mod import Sus2, Sus4, Parallel, Add6, Add7, Add9, Add11
import note_util

def rids_from_chord(chord: FunChord):
    rids = []
    root = chord.get_scale_root_tone()
    for tone in chord.tones():
        name = note_util.number_to_name[(tone + root) % 12]
        rids.append('Note: ' + name)

    return rids

# TODO: Revisit voicing stuff
class FunChordApp(object):
    """
    App handles midi connection, interface with midi and push2.
    """
    def __init__(self):
        # Init Push2 in User Mode to work smoothly with Ableton
        self.push = self.init_push()

        # Init Virtual Port for DAW
        self.midi_out_port = mido.open_output('Funchord Port', virtual=True)

        # Main loop
        self.running = False

        # Harmony
        # self.active_scale_name = 'Dmin'
        # self.active_scale_name = 'Emin'
        self.active_scale_name = 'Cmaj'
        self.modifiers = []  # TODO: merge functionality with _active_pad_stack?

        # Recording chords
        self.is_recording = False
        
        # TODO: next time I change this, I'm refactoring it into its own class.
        # List of (pad, velocity_when_played). Use related methods.
        self._active_pad_stack: List[Tuple[FunPad, int]] = []

        # midi note that the chord voicing will move towards
        self.voicing_center = note_util.name_to_midi('C3')

        self.note_ons = set()  # set of note-ons sent.

        # Model
        maj_scale = note_util.RELATIVE_KEY_DICT['maj']
        self.pads = np.array([
            np.array([None, PianoNotePad((0, 1), 1), PianoNotePad((0, 2), 3), None, PianoNotePad((0, 4), 6), PianoNotePad((0, 5), 8), PianoNotePad((0, 6), 10), None, None]),  # black notes
            np.array([PianoNotePad((1, idx), tone) for idx, tone in enumerate(maj_scale)] + [None]),# [PianoNotePad((1, 7), 0)]),  TODO: make the registry support duplicates
            np.array([None] * 8),
            np.array([BankPad((3, col)) for col in range(8)]),
            np.array([ChordPad((4, degree), self.active_scale_name, degree + 1) for degree in range(7)] + [None]),
            np.array([ModPad((5, 0), Parallel)] + [None] * 7),
            np.array([ModPad((6, 0), Sus4), ModPad((6, 1), Add11), ModPad((6, 2), Add9)] + [None] * 5),
            np.array([ModPad((7, 0), Sus2), ModPad((7, 1), Add7), ModPad((7, 2), Add6)] + [None] * 5),
        ], dtype=object)

        self.registry = PadRegistry(self.pads)

        self.init_colors()

    def get_active_chord(self) -> FunChord:
        # Find the last pad that has a chord.
        for pad, _ in self._active_pad_stack[::-1]:
            chord = pad.get_chord()
            if chord is not None:
                return chord
        return None

    def get_active_chord_velocity(self) -> int:
        # Find the last pad that has a chord, that's the velocity we care about.
        for pad, velocity in self._active_pad_stack[::-1]:
            chord = pad.get_chord()
            if chord is not None:
                return velocity
        return None

    def append_active_pad(self, pad: FunPad, velocity: int):
        self._active_pad_stack.append((pad, velocity))

    def remove_active_pad(self, target_pad):
        """
        Removes target_chord from the list of active chords.
        Returns True if that's the playing chord (top of the stack), false otherwise.
        """
        if len(self._active_pad_stack) == 0:
            print("Warning: tried to remove chord from empty stack. This is likely because the pad was pressed before push was ready.")
            return False            

        active_chord_seen = False  # active chord is the last chord-pad (ChordPad or BankPad)
        idx = len(self._active_pad_stack) - 1  # traverse backwards to catch active chord
        for pad, _ in self._active_pad_stack[::-1]:
            assert idx >= 0, "Index math is wrong!"
            chord = pad.get_chord()

            if pad is target_pad:
                self._active_pad_stack.pop(idx)
                if chord is not None and not active_chord_seen:
                    # this is a chord pad and we haven't seen another before
                    return True
                return False
            
            if chord is not None:
                active_chord_seen = True

            idx -= 1

        # Removed nothing
        return False

    def has_active_chords(self) -> bool:
        """
        Returns whether there are chord pads in the active_pad_stack
        """
        for pad, _ in self._active_pad_stack[::-1]:
            if pad.get_chord() is not None:
                return True
        return False

    # TODO: toggle button behavior will eventually go into a button handling class
    def set_record_button_color(self):
        """
        Sets the appropriate color for the record button.
        """
        color = 'red' if self.is_recording else 'white'
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_RECORD, color=color)

    def toggle_record(self):
        self.is_recording = not self.is_recording
        self.set_record_button_color()

    def set_recording_off(self):
        self.is_recording = False
        self.set_record_button_color()

    def color_wipe(self):
        self.push.pads.set_all_pads_to_black()

    def init_colors(self):
        # Set all pads to their default color
        # TODO: Make this part of the init for Pad?
        for i in range(8):
            for j in range(8):
                pad = self.pads[i][j]
                if pad:
                    self.push.pads.set_pad_color((i,j), color=pad.default_color())
                else:
                    self.push.pads.set_pad_color((i,j), color='black')

        # Set button colors to white
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_STOP)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_SETUP)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_RECORD)

    def init_push(self):
        return push2_python.Push2(use_user_midi_port=True)

    def play_midi_note(self, midi_note, velocity):
        if velocity == 0:
            print("Warning: 0 velocity note on is treated by note off according to MIDI")
        msg = mido.Message('note_on', note=midi_note, velocity=velocity)
        self.midi_out_port.send(msg)
        self.note_ons.add(midi_note)

    def compute_modded_chord(self):
        chord = self.get_active_chord()

        if chord is None:
            return None

        for mod in self.modifiers:
            chord = mod(chord)

        return chord

    def play_active_chord(self):
        """
        Sends the midi message for the active chord. Use this after changing the active chord.
        """
        chord = self.compute_modded_chord()
        velocity = self.get_active_chord_velocity()

        if chord is None:
            return

        self.send_note_offs()
        for midi_note in chord.midi_notes(self.voicing_center):
            self.play_midi_note(midi_note, velocity)

    def send_note_offs(self):
        for note in list(self.note_ons):
            msg = mido.Message('note_off', note=note)
            self.midi_out_port.send(msg)
            self.note_ons.remove(note)

    def stop_loop(self):
        self.running = False

    def run_loop(self):
        print("\nPress [Setup] to refresh color (after switching User modes)")
        print("Starting FunChord...")
        self.running = True

        try:
            while self.running:
                # TODO: retry connection to push if possible, and reset starting colors
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass

        self.end_app()  # when self.running is False

    def end_app(self):
        print("\nStopping FunChord...")
        self.send_note_offs()
        self.push.pads.set_all_pads_to_black()
        self.push.buttons.set_all_buttons_color('black')
        self.push.f_stop.set()
        print("Push2Python ended.")
        self.midi_out_port.close()
        print("MIDI port closed.")

@push2_python.on_button_pressed()
def on_button_pressed(_, button_name):
    if button_name in (push2_python.constants.BUTTON_STOP):
        # Set pressed button color to red
        app.push.buttons.set_button_color(button_name, 'red')
        
    # TODO: should be part of the button handling magic
    if button_name == push2_python.constants.BUTTON_RECORD:
        if not app.is_recording:
            app.push.buttons.set_button_color(button_name, 'light_gray')

    else:
        # Set pressed button color to white
        app.push.buttons.set_button_color(button_name, 'white')

@push2_python.on_button_released()
def on_button_released(_, button_name):
    # Set released button color to black (off)
    if button_name == push2_python.constants.BUTTON_STOP:
        app.stop_loop()
        # app.push.buttons.set_button_color(button_name, 'white')

    elif button_name == push2_python.constants.BUTTON_USER:
        app.color_wipe()
        app.init_colors()
        # app.push.buttons.set_button_color(button_name, 'white')

    elif button_name == push2_python.constants.BUTTON_SETUP:
        app.color_wipe()
        app.init_colors()
        # app.push.buttons.set_button_color(button_name, 'white')

    elif button_name == push2_python.constants.BUTTON_RECORD:
        app.toggle_record()

    else:
        app.push.buttons.set_button_color(button_name, 'black')

# TODO: content of the pad callbacks should be in the app
@push2_python.on_pad_pressed()
def on_pad_pressed(_, pad_n, pad_ij, velocity):
    should_play_chord = False
    previous_modded_chord = app.compute_modded_chord()

    pad = app.pads[pad_ij[0]][pad_ij[1]]
    if pad:
        app.append_active_pad(pad, velocity)

        # Handle chord bank pads
        if type(pad) is BankPad:
            changed = pad.on_press(app.push, app.get_active_chord(), app.modifiers, app.is_recording)
            if changed:
                app.set_recording_off()
        else:
            pad.on_press(app.push)

        # Handle chords pads
        if pad.get_chord() is not None:
            should_play_chord = True

        # Handle modifier pads
        get_mod = pad.get_modifier()
        # mod may be list if it's from a bank, or just the modifier
        mods = get_mod if type(get_mod) == list else [get_mod]
        for mod in mods:
            if mod is not None and mod not in app.modifiers:
                app.modifiers.append(mod)
                should_play_chord = True

    # Handle highlights and midi accordingly
    if should_play_chord:
        app.play_active_chord()

        # Highlight related pads through the Registry
        modded_chord = app.compute_modded_chord()
        if previous_modded_chord:
            # Clear previous pads
            for rid in rids_from_chord(previous_modded_chord):
                app.registry[rid].registry_release_highlight(app.push)

        if modded_chord:
            # Highlight new pads
            for rid in rids_from_chord(modded_chord):
                app.registry[rid].registry_highlight(app.push)


# TODO: content of the pad callbacks should be in the app
@push2_python.on_pad_released()
def on_pad_released(_, pad_n, pad_ij, velocity):
    should_release_notes = False
    should_play_chord = False
    modifier_changed = False
    previous_modded_chord = app.compute_modded_chord()
    pad = app.pads[pad_ij[0]][pad_ij[1]]
    if pad:        
        # Handle chords pads
        pad.on_release(app.push)
        if app.remove_active_pad(pad):
            # The playing chord was removed
            should_play_chord = True

        if pad.get_chord() is not None and not app.has_active_chords():
            should_release_notes = True

        # Handle modifier pads
        get_mod = pad.get_modifier()
        # mod may be list if it's from a bank, or just the modifier
        mods = get_mod if type(get_mod) == list else [get_mod]
        for mod in mods:
            if mod is not None and mod in app.modifiers:
                app.modifiers.remove(mod)
                modifier_changed = True
    
    # Handle highlights and midi accordingly
    # NOTE: We always release chord pads, but they may be played immediately after
    if should_release_notes:
        # should release all notes if the last active chord was released
        app.send_note_offs()

        # Release highlight related pads through the Registry
        new_computed_chord = app.compute_modded_chord()
        if previous_modded_chord:
            chord = previous_modded_chord if new_computed_chord is None else new_computed_chord

            # TODO: could probably be optimized to make fewer calls
            # Release previous pads
            # for rid in rids_from_chord(previous_modded_chord):
            #     app.registry[rid].registry_release_highlight(app.push)

            # Highlight new pads
            for rid in rids_from_chord(chord):
                app.registry[rid].registry_release_highlight(app.push)

    if should_play_chord:
        # Should only play a chord if the currently playing chord was released
        app.play_active_chord()

        # Highlight related pads through the Registry
        modded_chord = app.compute_modded_chord()
        if previous_modded_chord:
            # Clear previous pads
            for rid in rids_from_chord(previous_modded_chord):
                app.registry[rid].registry_release_highlight(app.push)

        if modded_chord:
            # Highlight new pads
            for rid in rids_from_chord(modded_chord):
                app.registry[rid].registry_highlight(app.push)

    elif modifier_changed:
        # replay the chord if the modifier changed
        app.play_active_chord()

        # Highlight related pads through the Registry
        new_computed_chord = app.compute_modded_chord()
        if previous_modded_chord:
            chord = previous_modded_chord if new_computed_chord is None else new_computed_chord

            # TODO: could probably be optimized to make fewer calls
            # Release previous pads
            for rid in rids_from_chord(previous_modded_chord):
                app.registry[rid].registry_release_highlight(app.push)

            # Highlight new pads
            for rid in rids_from_chord(chord):
                app.registry[rid].registry_highlight(app.push)

if __name__ == "__main__":
    app = FunChordApp()
    app.run_loop()
