import push2_python
import push2_python.constants
import mido
import time

# Init Push2
push = push2_python.Push2(use_user_midi_port=True)
# print(mido.get_output_names())
# print(push.midi_out_port)

# Init Virtual Port for DAW
virtual_outport = mido.open_output('Funchord Port', virtual=True)

# Game loop
running = True

def quit():
    print("Stop?")
    running = False

# Start by setting all pad colors to white
push.pads.set_all_pads_to_color('white')
push.buttons.set_button_color(push2_python.constants.BUTTON_STOP)
push.buttons.set_button_color(push2_python.constants.BUTTON_NEW)
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
def on_button_pressed(push, button_name):
    if button_name in (push2_python.constants.BUTTON_NEW, push2_python.constants.BUTTON_STOP):
        # Set pressed button color to white
        push.buttons.set_button_color(button_name, 'red')
    else:
        # Set pressed button color to white
        push.buttons.set_button_color(button_name, 'white')

@push2_python.on_button_released()
def on_button_released(push, button_name):
    # Set released button color to black (off)
    if button_name == push2_python.constants.BUTTON_STOP:
        quit()

    if button_name in (push2_python.constants.BUTTON_NEW, push2_python.constants.BUTTON_STOP):
        push.buttons.set_button_color(button_name, 'white')
    else:
        push.buttons.set_button_color(button_name, 'black')

@push2_python.on_pad_pressed()
def on_pad_pressed(push, pad_n, pad_ij, velocity):
    # Set pressed pad color to green
    push.pads.set_pad_color(pad_ij, 'green')
    msg = mido.Message('note_on', note=note_to_number('C0'), channel=1)
    virtual_outport.send(msg)
    # push.send_midi_to_push(msg)
    # print(msg)
    # push.midi_out_port.send(msg)


@push2_python.on_pad_released()
def on_pad_released(push, pad_n, pad_ij, velocity):
    # Set released pad color back to white
    push.pads.set_pad_color(pad_ij, 'white')
    msg = mido.Message('note_off', note=note_to_number('C0'), channel=1)
    virtual_outport.send(msg)
    # push.send_midi_to_push(msg)
    # print(msg)
    # push.midi_out_port.send(msg)

# Start infinite loop so the app keeps running
print('App runnnig...')
try:
    while running:
        # Try to configure Push2 MIDI at every iteration (if not already configured)
        # if not push.midi_is_configured():
        #     print("midi not configured")
        #     push.configure_midi()
        # else:
        #     print(mido.get_output_names())
        #     print(push.midi_out_port)
        #     print()
        # time.sleep(1)
        pass
except KeyboardInterrupt:
    # Quit cleanly
    print("Quitting...")
    virtual_outport.close()
    push.f_stop.set()

if not running:
    print("Quitting...")
    virtual_outport.close()
    push.f_stop.set()
