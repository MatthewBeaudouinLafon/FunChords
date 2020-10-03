import push2_python
import time
import mido
import push2_python.constants
from fun_chord import FunChord
from fun_pad import ChordPad
import note_util
import numpy as np

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
        self.note_ons = set()  # dict of note-ons sent.

        # Model
        self.pads = np.array([
            np.array([None] * 8),
            np.array([None] * 8),
            np.array([None] * 8),
            np.array([None] * 8),
            np.array([ChordPad((4, degree), self.active_scale_name, degree + 1) for degree in range(7)] + [None]),
            np.array([None] * 8),
            np.array([None] * 8),
            np.array([None] * 8),
        ])

        # Set all pads to their default color
        # TODO: Make this part of the init for Pad?
        for i in range(8):
            for j in range(8):
                pad = self.pads[i][j]
                if pad:
                    self.push.pads.set_pad_color((i,j), color=pad.default_color())
                else:
                    self.push.pads.set_pad_color((i,j), color='black')

    def init_push(self):
        push = push2_python.Push2(use_user_midi_port=True)
        
        # Start by setting all pad colors to white
        push.buttons.set_button_color(push2_python.constants.BUTTON_STOP)
        push.buttons.set_button_color(push2_python.constants.BUTTON_NEW)
        return push

    def play_active_chord(self, velocity):
        """
        Sends the midi message for the active chord. Use this after changing the active chord.
        """
        for note in self.active_chord.midi_notes():
            msg = mido.Message('note_on', note=note, velocity=velocity)
            self.midi_out_port.send(msg)
            self.note_ons.add(note)

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

        try:
            while self.running:
                # TODO: retry connection to push if possible, and reset starting colors
                pass
        except KeyboardInterrupt:
            self.end_app()

    def end_app(self):
        print("Stopping FunChord...")
        # TODO: clear push ui
        self.send_note_offs()
        self.push.f_stop.set()
        self.midi_out_port.close()

@push2_python.on_button_pressed()
def on_button_pressed(_, button_name):
    if button_name in (push2_python.constants.BUTTON_NEW, push2_python.constants.BUTTON_STOP):
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

    if button_name in (push2_python.constants.BUTTON_NEW, push2_python.constants.BUTTON_STOP):
        app.push.buttons.set_button_color(button_name, 'white')
    else:
        app.push.buttons.set_button_color(button_name, 'black')

@push2_python.on_pad_pressed()
def on_pad_pressed(_, pad_n, pad_ij, velocity):
    should_replay_chord = False

    pad = app.pads[pad_ij[0]][pad_ij[1]]
    if pad:
        pad.on_press(app.push)
        if pad.get_chord() is not None:
            app.active_chord = pad.get_chord()
            should_replay_chord = True
    
    if should_replay_chord:
        app.play_active_chord(velocity)


@push2_python.on_pad_released()
def on_pad_released(_, pad_n, pad_ij, velocity):
    should_release_notes = False
    pad = app.pads[pad_ij[0]][pad_ij[1]]
    if pad:
        pad.on_release(app.push)
        if pad.get_chord() is not None:
            # TODO: this acts dumb if two chord pads are active, probably the wrong architecture.
            app.active_chord = pad.get_chord()
            should_release_notes = True

    if should_release_notes:
        app.send_note_offs()

if __name__ == "__main__":
    app = FunChordApp()
    app.run_loop()
