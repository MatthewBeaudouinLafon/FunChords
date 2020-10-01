"""
Utlities to convert between note names, scale degrees, midi values.
"""

def name_to_midi(name):
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

RELATIVE_KEY_DICT = {
    'maj': [0, 2, 4, 5, 7, 9, 11],
    'min': [0, 2, 3, 5, 7, 8, 10],
}

def scalenumber_to_note(number, scale):
    # assert 0 <= number < 12, "note number out of range"
    pass
