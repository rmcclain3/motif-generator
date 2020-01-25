import math

class EventRegistry(object):
    Events = {}
    MetaEvents = {}
    
    def register_event(cls, event, bases):
        #print 'registering', event.__name__, bases
        if MetaEvent in bases or AbstractTextEvent in bases:
            assert event.metacommand not in cls.MetaEvents, \
                            "Event %s already registered" % event.name
            cls.MetaEvents[event.metacommand] = event
        elif (Event in bases) or (NoteEvent in bases):
            assert event.statusmsg not in cls.Events, \
                            "Event %s already registered" % event.name
            cls.Events[event.statusmsg] = event
        else:
            raise ValueError, ("Unknown bases class in event type: "+event.name
                               +str(bases))
    register_event = classmethod(register_event)


"""
EventMIDI : Concrete class used to describe MIDI Events.
Inherits from Event.
"""

class AbstractEvent(object):
    __slots__ = ['tick', 'data']
    name = "Generic MIDI Event"
    length = 0
    statusmsg = 0x0

    class __metaclass__(type):
        def __init__(cls, name, bases, dict):
            if name not in ['AbstractEvent', 'Event', 'MetaEvent',
                            'AbstractTextEvent', 'NoteEvent']:
                EventRegistry.register_event(cls, bases)

    def __init__(self, **kw):
        if type(self.length) == int:
            defdata = [0] * self.length
        else:
            defdata = []
        self.tick = 0
        self.data = defdata
        for key in kw:
            setattr(self, key, kw[key])

    def __cmp__(self, other):
        if self.tick < other.tick: return -1
        elif self.tick > other.tick: return 1
        return cmp(self.data, other.data)

    def __baserepr__(self, keys=[]):
        keys = ['tick'] + keys + ['data']
        body = []
        for key in keys:
            val = getattr(self, key)
            keyval = "%s=%s" % (key, val)
            body.append(keyval)
        body = str.join(', ', body)
        return "midi.%s(%s)" % (self.__class__.__name__, body)

    def __repr__(self):
        return self.__baserepr__()

class Event(AbstractEvent):
    __slots__ = ['channel']
    name = 'Event'

    def __init__(self, **kw):
        if 'channel' not in kw:
            kw = kw.copy()
            kw['channel'] = 0
            self.__kw = kw
        super(Event, self).__init__(**kw)

    def copy(self, **kw):
        _kw = {'channel': self.channel, 'tick': self.tick, 'data': self.data}
        _kw.update(kw)
        return self.__class__(**_kw) 

    def __cmp__(self, other):
        if self.tick < other.tick: return -1
        elif self.tick > other.tick: return 1
        return 0
        #if self.channel < other.channel: return -1
        #elif self.channel > other.channel: return 1
        #return cmp(self.data, other.data)

    def __repr__(self):
        return self.__baserepr__(['channel'])

    def is_event(cls, statusmsg):
        return (cls.statusmsg == (statusmsg & 0xF0))
    is_event = classmethod(is_event)


"""
MetaEvent is a special subclass of Event that is not meant to
be used as a concrete class.  It defines a subset of Events known
as the Meta  events.
"""
    
class MetaEvent(AbstractEvent):
    statusmsg = 0xFF
    metacommand = 0x0
    name = 'Meta Event'

    def is_event(cls, statusmsg):
        return (statusmsg == 0xFF)
    is_event = classmethod(is_event)


class AbstractTextEvent(MetaEvent):
    def get_text(self):
        return ''.join(map(chr, self.data))
    def set_text(self, t):
        self.data = [ord(x) for x in t]
    text = property(get_text, set_text)

    def __repr__(self):
        return self.__baserepr__(['text'])


"""
NoteEvent is a special subclass of Event that is not meant to
be used as a concrete class.  It defines the generalities of NoteOn
and NoteOff events.
"""

class NoteEvent(Event):
    __slots__ = ['pitch', 'velocity']
    length = 2

    def get_pitch(self):
        return self.data[0]
    def set_pitch(self, val):
        self.data[0] = val
    pitch = property(get_pitch, set_pitch)

    def get_velocity(self):
        return self.data[1]
    def set_velocity(self, val):
        self.data[1] = val
    velocity = property(get_velocity, set_velocity)

class NoteOnEvent(NoteEvent):
    statusmsg = 0x90
    name = 'Note On'

class NoteOffEvent(NoteEvent):
    statusmsg = 0x80
    name = 'Note Off'

class AfterTouchEvent(Event):
    statusmsg = 0xA0
    length = 2
    name = 'After Touch'

class ControlChangeEvent(Event):
    __slots__ = ['control', 'value']
    statusmsg = 0xB0
    length = 2
    name = 'Control Change'

    def set_control(self, val):
        self.data[0] = val
    def get_control(self):
        return self.data[0]
    control = property(get_control, set_control)

    def set_value(self, val):
        self.data[1] = val
    def get_value(self):
        return self.data[1]
    value = property(get_value, set_value)
    
class ProgramChangeEvent(Event):
    __slots__ = ['value']
    statusmsg = 0xC0
    length = 1
    name = 'Program Change'

    def set_value(self, val):
        self.data[0] = val
    def get_value(self):
        return self.data[0]
    value = property(get_value, set_value)

class ChannelAfterTouchEvent(Event):
    __slots__ = ['value']
    statusmsg = 0xD0
    length = 1
    name = 'Channel After Touch'

    def set_value(self, val):
        self.data[1] = val
    def get_value(self):
        return self.data[1]
    value = property(get_value, set_value)

class PitchWheelEvent(Event):
    __slots__ = ['pitch']
    statusmsg = 0xE0
    length = 2
    name = 'Pitch Wheel'

    def get_pitch(self):
        return ((self.data[1] << 7) | self.data[0]) - 0x2000
    def set_pitch(self, pitch):
        value = pitch + 0x2000
        self.data[0] = value & 0xFF
        self.data[1] = (value >> 7) & 0xFF
    pitch = property(get_pitch, set_pitch)

class SysexEvent(Event):
    statusmsg = 0xF0
    name = 'SysEx'
    length = 'varlen'

    def is_event(cls, statusmsg):
        return (cls.statusmsg == statusmsg)
    is_event = classmethod(is_event)

class SequenceNumberMetaEvent(MetaEvent):
    name = 'Sequence Number'
    metacommand = 0x00
    length = 2    

class TextMetaEvent(AbstractTextEvent):
    name = 'Text'
    metacommand = 0x01
    length = 'varlen'

class CopyrightMetaEvent(AbstractTextEvent):
    name = 'Copyright Notice'
    metacommand = 0x02
    length = 'varlen'

class TrackNameEvent(AbstractTextEvent):
    name = 'Track Name'
    metacommand = 0x03
    length = 'varlen'

class InstrumentNameEvent(AbstractTextEvent):
    name = 'Instrument Name'
    metacommand = 0x04
    length = 'varlen'

class LryricsEvent(AbstractTextEvent):
    name = 'Lyrics'
    metacommand = 0x05
    length = 'varlen'

class MarkerEvent(AbstractTextEvent):
    name = 'Marker'
    metacommand = 0x06
    length = 'varlen'

class CuePointEvent(AbstractTextEvent):
    name = 'Cue Point'
    metacommand = 0x07
    length = 'varlen'

class SomethingEvent(MetaEvent):
    name = 'Something'
    metacommand = 0x09

class ChannelPrefixEvent(MetaEvent):
    name = 'Channel Prefix'
    metacommand = 0x20
    length = 1

class PortEvent(MetaEvent):
    name = 'MIDI Port/Cable'
    metacommand = 0x21

class TrackLoopEvent(MetaEvent):
    name = 'Track Loop'
    metacommand = 0x2E

class EndOfTrackEvent(MetaEvent):
    name = 'End of Track'
    metacommand = 0x2F

class SetTempoEvent(MetaEvent):
    __slots__ = ['bpm', 'mpqn']
    name = 'Set Tempo'
    metacommand = 0x51
    length = 3

    def set_bpm(self, bpm):
        self.mpqn = int(float(6e7) / bpm)
    def get_bpm(self):
        return float(6e7) / self.mpqn
    bpm = property(get_bpm, set_bpm)

    def get_mpqn(self):
        assert(len(self.data) == 3)
        vals = [x << (16 - (8 * self.data.index(x))) for x in self.data]
        return sum(vals)
    def set_mpqn(self, val):
        self.data = [(val >> (16 - (8 * x)) & 0xFF) for x in range(3)]
    mpqn = property(get_mpqn, set_mpqn)

class SmpteOffsetEvent(MetaEvent):
    name = 'SMPTE Offset'
    metacommand = 0x54

class TimeSignatureEvent(MetaEvent):
    __slots__ = ['numerator', 'denominator', 'metronome', 'thirtyseconds']
    name = 'Time Signature'
    metacommand = 0x58
    length = 4

    def get_numerator(self):
        return self.data[0]
    def set_numerator(self, val):
        self.data[0] = val
    numerator = property(get_numerator, set_numerator)

    def get_denominator(self):
        return 2 ** self.data[1]
    def set_denominator(self, val):
        self.data[1] = int(math.sqrt(val))
    denominator = property(get_denominator, set_denominator)

    def get_metronome(self):
        return self.data[2]
    def set_metronome(self, val):
        self.data[2] = val
    metronome = property(get_metronome, set_metronome)

    def get_thirtyseconds(self):
        return self.data[3]
    def set_thirtyseconds(self, val):
        self.data[3] = val
    thirtyseconds = property(get_thirtyseconds, set_thirtyseconds)

# maps data[0] to Key name, base midi pitch
keyMap = { (249, 0): ('Cb', 11),
           (250, 0): ('Gb',  6),
           (251, 0): ('Db',  1),
           (252, 0): ('Ab',  8),
           (253, 0): ('Eb',  3),
           (254, 0):('Bb', 10),
           (255, 0): ('F',   5),
           (0, 0):   ('C',   0),
           (1, 0):   ('G',   7),
           (2, 0):   ('D',   2),
           (3, 0):   ('A',   9),
           (4, 0):   ('E',   4),
           (5, 0):   ('B',  11),
           (6, 0):   ('F#',  6),
           (7, 0):   ('C#',  1),
           (249, 1): ('Abm', 8),
           (250, 1): ('Ebm', 3),
           (251, 1): ('Bbm', 10),
           (252, 1): ('Fm',  5),
           (253, 1): ('Cm',  0),
           (254, 1): ('Gm',  7),
           (255, 1): ('Dm',  2),
           (0, 1):   ('Am',  9),
           (1, 1):   ('Em',  4),
           (2, 1):   ('Bm',  11),
           (3, 1):   ('F#m', 6),
           (4, 1):   ('C#m', 1),
           (5, 1):   ('G#m', 8),
           (6, 1):   ('D#m', 3),
           (7, 1):   ('A#m', 10)  }

class KeySignatureEvent(MetaEvent):
    name = 'Key Signature'
    metacommand = 0x59

    def get_key(self):
        return keyMap[(self.data[0], self.data[1])]
    keyData = property(get_key)

class SequencerSpecificEvent(MetaEvent):
    name = 'Sequencer Specific'
    metacommand = 0x7F
