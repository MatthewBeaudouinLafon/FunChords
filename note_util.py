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

def split_note_octave(name, default_octave=1):
    len_name = len(name)
    if len_name == 1:
        return (name, default_octave)

    if len_name == 2:
        # accidental eg C#
        if name[1] in ('#', 'b'):
            return (name, default_octave)

        # actual octave eg C1
        return name[0], name[1]

    if len_name == 3:
        # C#1
        if name[1] in ('#', 'b'):
            return name

        # C-1 or C10

def name_to_midi(name):
    """
    Convert nome formed as (note, accidental, octave) to midi note number.
    eg. C#2 -> 49
    """
    note, octave = name[:-1], int(name[-1:])

    if 'b' in note:
        note = flat_to_sharp[note]

    note_val = name_to_number[note]
    octave_offset = (octave + 2) * 12  # NOTE: octave starts at -2
    return note_val + octave_offset

def midi_to_name(midi, include_octave=False, accidental_preference='#'):
    assert accidental_preference in ('#', 'b'), "accidental_preference should be #, or b, not {}".format(accidental_preference)
    number_to_name = {
        0: "C",
        1: "C#",
        2: "D",
        3: "D#",
        4: "E",
        5: "F",
        6: "F#",
        7: "G",
        8: "G#",
        9: "A",
        10: "A#",
        11: "B"
    }

    sharp_to_flat = {
        "C#": "Db",
        "D#": "Eb",
        "F#": "Gb",
        "G#": "Ab",
        "A#": "Bb",
    }

    octave = midi // 12 - 2
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
    pass

# row index is the interval
interval_consonance = [1, 10, 8, 6, 4, 3, 7, 2, 5, 4, 9, 8]
sorted_interval_by_consonance = list(np.argsort(interval_consonance))
sorted_interval_by_dissonance = sorted_interval_by_consonance[::-1]

def cg_voicing(tone, voicing_center):
    """
    Returns how many octaves up or down this note should be.

    tone (int): in scale tone (0 is root)
    """
    # Goal: octave shift as shown below
    # +1 +1 0 0 0 0 0 cg 0 0 0 0 0 0 -1 -1 ...(7*'-1')... -1 -1 -2 -2 -2 etc.
    
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
