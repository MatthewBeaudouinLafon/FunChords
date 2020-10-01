import push2_python
import time
import mido
import push2_python.constants
import chord
import note_util

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
        self.active_scale = note_util.RELATIVE_KEY_DICT['maj']
        self.active_chord = None
        self.note_ons = set()  # dict of note-ons sent.

    def init_push(self):
        push = push2_python.Push2(use_user_midi_port=True)
        
        # Start by setting all pad colors to white
        push.pads.set_all_pads_to_color('white')
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

def note_to_number(name):
    """
    Convert nome formed as (note, accidental, octave) to midi note number.
    eg. C#2 -> 49
    """
    letter_to_number = {
        "C": 0,
        "D": 2,
        "E": 4,
        "F": 5,
        "G": 7,
        "A": 9,
        "B": 11,
    }

    note, octave = name[:-1], int(name[-1])
    note_val = letter_to_number[note[0]]
    if len(note) == 2:
        accidental = note[-1]
        if accidental == "#":
            note_val += 1
        elif accidental == "b":
            note_val -= 1
        
    octave_offset = (octave + 2) * 12  # NOTE: octave starts at -2
    return note_val + octave_offset

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
    # Set pressed pad color to green
    app.push.pads.set_pad_color(pad_ij, 'green')
    app.active_chord = chord.FunChord('Cmaj', 1)
    app.play_active_chord(velocity)


@push2_python.on_pad_released()
def on_pad_released(_, pad_n, pad_ij, velocity):
    # Set released pad color back to white
    app.push.pads.set_pad_color(pad_ij, 'white')
    app.send_note_offs()

if __name__ == "__main__":
    app = FunChordApp()
    app.run_loop()
