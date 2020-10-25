import note_util
import numpy as np

class ScaleNote(object):
    """
    """
    # TODO: re-evaluate 0 vs 1 indexing for scale degrees
    MAX_SCALE_NOTE = 7
    def __init__(self, note):
        if type(note) is ScaleNote:
            self._note = note._note
            self._accidental = note._accidental
            return

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

        print("Note type is {} instead of int or str".format(type(note)))
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
        return "Scale Note({})".format(self.get_name())

    def __eq__(self, other) -> bool:
        if type(other) in (int, str):
            other = ScaleNote(other)
        elif type(other) != ScaleNote:
            raise TypeError
        # TODO: Handle sharps and flats note equality, including E#==F
        # # Handle C# == Db
        # if abs(self._note - other._note) == 1:
        #     smaller_note = self
        #     bigger_note = other

        #     if self._note > other._note:
        #         smaller_note = other
        #         bigger_note = self

        #     if smaller_note.accidental_str == '#' and bigger_note.accidental_str == 'b':
        #         return True
        return self._note == other._note and self._accidental == other._accidental

    def __hash__(self) -> int:
        # shitty hash but should work
        return self._accidental * 100 + self._note

    def get_tone(self) -> int:
        return self._note

    def get_name(self) -> str:
        return self.accidental_str() + str(self._note + 1)

    def is_root(self) -> bool:
        return self._note == 0

    def in_octave(self):
        """
        Return note within an octave ie. inverted to 0-7.
        """
        return self._note % (self.MAX_SCALE_NOTE + 1)

    def in_octave_scale_note(self):
        return ScaleNote(self.accidental_str() + str(1 + self.in_octave()))

    def accidental_str(self):
        return self.accidental_to_str(self._accidental)

    @staticmethod
    def accidental_to_str(accidental: int) -> str:
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
    def __init__(self, scale_name, degree, additions=[], omissions=[]):
        """
        scale_name (str): Name of the scale eg. Cmin, G#maj, etc.
        degree (int): scale degree of the chord's root note (root at 1)
        octave (int): Octave to play at
        omissions ([str|int]): Note to remove from the chord, relative to the chord eg. [1, '5']
        additions ([str|int]): Notes to add to the chord (such as extensions) relative to the chord eg. [2, 7, 'b13']
        """
        assert len(scale_name) >= 4, "Scale name '{}' should be formatted as (note letter)(accidental)(min|maj)".format(scale_name)

        # Take scale appart
        quality = scale_name[-3:]  # "min"|"maj"
        note = scale_name[:-3]  # note with accidental
        
        self._scale_root = note  # scale root note name
        self._scale = note_util.RELATIVE_KEY_DICT[quality]  # 7-note scale
        self.scale_quality = quality
        self._degree = ScaleNote(degree)  # scale degree of the chord's root note
        self._additions = set([ScaleNote(note) for note in additions])
        self._omissions = set([ScaleNote(note) for note in omissions])

    def __repr__(self):
        # eg. Ab Maj 7 b9 -3 (removed 3rd)
        scale_root_tone = note_util.name_to_number[self._scale_root]
        degree_interval = self._scale[self._degree._note]
        root_name = note_util.number_to_name[(scale_root_tone + degree_interval) % 12]

        extensions = [note.get_name for note in self._additions]
        omissions = ['-' + note.get_name for note in self._additions]
        return ' '.join([root_name, self.scale_quality] + extensions + omissions)

    def __eq__(self, other):
        # TODO: invert additions into octave, compare notes in 12 tones.
        pass

    def get_root_tone(self):
        return note_util.name_to_number[self._scale_root]

    def copy_additions(self):
        return self._additions.copy()

    def copy_omissions(self):
        return self._omissions.copy()

    def get_scale_name(self):
        return self._scale_root + self.scale_quality

    def is_root(self):
        return self._degree.is_root()

    def root_degree(self):
        return self._degree.in_octave_scale_note()

    def triad_notes(self):
        """
        Returns first three notes of the chord.
        """
        # NOTE: note inputs are 1-indexed
        triad = [ScaleNote(1 + (2 * n)) for n in range(0,3)]
        for omission in self._omissions:
            omitted_note = omission
            if omitted_note in triad:
                triad.remove(omitted_note)
        return triad

    def scale_notes(self):
        """
        Returns the notes in scale used.
        """
        chord_notes = self.triad_notes() + list(self._additions)
        
        for omission in self._omissions:
            omitted_note = omission
            if omitted_note in chord_notes:
                chord_notes.remove(omitted_note)

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

    def midi_notes(self, octave):
        """
        Return list of midi notes.
        """
        scale_root_midi_name = str(self._scale_root) + str(octave)
        root_midi = note_util.name_to_midi(scale_root_midi_name)
        return [root_midi + tone for tone in self.tones()]

if __name__ == "__main__":
    scale = 'Cmaj'
    extensions = ['7', "13"]
    
    # ScaleNote(1), ScaleNote(3), ScaleNote(5), ScaleNote(7)
    print("Cmaj scale notes", FunChord(scale, 1, additions=extensions).scale_notes())

    # tones = [0, 4, 7, 11]
    print("Cmaj tones", FunChord(scale, 1, additions=extensions).tones())

    # midi = [36, 40, 43, 47]
    print("Cmaj midi notes", FunChord(scale, 1, additions=extensions).midi_notes(1))
