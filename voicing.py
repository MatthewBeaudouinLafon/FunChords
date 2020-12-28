""" Functions for converting chord tones into voiced midi notes.

This file contains a few voicing algorithms to make experimentation easier. All functions take a
"voicing center", which represents the center of mass for notes, and an octave range. These
functions convert "tones" (12 notes in scale) to voiced midi notes.
"""

from enum import Enum, auto
from typing import List
from math import ceil
from copy import deepcopy

import note_util
# from fun_chord import FunChord

DEBUG = False
def dbprint(string=''):
    if DEBUG:
        print(string)

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

    # Algorithmically voices chord as they would (might?) be on a guitar.
    GUITAR = auto()

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
    Wrap all chord notes within the octave. Duplicate based on voicing range.
    TODO: Maybe have a spice-meter knob that disables bad intervals, from the bottom up.

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

    additional_octave_notes = []
    for octave in range(1, voicing_range - 1):
        for note in midi_notes:
            additional_octave_notes.append(note + 12 * octave)

    bass_note = []
    if bass_note:
        # NOTE: bass note goes quite far down in some cases.
        root_tone = chord.get_root_tone()
        root_midi = wrap_tone_around_midi(root_tone, voicing_center, chord.get_scale_note_name())
        bass_note = [root_midi - 12]

    return bass_note + midi_notes + additional_octave_notes

voicing_function[VoicingType.WRAP] = wrap_voicing


def spread_voicing(
        chord: 'FunChord',
        voicing_center: int,
        voicing_range: int,
        bass_note: bool,
    ):
    """
    Try to intelligently spread number of voices over two octaves. Fewer, simple notes in the
    bass, and more dense tension up top.

    Inspiration from:
    https://www.thejazzpianosite.com/jazz-piano-lessons/jazz-chord-voicings/chord-voicing-rules/
    https://www.thejazzpianosite.com/jazz-piano-lessons/jazz-chord-progressions/voice-leading/

    Args:
        chord: instance of funchord to be voiced.
        voicing_center: Midi note center of mass for voicing.
        voicing_range: Number of octaves spanned by the result, centered on voicing_center.
        bass_note: Whether to add a bass note.

    Returns:
        A list of midi notes.
    """
    raise NotImplementedError

voicing_function[VoicingType.SPREAD] = spread_voicing


def is_in_lane(tone, lower_bound, upper_bound):
    """
    Determine if a tone is within a tone "lane", accounting for octave wraparound.
    """
    # Chord tones may be above 12 to represent above octave notes
    # To check if it's in a lane, we must mod 12 for the comparison to work.
    tone = tone % 12

    if lower_bound <= upper_bound:
        # String tones are within one octave eg. 4 and 9 for E and A
        dbprint("{} <= {} <= {} is {}".format(lower_bound, tone, upper_bound, lower_bound <= tone <= upper_bound))
        return lower_bound <= tone <= upper_bound
    else:
        # String tones wrap around the octave eg. 9 and 2 for A and D
        dbprint("{} <= {} or {} <= {} is {}".format(tone, lower_bound, upper_bound, tone, tone <= lower_bound or upper_bound <= tone))
        return tone <= lower_bound or upper_bound <= tone

def guitar_voicing(
        chord: 'FunChord',
        voicing_center: int,
        voicing_range: int,
        bass_note: bool,
    ):
    """
    Algorithmically voice chords like a guitar. It allocates one note per "string", starting with
    the lowest notes.

    TODO: The bass notes inversions are pretty bad. Either hardcode that or figure out a better way
    to allocate notes.
    TODO: This doesn't guarantee making "usable chords" since it doesn't take hand range into
    account.

    Args:
        chord: instance of funchord to be voiced.
        voicing_center: Midi note center of mass for voicing.
        voicing_range: Number of octaves spanned by the result, centered on voicing_center.
        bass_note: Whether to add a bass note.

    Returns:
        A list of midi notes.
    """
    # Prep info about each open string
    octave_center = note_util.midi_note_nearest_name_octave(voicing_center)
    guitar_note_names = list('EADGBE')
    # relative_octave_list = [-1, -1, 0, 0, 0, 1]  # TODO: automagically compute?
    relative_octave_list = [0, 0, 1, 1, 1, 2]  # TODO: automagically compute?

    guitar_midi = []
    for idx, note in enumerate(guitar_note_names):
        note_octave = relative_octave_list[idx] + octave_center
        guitar_midi.append(note_util.name_to_midi(note + str(note_octave)))

    guitar_tones = [note_util.name_to_number[name] for name in guitar_note_names]
    guitar_tones.append((guitar_tones[-1] + 5) % 12)  # add hypothetical string to make lanes work
    # TODO: replace "5" with the most common or minimum lane gap.

    # Assign chord tones to each string.
    midi_notes = []

    chord_tones = chord.tones()
    remaining_notes = deepcopy(chord_tones)
    num_attempts = 0  # number of notes attempted
    for idx, string_tone in enumerate(guitar_tones[:-1]):  # For each lane...
        next_string_tone = guitar_tones[idx + 1]
        octave = octave_center + relative_octave_list[idx]

        # Refresh remaining notes
        if len(remaining_notes) == 0:
            # TODO: find a better way to reintroduce extension notes instead of root/5th
            dbprint("Replenish notes")
            remaining_notes = deepcopy(chord_tones)

        if num_attempts == len(chord_tones) - 1:
            # Failed to put any note in this lane, skip it
            dbprint("Skipping string {} ({})".format(idx, guitar_note_names[idx]))
            num_attempts = 0
            continue

        dbprint("On string {} ({})".format(idx, guitar_note_names[idx]))
        # Find chord note that fits in this lane 
        for tone in remaining_notes:
            dbprint("Try placing {}".format(tone))
            if is_in_lane(tone, string_tone, next_string_tone):
                midi_notes.append(note_util.tone_to_midi(tone, octave))

                # Remove first occurence of the note, which works because we're stepping forward
                # through the tones.
                # TODO: for the initial triad, if the first note doesn't fit we're likely to get
                # 3-1-5, which is a bad voicing (huge leap at the bottom).
                remaining_notes.remove(tone)
                num_attempts = 0
                break
            num_attempts += 1
        dbprint()
    dbprint('-'*8+'\n')

    return midi_notes

voicing_function[VoicingType.GUITAR] = guitar_voicing


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
