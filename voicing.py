""" Functions for converting chord tones into voiced midi notes.

This file contains a few voicing algorithms to make experimentation easier. All functions take a
"voicing center", which represents the center of mass for notes, and an octave range. These
functions convert "tones" (12 notes in scale) to voiced midi notes.
"""

from enum import Enum, auto
from typing import List
from math import ceil

import note_util
# from fun_chord import FunChord

class VoicingType(Enum):
    #TODO: All functions can play an additional note in the bass an octave below?

    # Play chords in root position
    ROOT = auto()

    # Play all chord notes over n octaves. Useful to fold piano roll in Ableton.
    FULL = auto()

    # Only play the chord's root note. Useful for starting basslines.
    BASS = auto()

    # Wrap notes into an octave range
    WRAP = auto()

    # TODO
    SPREAD = auto()

voicing_function = {}

# Utilities
def midify_tone(tone, scale_root, octave):
    """ Convert a tone to midi. """
    scale_root_midi_name = str(scale_root) + str(octave)
    root_midi = note_util.name_to_midi(scale_root_midi_name)
    return root_midi + tone

def wrap_tone_around_midi(tone, voicing_center, scale_root_name, wrap_range=12):
    """
    Convert tone to midi and place it within 6 semitones from the voicing center.

    Args:
        tone: Scale tone, 0 is root of scale.
        voicing_center: Midi note center of mass for voicing.
        scale_root_name: Name of the root of the scale.
        wrap_range: total range of possible notes after wrap.

    Returns:
        Tone as midi note close to the voicing center.
    """
    center_octave = note_util.midi_note_octave(voicing_center)
    midi_note = midify_tone(tone, scale_root_name, center_octave)

    # Since 12 is even, we need bias the wrap to leave more notes above (less muddy) 
    # with 11 // 2 -> 0 1 2 3 4 Center 6 7 8 9 10 11
    bottom_thresh = -1 * ((wrap_range - 1) // 2)
    top_thresh = (wrap_range // 2)

    # Searching for n = number of octave shifts s.t. n is a signed integer and:
    # voicing_center + bottom_thresh < midi_note + 12*n < voicing_center + top_thresh
    # so where diff = voicing_center - midi_note
    # (diff + bottom_thresh) / 12 < n < (diff + top_thresh) / 12
    # so the first valid is the first integer above the lower bound, which should be below the upper
    # bound.
    diff = voicing_center - midi_note
    lower_bound = (diff + bottom_thresh) / 12.
    upper_bound = (diff + top_thresh) / 12.
    
    # dodge floating point weirdness near integers
    if float(lower_bound).is_integer():
        lower_bound = int(round(lower_bound))

    octave_shifts = int(ceil(lower_bound))
    assert octave_shifts < upper_bound, "Wrap algorithm broke: lower_bound ({}) < ceil_lower_bound ({}) is not < upper bound ({})".format(
        lower_bound, int(ceil(lower_bound)), upper_bound)

    return midi_note + 12 * octave_shifts

    # while not (bottom_thresh <= (midi_note - voicing_center) <= top_thresh):
    #     if midi_note < center_octave and voicing_center - midi_note > 5:
    #         # Note too low
    #         midi_note += 12
    #     elif midi_note > center_octave and midi_note - voicing_center > 6:
    #         # Note too high
    #         midi_note -= 12
    #     else:
    #         assert False, "Shouldn't be here! (midi_note - voicing_center) = ({} - {}) = {}".format(midi_note, voicing_center, midi_note - voicing_center)

    # return midi_note

# Voicing types
def root_voicing(
        chord: 'FunChord',
        voicing_center: int,
        voicing_range: int,
        bass_note: bool,
    ):
    """
    Voice chords in root position near the voicing center.

    Args:
        chord: instance of funchord to be voiced.
        voicing_center: Midi note center of mass for voicing.
        voicing_range: Number of octaves spanned by the result, centered on voicing_center.
        bass_note: Whether to add a bass note.

    Returns:
        A list of midi notes.
    """
    root_tone = chord.get_root_tone()
    root_midi = wrap_tone_around_midi(root_tone, voicing_center, chord.get_scale_note_name())
    midi_notes = [root_midi]
    
    for tone in chord.tones()[1:]:
        dist_from_root = tone - root_tone
        midi_notes.append(root_midi + dist_from_root)
        
    bass_midi_note = []
    if bass_note:
        bass_midi_note = [midi_notes[0] - 12]

    if voicing_range == 1:
        return bass_midi_note + midi_notes

    # Add additional octaves as needed.
    new_octave_notes = []
    for octaves in range(1, voicing_range):
        for note in midi_notes:
            new_octave_notes.append(note + 12 * octaves)

    return bass_midi_note + midi_notes + new_octave_notes

voicing_function[VoicingType.ROOT] = root_voicing


def bass_voicing(
        chord: 'FunChord',
        voicing_center: int,
        voicing_range: int,
        bass_note: bool,
    ):
    """
    Just play the root of each chord near the voicing center.

    Args:
        chord: instance of funchord to be voiced.
        voicing_center: Midi note center of mass for voicing.
        voicing_range: Number of octaves spanned by the result, centered on voicing_center.
        bass_note: Whether to add a bass note.

    Returns:
        A list of midi notes.
    """
    return [wrap_tone_around_midi(chord.get_root_tone(), voicing_center, chord.get_scale_note_name())]

voicing_function[VoicingType.BASS] = bass_voicing


def wrap_voicing(
        chord: 'FunChord',
        voicing_center: int,
        voicing_range: int,
        bass_note: bool,
    ):
    """
    Wrap all chord notes within the octave

    Args:
        chord: instance of funchord to be voiced.
        voicing_center: Midi note center of mass for voicing.
        voicing_range: Number of octaves spanned by the result, centered on voicing_center.
        bass_note: Whether to add a bass note.

    Returns:
        A list of midi notes.
    """
    midi_notes = []
    for tone in chord.tones():
        midi_notes.append(wrap_tone_around_midi(tone, voicing_center, chord.get_scale_note_name()))

    if bass_note:
        # NOTE: bass note goes quite far down in some cases.
        root_tone = chord.get_root_tone()
        root_midi = wrap_tone_around_midi(root_tone, voicing_center, chord.get_scale_note_name())
        midi_notes = [root_midi - 12] + midi_notes

    return midi_notes

voicing_function[VoicingType.WRAP] = wrap_voicing

# Actual function to use
def voice(chord: 'FunChord',
          voicing_center: int,
          voicing_range: int,
          bass_note: bool,
          voicing_type: VoicingType = VoicingType.ROOT) -> List[int]:
    """
    Convert chord tones to midi notes using a given voicing type (ie. algorithm).

    Args:
        chord: instance of funchord to be voiced.
        voicing_center: Midi note center of mass for voicing.
        voicing_range: Number of octaves spanned by the result, centered on voicing_center.
            Note that the voicing type aren't guaranteed to strictly enforce this.
        bass_note: Whether to add a bass note.
        voicing_type: Algorithm to voice the chord.

    Returns:
        A list of midi notes.
    """
    assert voicing_range > 0, "Voicing range {} <= 0".format(voicing_range)

    voicing = voicing_function[voicing_type]    
    return voicing(chord, voicing_center, voicing_range, bass_note)
