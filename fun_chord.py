import note_util
import numpy as np

class ScaleNote(object):
    """
    """
    # TODO: re-evaluate 0 vs 1 indexing for scale degrees
    MAX_SCALE_NOTE = 7
    def __init__(self, note):
        if type(note) is int:
            assert note > 0, "ScaleNote input is 1-indexed; {} out of range".format(note)
            self._note = note - 1
            self._accidental = 0
            return

        if type(note) is str:
            if '#' not in note and 'b' not in note:
                assert int(note) > 0, "ScaleNote input is 1-indexed; {} out of range".format(note)
                self._note = int(note) - 1
                self._accidental = 0
                return

            assert note[0] in ("#", "b"), "ScaleNote accidental '{}' should be # or b".format(note[0])

            note_number = int(note[1:])
            assert note_number > 0, "ScaleNote input is 1-indexed; {} out of range".format(note_number)

            self._note = int(note_number) - 1
            self._accidental = 1 if note[0] == "#" else -1
            return

        raise TypeError

    def __add__(self, other):
        if type(other) is int:
            new_note = (self._note + other)
            return ScaleNote(str(new_note) + self.accidental_str())
        elif type(other) is ScaleNote:
            new_note = self._note + other._note
            new_accidental = self._accidental + other._accidental

            if new_accidental == 2:
                new_accidental = 0
                new_note += 1
            elif new_accidental == -2:
                new_accidental = 0
                new_note -= 1

            return ScaleNote(self.accidental_to_str(new_accidental) + str(new_note + 1))
        else:
            raise TypeError("unsupported operand type(s) for +: '{}' and '{}'".format(type(self), type(other)))

    def __repr__(self):
        # NOTE: root degree is 1, so notes are 1-indexed for reading (but 0-indexed internally)
        return "Scale Note({})".format(self.accidental_str() + str(self._note + 1))

    def __eq__(self, other):
        # TODO: invert note into octave, check for #x == b(x+1).
        pass

    def is_root(self):
        return self._note == 0

    def in_octave(self):
        """
        Return note within an octave ie. inverted to 0-7.
        """
        return self._note % (self.MAX_SCALE_NOTE + 1)

    def accidental_str(self):
        return self.accidental_to_str(self._accidental)

    @staticmethod
    def accidental_to_str(accidental):
        if accidental == -1:
            return 'b'
        elif accidental == 0:
            return ''
        elif accidental == 1:
            return '#'

class FunChord(object):
    """
    Chord function in a scale
    """
    def __init__(self, scale_name, degree, octave=1, extensions=[]):
        """
        scale_name (str): Name of the scale eg. Cmin, G#maj, etc.
        degree (int): scale degree of the chord's root note (root at 1)
        """
        assert len(scale_name) >= 4, "Scale name {} should be formatted as (note letter)(accidental)(min|maj)"

        # Take scale appart
        quality = scale_name[-3:]  # "min"|"maj"
        note = scale_name[:-3]  # note with accidental
        
        self._scale_root = note  # scale root note name
        self._scale = note_util.RELATIVE_KEY_DICT[quality]  # 7-note scale
        self._degree = ScaleNote(degree)  # scale degree of the chord's root note
        self._extensions = [ScaleNote(note) for note in extensions]
        self._octave = octave

    def __eq__(self, other):
        # TODO: invert extensions into octave, compare notes in 12 tones.
        pass

    def is_root(self):
        return self._degree.is_root()

    def triad_notes(self):
        """
        Returns first three notes of the chord.
        """
        # NOTE: note inputs are 1-indexed
        return [ScaleNote(1 + (2 * n)) for n in range(0,3)]

    def scale_notes(self):
        """
        Returns the notes in scale used.
        """
        chord_notes = self.triad_notes() + self._extensions
        scale_notes = [(self._degree + scale_note) for scale_note in chord_notes]
        return scale_notes

    def tones(self):  # TODO: find better name for 0-11
        """
        Returns notes in twelve tone value.
        """
        tones = []
        for scale_note in self.scale_notes():
            note_index = scale_note._note

            scale_len = len(self._scale)
            tone = self._scale[note_index % scale_len] + 12 * (note_index // scale_len)
            tone += scale_note._accidental
            tones.append(tone)
        return tones

    def midi_notes(self):
        """
        Return list of midi notes.
        """
        scale_root_midi_name = str(self._scale_root) + str(self._octave)
        root_midi = note_util.name_to_midi(scale_root_midi_name)
        return [root_midi + tone for tone in self.tones()]

if __name__ == "__main__":
    scale = 'Cmaj'
    extensions = ['7', "13"]
    
    # ScaleNote(1), ScaleNote(3), ScaleNote(5), ScaleNote(7)
    print("Cmaj scale notes", FunChord(scale, 1, extensions=extensions).scale_notes())

    # tones = [0, 4, 7, 11]
    print("Cmaj tones", FunChord(scale, 1, extensions=extensions).tones())

    # midi = [36, 40, 43, 47]
    print("Cmaj midi notes", FunChord(scale, 1, extensions=extensions).midi_notes())
