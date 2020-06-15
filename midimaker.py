import midifile, midi

frameRate = 44100

# Key agnostic midi file maker.
# Pitch numbering is always wrt a tonic which will also set the current register for the piece.
# Because of overlapping notes, the client will have to directly increase time.
# Tempo and tonic can be changed troughout the piece.
# Has no concept of meter, just a quarter note beat.

Rest = -9999

def flushCmp(x, y):
    val = cmp(x.tick, y.tick)
    if val:
        return val
    if isinstance(x, midifile.NoteOffEvent) and isinstance(y, midifile.NoteOnEvent):
        return -1;
    if isinstance(y, midifile.NoteOffEvent) and isinstance(x, midifile.NoteOnEvent):
        return 1;
    if x.data[0] == y.data[0]:
        raise Exception, 'Unable to sort same notes: %s %s' % (str(x), str(y))
    return cmp(x.data[0], x.data[1])

valueToTicksFactor = dict([('w', (4,1)), ('h', (2,1) ), ('q', (1,1)),
                           ('e', (1,2)), ('s', (1,4)), ('t', (1/32)),
                           ('Q', (2,3)), ('E', (1,3))])

class Maker(object):
    def __init__(self, tonic, bpm, debug = False):
        self.debug = debug
        self.resolution = 96  # ticks per quarter note
        # final sorted midi events, where ticks are delta from the previous event
        self.pattern = midifile.Pattern(resolution=self.resolution)
        self.track = midifile.Track()
        self.pattern.append(self.track)
        # added time becomes a delta time of the next event
        self.currentDelta = 0
        # if a note is being held, then a NoteOffEvent gets automatically inserted, so keep
        # track of held notes
        self.heldNotes = set()
        # Since when you want to add rest, you want to advance a future event, save the amount
        # of skip time until the next event is added. Note: use it when adding to track (not queue)
        self.skipTicks = 0
        self.position = 0
        self.setTonic(tonic)
        self.setTempo(bpm)
        self.queue = []

    def addTime(self, duration):
        pass

    def setTempo(self, bpm):
        self.bpm = bpm
        e = midifile.SetTempoEvent(tick=0)
        e.set_bpm(self.bpm)
        self.track.append(e)

    def setTonic(self, tonic):
        self.tonic = tonic
        
    def skipSeconds(self, deltaSec):
        beats = deltaSec * self.bpm / 60.
        ticks = int(self.resolution * beats + .5)
        self.skipTicks += ticks
        self.position += ticks

    def skipBeats(self, beats):
        ticks = int(self.resolution * beats + .5)
        self.skipTicks += ticks
        self.position += ticks

    def skipValue(self, value):
        n,d = valueToTicksFactor[value]
        ticks = n * self.resolution / d
        self.skipTicks += ticks
        self.position += ticks

    def addMotif(self, motif, value='q'):
        ''' original version which just does monophonic quarter notes '''
        velocity = 80
        for pitch in motif:
            if pitch == 'r':
                self.addRest(value)
            else:
                self.addNote(pitch, velocity, value)
        
    def addQuarterNote(self, pitch, velocity):
        self.addNote(self, pitch, velocity, 'q')

    def addNote(self, pitch, velocity, value):
        n,d = valueToTicksFactor[value]
        ticks = n * self.resolution / d
        note = self.tonic + pitch
        self.track.append(midifile.NoteOnEvent(tick=self.skipTicks, pitch=note, velocity=velocity))
        self.skipTicks = 0
        self.track.append(midifile.NoteOffEvent(tick=ticks, pitch=note, velocity=velocity))
        self.position += ticks

    def addRest(self, value):
        n,d = valueToTicksFactor[value]
        ticks = n * self.resolution / d
        self.skipTicks += ticks
        self.position += ticks

    def valueToTicks(self, value):
        n,d = valueToTicksFactor[value]
        ticks = n * self.resolution / d
        return ticks
    
    def enqueue(self, pitch, velocity, startTick, endTick):
        # skip rests
        if pitch != Rest:
            midipitch = self.tonic + pitch
            self.queue.append(midifile.NoteOnEvent(tick=startTick, pitch=midipitch, velocity=velocity))
            #print self.queue[-1]
            self.queue.append(midifile.NoteOffEvent(tick=endTick, pitch=midipitch, velocity=velocity))
            #print self.queue[-1]

    def enqueueMotif(self, motif, value='q'):
        velocity = 80
        currTicks = 0
        inChord = False
        holdTicks = self.valueToTicks(value)
        for pitch in motif:
            if pitch == 'r':
                currTicks += holdTicks
            elif pitch == '=':
                inChord = not inChord
            else:
                self.enqueue(pitch, velocity, currTicks, currTicks + holdTicks)
                if not inChord:
                    currTicks += holdTicks

    def flush(self):
        self.queue.sort(cmp=flushCmp)
        running_tick = 0
        for event in self.queue:
            event.tick -= running_tick
            running_tick += event.tick
            self.position += event.tick
        # apply skip ticks to the first event added to the track
        if self.skipTicks > 0:
            self.queue[0].tick = self.skipTicks
            self.skipTicks = 0
        self.queue = [ x for x in self.queue if x.pitch >= 0 ]
        self.track.extend(self.queue)
        self.queue = []
        
    def endTrack(self):
        self.track.append(midifile.EndOfTrackEvent(tick=1))

    def getTime(self):
        secPerTick = (60.0 / self.bpm) / self.resolution
        framesPerTick = secPerTick * frameRate
        t = self.position * secPerTick
        frames = int(self.position * framesPerTick)
        return (t, frames)
        
    def write(self, fname):
        midifile.write_midifile(fname, self.pattern)

    def dump(self):
        midi.dumpmidi(self.pattern)

