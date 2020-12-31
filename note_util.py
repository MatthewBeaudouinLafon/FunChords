"""
Utlities to convert between note names, scale degrees, midi values.
"""

import numpy as np

name_to_number = {
    "C": 0,
    "C#": 1,
    "D": 2,
    "D#": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "G": 7,
    "G#": 8,
    "A": 9,
    "A#": 10,
    "B": 11,
}

number_to_name = {value: key for key, value in name_to_number.items()}

sharp_to_flat = {
    "C#": "Db",
    "D#": "Eb",
    "F#": "Gb",
    "G#": "Ab",
    "A#": "Bb",
}

flat_to_sharp = {value: key for key, value in sharp_to_flat.items()}

def tone_to_midi(tone, midi_octave):
    return tone + midi_octave * 12

def name_to_midi(name):
    """
    Convert nome formed as (note, accidental, octave) to midi note number.
    eg. C#2 -> 49
    """
    # TODO: regex
    note, octave = name[:-1], int(name[-1:])

    if 'b' in note:
        note = flat_to_sharp[note]

    note_val = name_to_number[note]
    return tone_to_midi(note_val, octave + 2)  # NOTE: octave in name starts at -2

def midi_note_octave(midi_note):
    return midi_note // 12 - 2

def midi_note_nearest_name_octave(midi_note):
    octave = midi_note_octave(midi_note) + 2  # NOTE: octave in name starts at -2
    tone = midi_note % 12
    if tone >= 6:
        octave += 1
    return octave

def midi_to_name(midi: int, include_octave=False, accidental_preference='#'):
    assert accidental_preference in ('#', 'b'), "accidental_preference should be #, or b, not {}".format(accidental_preference)

    octave = midi_note_octave(midi)
    tone = midi % 12

    note_name = number_to_name[tone]

    if len(note_name) > 1:
        note_name = note_name if accidental_preference == '#' else sharp_to_flat[note_name]

    if include_octave:
        return note_name + str(octave)

    return note_name

def interval_note(note_name: str, interval: int) -> str:
    midi = name_to_midi(note_name)
    new_midi = midi + interval
    NotImplemented

RELATIVE_KEY_DICT = {
    'maj': [0, 2, 4, 5, 7, 9, 11],
    'min': [0, 2, 3, 5, 7, 8, 10],
}

def scalenumber_to_note(number, scale):
    # assert 0 <= number < 12, "note number out of range"
    raise NotImplementedError

# row index is the interval
interval_consonance = [1, 10, 8, 6, 4, 3, 7, 2, 5, 4, 9, 8]
sorted_interval_by_consonance = list(np.argsort(interval_consonance))
sorted_interval_by_dissonance = sorted_interval_by_consonance[::-1]


if __name__ == "__main__":
    print("Sorted interval by consonance")
    print(sorted_interval_by_consonance)
    print()

    note = 'D#2'
    print(note)
    midi = name_to_midi(note)
    print(midi)
    print(midi_to_name(midi, include_octave=True))
    print()
    
    note = 'Gb-1'
    print(note)
    midi = name_to_midi(note)
    print(midi)
    print(midi_to_name(midi, include_octave=True, accidental_preference='b'))
