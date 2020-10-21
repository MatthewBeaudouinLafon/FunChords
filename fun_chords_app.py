import time
import numpy as np

import push2_python
import mido
import push2_python.constants

from fun_chord import FunChord
from fun_pad import PadRegistry, ChordPad, ModPad, BankPad, PianoNotePad
from chord_mod import Sus2, Sus4, Parallel, Add6, Add7, Add9, Add11
import note_util

def rids_from_chord(chord):
    rids = []
    for tone in chord.tones():
        name = note_util.number_to_name[tone % 12]
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
        self.active_scale_name = 'Cmaj'
        self.active_chord = None
        self.modifiers = []
        self.octave = 3
        self.voicing_center = 0  # scale note that the chord voicing will move towards
        self.note_ons = set()  # set of note-ons sent.
        self.previous_velocity = 64

        # Model
        maj_scale = note_util.RELATIVE_KEY_DICT['maj']
        self.pads = np.array([
            np.array([None, PianoNotePad((0, 1), 1), PianoNotePad((0, 2), 3), None, PianoNotePad((0, 4), 6), PianoNotePad((0, 5), 8), PianoNotePad((0, 6), 10), None, None]),  # black notes
            np.array([PianoNotePad((1, idx), tone) for idx, tone in enumerate(maj_scale)] + [None]),# [PianoNotePad((1, 7), 0)]),
            np.array([None] * 8),
            np.array([BankPad((3, col)) for col in range(8)]),
            np.array([ChordPad((4, degree), self.active_scale_name, degree + 1) for degree in range(7)] + [None]),
            np.array([ModPad((5, 0), Parallel)] + [None] * 7),
            np.array([ModPad((6, 0), Sus4), ModPad((6, 1), Add11), ModPad((6, 2), Add9)] + [None] * 5),
            np.array([ModPad((7, 0), Sus2), ModPad((7, 1), Add7), ModPad((7, 2), Add6)] + [None] * 5),
        ])

        self.registry = PadRegistry(self.pads)

        self.init_colors()

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

        # Start by setting all pad colors to white
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_STOP)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_NEW)

    def init_push(self):
        return push2_python.Push2(use_user_midi_port=True)

    def cg_voicing(self, tone, voicing_center):
        """
        Returns how many octaves up or down this note should be.

        tone (int): in scale tone (0 is root)
        """
        # Goal:
        # +1 +1 0 0 0 0 0 cg 0 0 0 0 0 0 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -2 -2 -2
        
        diff = tone - voicing_center

        top_thresh = 6
        bottom_thresh = -5
        if diff > 0:
            if diff <= top_thresh:
                return 0
            return -1 - ((diff - top_thresh) // 12)

        if diff > bottom_thresh:
            return 0
        
        # NOTE: bass shouldn't go below 1 octave
        # TODO: do the // operation just in case
        # (deal with the off by one since 5 // 2 = 2 but -5 // 2 = -3)
        return 1

        # bottom = max(0, voicing_center - 5)
        # top = min(11, voicing_center + 6)
        # # TODO: this doesn't handle extensions well, they sometimes need to be inverted twice down.
        # if tone < bottom:
        #     return 1
        # elif tone > top:
        #     return -1
        # else:
        #     return 0

    def compute_modded_chord(self):
        chord = self.active_chord

        if chord is None:
            return None

        for mod in self.modifiers:
            chord = mod(chord)

        return chord

    def play_active_chord(self, velocity):
        """
        Sends the midi message for the active chord. Use this after changing the active chord.
        """
        # TODO: use note_util.sorted_intervals_by_dissonance < 6 to select.
        # TODO: parametrize acceptable dissonance
        bad_intervals = [1, 2]
        bad_intervals += [-i for i in bad_intervals]
        chord = self.compute_modded_chord()

        if chord is None:
            return

        self.send_note_offs()
        tones = chord.tones()
        handled_notes = set()  # midi notes
        for idx, midi_note in enumerate(chord.midi_notes(self.octave)):
            # CG voicing
            voicing_diff = 12 * self.cg_voicing(tones[idx], self.voicing_center)
            midi_note = midi_note + voicing_diff

            # TODO: this can only work if I have two octaves to play with.
            # # adjust if there are dissonant notes
            # dissonant_notes = [midi_note + i for i in bad_intervals]
            
            # for note in dissonant_notes:
            #     if note in handled_notes:
            #         print(note, 'too close to', midi_note)
            #         midi_note += 12
            #         break
            # handled_notes.add(midi_note)

            # send notes
            msg = mido.Message('note_on', note=midi_note, velocity=velocity)
            self.midi_out_port.send(msg)
            self.note_ons.add(midi_note)

    def send_note_offs(self):
        for note in list(self.note_ons):
            msg = mido.Message('note_off', note=note)
            self.midi_out_port.send(msg)
            self.note_ons.remove(note)

    def stop(self):
        self.running = False

    def run_loop(self):
        print("Starting FunChord...")
        self.running = True
        # TODO: fix 'stop clip' button only half working?

        try:
            while self.running:
                # TODO: retry connection to push if possible, and reset starting colors
                time.sleep(0.1)
                pass
        except KeyboardInterrupt:
            self.end_app()

    def end_app(self):
        print("\nStopping FunChord...")
        # TODO: clear push ui
        self.send_note_offs()
        self.push.pads.set_all_pads_to_black()
        self.push.f_stop.set()
        self.midi_out_port.close()

@push2_python.on_button_pressed()
def on_button_pressed(_, button_name):
    if button_name in (push2_python.constants.BUTTON_NEW,
                       push2_python.constants.BUTTON_STOP,
                       push2_python.constants.BUTTON_SETUP,
                       push2_python.constants.BUTTON_USER):
        # Set pressed button color to white
        app.push.buttons.set_button_color(button_name, 'red')
        
    else:
        # Set pressed button color to white
        app.push.buttons.set_button_color(button_name, 'white')

@push2_python.on_button_released()
def on_button_released(_, button_name):
    # Set released button color to black (off)
    if button_name == push2_python.constants.BUTTON_STOP:
        app.stop()

    if button_name == push2_python.constants.BUTTON_SETUP:
            app.init_colors()

    if button_name in (push2_python.constants.BUTTON_NEW,
                       push2_python.constants.BUTTON_STOP,
                       push2_python.constants.BUTTON_SETUP,
                       push2_python.constants.BUTTON_USER):
        app.push.buttons.set_button_color(button_name, 'white')
    else:
        app.push.buttons.set_button_color(button_name, 'black')

# TODO: content of the pad callbacks should be in the app
@push2_python.on_pad_pressed()
def on_pad_pressed(_, pad_n, pad_ij, velocity):
    should_play_chord = False
    previous_modded_chord = app.compute_modded_chord()

    pad = app.pads[pad_ij[0]][pad_ij[1]]
    if pad:
        # Handle chord bank pads
        if type(pad) is BankPad:
            pad.on_press(app.push, app.active_chord, app.modifiers)
        else:
            pad.on_press(app.push)

        # Handle chords pads
        if pad.get_chord() is not None:
            app.active_chord = pad.get_chord()
            should_play_chord = True

        # Handle modifier pads
        get_mod = pad.get_modifier()
        # mod may be list if it's from a bank, or just the modifier
        mods = get_mod if type(get_mod) == list else [get_mod]
        for mod in mods:
            if mod is not None and mod not in app.modifiers:
                app.modifiers.append(mod)
                should_play_chord = True

    if should_play_chord:
        app.previous_velocity = velocity
        app.play_active_chord(velocity)

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


@push2_python.on_pad_released()
def on_pad_released(_, pad_n, pad_ij, velocity):
    should_release_notes = False
    modifier_changed = False
    previous_modded_chord = app.compute_modded_chord()
    pad = app.pads[pad_ij[0]][pad_ij[1]]
    if pad:        
        # Handle chords pads
        pad.on_release(app.push)
        if pad.get_chord() is not None: # TODO: and pad.get_chord() == app.active_chord:
            # TODO: this acts dumb if two chord pads are active, need to rethink this.
            app.active_chord = None
            should_release_notes = True

        # Handle modifier pads
        get_mod = pad.get_modifier()
        # mod may be list if it's from a bank, or just the modifier
        mods = get_mod if type(get_mod) == list else [get_mod]
        for mod in mods:
            if mod is not None and mod in app.modifiers:
                app.modifiers.remove(mod)
                modifier_changed = True

    if should_release_notes:
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

    elif modifier_changed:
        # replay the chord if the modifier changed
        app.play_active_chord(app.previous_velocity)

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
