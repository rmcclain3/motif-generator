#!/bin/env python

import sys, pprint, midifile, pdb

# Note in midifile, files get converted to 'patterns', hence the use of variable p below.

# convention midi pitch = pm, pitch class (c relative) = pc, pitch class (tonic relative) = pt

asciiDegreeNames = ['1', 'b2', '2', 'b3', '3', '4',
                    'b5', '5', 'b6', '6', 'b7', '7' ]

asciiDegreeStrings = ['1 ', 'b2', '2 ', 'b3', '3 ', '4 ',
                     'b5', '5 ', 'b6 ', '6 ', 'b7 ', '7 ' ]


asciiNoteNames = ['C', 'Db', 'D', 'Eb', 'E', 'F',
                  'Gb', 'G', 'Ab', 'A', 'Bb', 'B' ]

unicodeNoteNames = [u'C', u'D\u266d', u'D', u'E\u266d', u'E', u'F',
                    u'G\u266d', u'G', u'A\u266d', u'A', u'B\u266d', u'B' ]

unicodeDegreeNames = [u'1', u'\u266d2', u'2', u'\u266d3', u'3', u'4',
                      u'\u266f4', u'5', u'\u266d6', u'6', u'\u266d7', u'7' ]

unicodeSymbolNames = dict([('1', u'1'),
                           ('#1', u'\u266f1'), ('b2', u'\u266d2'), ('2', u'2'),
                           ('#2', u'\u266f2'), ('b3', u'\u266d3'), ('3', u'3'), ('4', u'4'),
                           ('#4', u'\u266f4'), ('b5', u'\u266d5'), ('5', u'5'),
                           ('#5', u'\u266f5'), ('b6', u'\u266d6'), ('6', u'6'),
                           ('#6', u'\u266f6'), ('b7', u'\u266d7'), ('7', u'7')])

keyToUnicodeMap = { 'Cb': u'C\u266d',
                    'Gb': u'G\u266d',
                    'Db': u'D\u266d',
                    'Ab': u'A\u266d',
                    'Eb': u'E\u266d',
                    'Bb': u'B\u266d',
                    'F': u'F',
                    'C': u'C',
                    'G': u'G',
                    'D': u'D',
                    'A': u'A',
                    'E': u'E',
                    'B': u'B',
                    'F#': u'F\u266f',
                    'C#': u'C\u266f',
                    'Abm': u'A\u266dm',
                    'Ebm': u'E\u266dm',
                    'Bbm': u'B\u266dm',
                    'Fm': u'Fm',
                    'Cm': u'Cm',
                    'Gm': u'Gm',
                    'Dm': u'Dm',
                    'Am': u'Am',
                    'Em': u'Em',
                    'Bm': u'Bm',
                    'F#m': u'F\u266fm',
                    'C#m': u'C\u266fm',
                    'G#m': u'G\u266fm',
                    'D#m': u'D\u266fm',
                    'A#m': u'A\u266fm' }

def dumpmidi(p):
    print ('Format %d, Resolution %d, Tracks %d'
           % (p.format, p.resolution, len(p)))

    # program change
    for t in p:
        print "***********"
        print pprint.pformat(t)

def findKeyData(p):
    for track in p:
        for e in track:
            if isinstance(e, midifile.KeySignatureEvent):
                key, base = e.keyData
                return (key, base)  # key name, pitch class number
    return (None, None)

def findUnicodeKey(p, minor=False):
    midiData = findKeyData(p)
    if not midiData[0]:
        return None
    if minor and midiData[1] != 1:
        midiData = (e.data[0], 1)
    return keyToUnicodeMap[midifile.keyMap[midiData][0]]

def noteCount(p):
    count = 0
    for track in p:
        for e in track:
            if isinstance(e, midifile.NoteOnEvent) and e.velocity > 0:
                count += 1
    return count

def getMidiNotePairs(p):
    # return midi note, duration of note pairs, as monophonic melody
    #pdb.set_trace()
    ticks = 0
    notes = []
    for track in p:
        onPitch = None
        for e in track:
            ticks += e.tick
            if isinstance(e, midifile.NoteEvent):
                # any note event ends any current note in this monophonic context
                # note: include rests in a note duration, need velocity > 0 to start
                # next note.
                if onPitch and e.velocity > 0 and ticks > 0:
                    notes.append( (onPitch, ticks ) )
                    onPitch = None
                if isinstance(e, midifile.NoteOnEvent) and e.velocity > 0:
                    onPitch = e.pitch
                    ticks = 0
        if onPitch and ticks > 0:
            notes.append( (onPitch, ticks ) )

        break; # only take first track
    return notes
    
def getPitchNumbers(p):
    numbers = []
    base = -1
    for track in p:
        for e in track:
            if isinstance(e, midifile.KeySignatureEvent):
                if base < 0:
                    key, base = e.keyData
            if isinstance(e, midifile.NoteOnEvent) and e.velocity > 0:
                if base < 0:
                    numbers.append((e.pitch - midifile.keyMap[ (0, 0) ]) % 12)
                else:
                    numbers.append((e.pitch - base) % 12)
    return numbers

def getAsciiNoteNames(pcs):
    notes = [ asciiNoteNames[pc % 12] for pc in pcs ]
    return notes

def getUnicodeNoteNames(pcs):
    notes = [ unicodeNoteNames[pc % 12] for pc in pcs ]
    return notes

def getAsciiNoteName(p):
    return asciiNoteNames[p]

def getUnicodeNoteName(p):
    return unicodeNoteNames[p]

def getAsciiDegreeNames(pcs, tonic = 0):
    notes = [ asciiDegreeNames[(pc + 12 - tonic) % 12] for pc in pcs ]
    return notes

def getAsciiDegreeString(pcs, tonic = 0):
    s = ' '.join([ asciiDegreeStrings[(pc + 12 - tonic) % 12] for pc in pcs ])
    return s

def getAsciiDegreeName(pc, tonic = 0):
    return asciiDegreeNames[(pc + 12 - tonic) % 12]

def convertTimebase(p, newTicksPerSec):
    ticks, ticksPerSec, mpqn = getTimeInfo(p)
    factor = float(newTicksPerSec) / float(ticksPerSec)
    for track in p:
        for e in track:
            e.tick = int(factor * e.tick)

def factorTicks(p, factor):
    for track in p:
        for e in track:
            e.tick = int(factor * e.tick)

def translate(p, delta):
    for track in p:
        for e in track:
            if isinstance(e, midifile.NoteEvent):
                e.set_pitch(e.pitch + delta)

def getUnicodeDegreeNames(pcs, tonic = 0):
    notes = [ unicodeDegreeNames[(pc + 12 - tonic) % 12] for pc in pcs ]
    return notes

def getUnicodeDegreeName(pc, tonic = 0):
    return unicodeDegreeNames[(pc + 12 - tonic) % 12]

def getTimeInfo(p):
    ticks = 0
    ticksPerSec = None
    mpqn = None
    for track in p:
        for e in track:
            ticks += e.tick
            if isinstance(e, midifile.SetTempoEvent):
                if ticksPerSec == None:
                    ticksPerSec = int(p.resolution / 1e-6 / e.mpqn)
                    mpqn = e.mpqn
    return ticks, ticksPerSec, mpqn

if __name__ == '__main__':
    options = ['help']

    def usage():
        print "Options:"
        for word in options:
            print "  ", word
        sys.exit(0)
        
    import getopt
    def main():
        opts, pargs = getopt.getopt(sys.argv[1:], '', options)
        for opt, val in opts:
            if opt == '--help':
                usage()

        p = midifile.FileReader().read(open(pargs[0], "rb"))
        dumpmidi(p)
        
    
    main()
