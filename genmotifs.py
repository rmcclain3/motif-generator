#!/usr/bin/env python

import sys, os, os.path, random, time, codecs, pdb
import midimaker, midi

Petrucci = '../Petrucci'

noteNames = ['1', 'b2', '2', 'b3', '3', '4',
             '#4', '5', 'b6', '6', 'b7', '7']

keyToBase = dict([('c', 0), ('c#', 1), ('db', 1), ('d', 2), ('d#', 3), ('eb', 3),
                   ('e', 4), ('f', 5), ('f#', 6), ('gb', 6), ('g', 7), ('g#', 8),
                   ('ab', 8), ('a', 9), ('a#', 10), ('bb', 10), ('b', 11)])

pitchToSymbol = noteNames
symbolToPitch = dict([(s,p) for p,s in enumerate(pitchToSymbol)])
lf = u'\240a'

def makeMustSet(symbols):
    return set([symbolToPitch[symbol] for symbol in symbols])

class Scale(object):
    def __init__(self):
        # maybe should change this to pitchToDegree for clarity
        self.pitchSet = set(self.stepToPc.values())
        self.pcToStep = dict()
        self.pcToStepString = dict()
        self.stepToNote = dict()
        self.top = 400
        self.minNotes = 4
        self.maxNotes = 12
        self.mustFixPosition = None
        self.mustPitches = set()
        self.minPcs = 0
        self.nChromatics = 0
        self.cue = [0, 7, 12]
        self.moniker = None
        for step, pc in self.stepToPc.items():
            self.pcToStep[pc] = step
            self.pcToStepString[pc] = '%d' % (step,)

    def getPitches(self):
        pitches = self.pcToStep.keys()
        pitches.sort()
        return pitches
    
    def mapNgramToScale(self, nGram, startPitch,
                         conjunct, outside, unisons, minPcs,
                        mustFixPosition, begOrEndSet, nChromatics):
        nChromaticsSoFar = 0
        assert (startPitch % 12) in self.pcToStep, 'illegal start pitch'
        if (conjunct != None
             and (max(abs(max(nGram)), abs(min(nGram)))) > conjunct):
            return None
        if outside == None:
            outside = 100
        pitch = startPitch
        pitches = [startPitch,]
        zeroSteps = 0
        for step in nGram:
            if step == 0:
                zeroSteps += 1
            pitch = (pitch + step)
            if pitch % 12 not in self.pcToStep:
                nChromaticsSoFar += 1
                if nChromaticsSoFar > nChromatics:
                    return None
            pitches.append(pitch)
            
        if unisons != None and zeroSteps > unisons:
            return None
        if nChromaticsSoFar != nChromatics:
            return None

        pitchSet = set([x % 12 for x in pitches])
        if len(pitchSet) < minPcs:
            return None
        if begOrEndSet and not (pitches[0] in begOrEndSet or pitches[-1] in begOrEndSet):
            return None
        
        if mustFixPosition:
            for sp in self.pcToStep.keys():
                if sp == startPitch % 12:  # only check other start pitches
                    continue
                okay = False
                pitch = sp
                for step in nGram:
                    pitch = (pitch + step)
                    if pitch % 12 not in self.pcToStep:
                        okay = True       # ngram out of scale from that start pitch
                        break
                if not okay:              # the ngram never stepped out of scale from new start pitch
                    break
                okay = True               # so far so good
            if not okay:                  # were we good all the way?
                return None
        return pitches

    def stringifyMotif(self, motif):
        degrees = []
        for x in motif:
            if x == '=':
                continue
            if x == 'r':
                degrees.append('_')
            else:
                p = x % 12
                if p in self.pcToStepString:
                    degrees.append(self.pcToStepString[p])
                else:
                    degrees.append('x')
        return ''.join(degrees)

class Diatonic(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,2), (3,4), (4,5), (5,7), (6,9), (7,11)])
        super(Diatonic, self).__init__()
        self.mustPitches = makeMustSet(['1', '3', '4', '7'])
        self.cue = [0, 4, 7, 12]        
        self.minPcs = 5
        self.top = 500
        self.moniker = 'io'
        
Ionian = Diatonic
        
class Lydian(Scale):
    # lacking the dominant pitch, tonic is hard to perceive
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,2), (3,4), (4,6), (5,7), (6,9), (7,11)])
        super(Lydian, self).__init__()
        self.cue = [0, 4, 7, 12]        
        self.mustPitches = makeMustSet(['1', '3', '#4', '7'])
        self.moniker = 'ly'

class Mixolydian(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,2), (3,4), (4,5), (5,7), (6,9), (7,10)])
        super(Mixolydian, self).__init__()
        self.cue = [0, 4, 7, 12]        
        self.mustPitches = makeMustSet(['1', '3', '4', '6', 'b7'])
        self.moniker = 'mx'

class Aeolian(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,2), (3,3), (4,5), (5,7), (6,8), (7,10)])
        self.cue = [0, 3, 7, 12]        
        super(Aeolian, self).__init__()
        self.cue = [0, 3, 7, 12]        
        self.mustPitches = makeMustSet(['1', '2', 'b3', '5', 'b6'])
        self.moniker = 'ae'

class Dorian(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,2), (3,3), (4,5), (5,7), (6,9), (7,10)])
        super(Dorian, self).__init__()
        self.cue = [0, 3, 7, 12]        
        self.mustPitches = makeMustSet(['1', '2', 'b3', '6', 'b7'])
        self.moniker = 'dr'        

class Phrygian(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,1), (3,3), (4,5), (5,7), (6,8), (7,10)])
        super(Phrygian, self).__init__()
        self.cue = [0, 3, 7, 12]        
        self.mustPitches = makeMustSet(['1', 'b2', 'b3', '5', 'b6'])
        self.moniker = 'ph'

class MelodicMinor(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,2), (3,3), (4,5), (5,7), (6,9), (7,11)])
        super(MelodicMinor, self).__init__()
        self.cue = [0, 3, 7, 12]        
        self.mustPitches = makeMustSet(['1', '2', 'b3', '6', '7'])
        self.moniker = 'mm'

class HarmonicMinor(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,2), (3,3), (4,5), (5,7), (6,8), (7,11)])
        super(HarmonicMinor, self).__init__()
        self.cue = [0, 3, 7, 12]        
        self.mustPitches = makeMustSet(['1', '2', 'b3', 'b6', '7'])
        self.moniker = 'hm'

class MajorChromatics(Diatonic):
    def __init__(self):
        super(MajorChromatics, self).__init__()
        self.cue = [0, 4, 7, 12]        
        self.nChromatics = 1
        self.top = 800
        self.moniker = 'chj'
    
class MinorChromatics(Aeolian):
    def __init__(self):
        super(MinorChromatics, self).__init__()
        self.cue = [0, 3, 7, 12]        
        self.nChromatics = 1
        self.minPcs = 6
        self.top = 500
        self.moniker = 'chn'
    
class AllMinor(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,2), (3,3), (4,5), (5,7), (6,8), (7,9), (8,10), (9,11)])
        super(AllMinor, self).__init__()
        self.cue = [0, 3, 7, 12]        
        self.mustPitches = set()
        self.moniker = 'mn'

class Chromatic(Scale):
    def __init__(self):
        self.stepToPc = dict([ (x+1,x) for x in xrange(12) ])
        super(Chromatic, self).__init__()
        self.pcToStepString = dict([(x, '%d' % (x,)) for x in xrange(0, 10)])
        self.pcToStepString[10] = 't'
        self.pcToStepString[11] = 'e'
        self.moniker = 'cr'
        
# below unused so far
class Acoustic(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,2), (3,3), (4,5), (5,7), (6,9), (7,11)])
        super(Acoustic, self).__init__()
        self.mustPitches = set()
        self.moniker = 'ac'
        
class WholeTone(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,2), (3,4), (4,6), (5,8), (6,10)])
        super(WholeTone, self).__init__()
        self.mustPitches = set()
        self.moniker = 'wt'

class Octatonic(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,1), (3,3), (4,4),
                              (5,6), (6,7), (7,9), (8,10)])
        super(Octatonic, self).__init__()
        self.moniker = 'oct'

class HarmonicMajor(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,2), (3,4), (4,5), (5,7), (6,8), (7,11)])
        super(HarmonicMajor, self).__init__()

class Hexatonic(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,3), (3,4), (4,5), (5,8), (7,11)])
        super(Hexatonic, self).__init__()

class Pentatonic(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,2), (3,4), (4,7), (5,9)])
        super(Pentatonic, self).__init__()

class MinorPentatonic(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,3), (3,5), (4,7), (5,10)])
        super(MinorPentatonic, self).__init__()

class Blues(Scale):
    def __init__(self):
        self.stepToPc = dict([(1,0), (2,3), (3,5), (4,6), (5,7), (6,10)])
        super(Blues, self).__init__()
        self.minPcs = 6
class NgramAnalyzer(object):
    def __init__(self):
        pass

intervalName = dict([(i, ('U', 'm2', 'M2', 'm3', 'M3', 'P4', 'T', 'P5', 'm6', 'M6', 'm7', 'M7')[i]) for i in xrange(12)])
    
def havePitches(pitchSequence, pitchSet, mustSet, nChromatics, scaleSet):
    if not mustSet:
        return True
    if nChromatics == 0:
        return mustSet.issubset(pitchSet)
    
    # mustSet must precede any chromatics
    haveSet = set()
    for p in pitchSequence:
        if p not in scaleSet:
            return False
        haveSet.add(p)
        if mustSet.issubset(haveSet):
            return True
    raise Exception, 'Should have hit a chromatic note'

def avoidDouble(motif):
    n = len(motif)
    for i in xrange(n-3):
        for j in xrange(i+2, n-1):
            if motif[i] == motif[j] and motif[i+1] == motif[j+1]:
                return False
    return True

def avoidSets(pitchSet, poisonSets):
    for poisonSet in poisonSets:
        if poisonSet.issubset(pitchSet):
            return False
    return True

def avoidSequences(pitches, poisonSequences):
    for poisonSequence in poisonSequences:
        nNotes = len(poisonSequence)
        for i in xrange(0, len(pitches) - nNotes + 1):
            if pitches[i:i+nNotes] == poisonSequence:
                return False
    return True

class Tone(object):
    def __init__(self, symbol, scales):
        self.symbol = symbol
        self.pitch = symbolToPitch[self.symbol]
        self.scales = scales # just the ones to train on for this pitch

def encodeMelody(mel):
    uChars = []
    for mp in mel:
        if mp == '=':
            continue
        if mp == 'r':
            uChars.append(u' ')
        else:
            pc = mp % 12
            uChars.append(midi.getUnicodeDegreeName(pc))
    return u''.join(uChars)

def getTopMotifs(scale, nTop, minGrams, maxGrams, cue, startPitch,
                 conjunct, outside, unisons, minPcs, mustFix, mustSet,
                 nChromatics, begOrEndSet, poisonSets, poisonSequences, fileBase):
    tops = []
    for i in xrange(minGrams, maxGrams+1):
        if i == 14:
            continue
        name = os.path.abspath(Petrucci + "/ngram%d.csv" % (i,))

        f = open(name)
        line = f.readline()
        tried = 0
        kept = 0
        count = 99999999
        while line:
            line = line.rstrip()
            ng, year, count = line.split('\t')
            count = int(count)
            ng = ng.split()
            ng = map(int, ng)
            ng = tuple(ng)
            pitches = scale.mapNgramToScale(ng, startPitch,
                                            conjunct, outside, unisons, minPcs,
                                            mustFix, begOrEndSet, nChromatics)
            tried += 1
            if pitches:
                pitchSequence = [x % 12 for x in pitches] 
                pitchSet = set(pitchSequence)
                if (avoidSets(pitchSet, poisonSets)
                    and havePitches(pitchSequence, pitchSet, mustSet, nChromatics, scale.pitchSet)
                    and avoidDouble(pitches)
                    and avoidSequences(pitchSequence, poisonSequences)):

                    #pdb.set_trace()
                    if cue:
                        pitches = cue + ['r',] + pitches
                    tops.append((count, pitches, scale, fileBase, None))
                    kept += 1
                    if kept >= nTop:
                        break
            line = f.readline()
        f.close()
        #print "%d notes, %d / %d" % (i+1, kept, tried)
    tops.sort(reverse=True)
    tops = tops[:nTop]
    return tops


def outputMotifsToFile(lfp, motifs, maker, doMarker, doDump, doPdb, nKeys, base0, settleTime, oneIn, sleepTime, scale, scaleClassname):
    #pdb.set_trace()
    maker.skipSeconds(2.0)
    if doMarker:
        startTime, startFrame = maker.getTime()
        maker.addMotif([0,])
        stopTime, stopFrame = maker.getTime()
        lfp.write(u'%s %d %.3f %.3f %d %d\n' % (u'marker', 0, startTime, stopTime, startFrame, stopFrame))
        maker.skipSeconds(settleTime)
        doMarker = False

    if doDump:
        for m in motifs:
            print m
        sys.exit()

    if doPdb:
        #pdb.set_trace()
        pass
    for iKey in xrange(nKeys):
        key = base0 + iKey
        maker.setTonic(key)
        keyOctave = ((key -60) + 4 * 12) / 12
        keyName = midi.getAsciiNoteName(key % 12).lower()

        nMotifs = len(motifs)
        for index, tup in enumerate(motifs):
            if (iKey + index) % oneIn == 0:
                count, motif, scale, motifString, fileBase, footnote = tup
                startTime, startFrame = maker.getTime()
                #pdb.set_trace()
                maker.enqueueMotif(motif)
                maker.flush()
                maker.skipSeconds(sleepTime)
                stopTime, stopFrame = maker.getTime()
                logline = []
                name = "%s_%s_%s%d_%s" % (fileBase, scale.moniker, keyName, keyOctave, motifString)
                logline.append(u'%s %d %.3f %.3f %d %d ' % (name, 0, startTime, stopTime, startFrame, stopFrame))
                emelody = encodeMelody(motif)
                emelody = emelody + unicode(' ' + scaleClassname)
                if footnote:
                    emelody = emelody + unicode(' ' + footnote)
                logline.append(u' Melody: ' + emelody)
                lfp.write(u'%s\n' % (lf.join(logline),))
                maker.skipSeconds(settleTime)                        
    
if __name__ == '__main__':
    options = ['help', 'pdb', 'petrucci=', 'scales=', 'top=', 'tempo=', 'sleep=',
               'key=', 'keyOctave=', 'nKeys=', 'oneIn=',
               'unisons=', 'conjunct=', 'minNotes=', 'maxNotes=', 'minPcs=',
               'dump', 'starts=', 'must=', 'begorends=', 'fix',
               'chromatics=', 'cue=',
               'base=', 
               'poisonSets=', 'poisonSequences=',
               'dyads', 'descending', 'harmonic',
   ]

    def usage():
        print "Options:"
        for word in options:
            print "  ", word
        sys.exit(0)
        
    import getopt
    def main():
        top = 0
        tempo = 60
        scaleClassnames = ['Diatonic', 'Mixolydian', 'MajorChromatics',
                           'Aeolian', 'Dorian', 'Phrygian', 'HarmonicMinor', 'MelodicMinor', 'MinorChromatics']
        key = keyToBase['c']
        keyOctave = 3
        conjunct = 11
        outside = None
        unisons = 0
        minNotes = 0
        maxNotes = 0
        nKeys = 12
        oneIn = 12
        minPcs = 0
        doDump = False
        startPitches = None
        cue = None
        mustSet = None
        begOrEndSet = None
        poisonSets = []
        poisonSequences = []
        nChromatics = 0
        theFileBase = None
        sleepTime = 2.0  # time padded to the end of motif in .wav sample
        mustFixPosition = None
        global running, selectAnother, pause, Petrucci
        selectAnother = False
        running = True
        pause = False
        doPdb = False
        doDescending = False
        doHarmonic = False

        #pdb.set_trace()
        opts, pargs = getopt.getopt(sys.argv[1:], '', options)
        for opt, val in opts:
            if opt == '--help':
                usage()
            elif opt == '--pdb':
                doPdb = True
            elif opt == '--petrucci':
                Petrucci = val
            elif opt == '--scales':
                if ',' in val:
                    scaleClassnames = val.split(',')
                else:
                    scaleClassnames = [val, ]
            elif opt == '--top':
                top = int(val)
            elif opt == '--tempo':
                tempo = int(val)
            elif opt == '--key':
                key = keyToBase[val.lower()]
            elif opt == '--keyOctave':
                keyOctave = int(val)
            elif opt == '--nKeys':
                nKeys = int(val) # number of keys to chromatically step up when generating
            elif opt == '--oneIn':
                oneIn = int(val)
            elif opt == '--conjunct':
                conjunct = int(val)
            elif opt == '--minNotes':
                minNotes = int(val)
            elif opt == '--maxNotes':
                maxNotes = int(val)
            elif opt == '--unisons':
                unisons = int(val)
            elif opt == '--minPcs':
                minPcs = int(val)
            elif opt == '--dump':
                doDump = True
            elif opt == '--starts':
                startPitches = val
            elif opt == '--base':
                theFileBase = val
            elif opt == '--must':
                mustSet = set(map(int, val.split(',')))
            elif opt == '--begorends':
                begOrEndSet = set(map(int, val.split(',')))
            elif opt == '--chromatics':
                nChromatics = int(val)
            elif opt == '--cue':
                cue = map(int, val.split(','))
            elif opt == '--poisonSets':
                poisonStrings = val.split(':')
                poisonSets = []
                for ps in poisonStrings:
                    poisonSets.append(set(map(int, ps.split(','))))
            elif opt == '--poisonSequences':
                poisonStrings = val.split(':')
                poisonSequences = []
                for ps in poisonStrings:
                    poisonSequences.append(map(int, ps.split(',')))
            elif opt == '--fix':
                mustFixPosition = True
            elif opt == '--sleep':
                sleepTime = float(val)
            elif opt == '--dyads':
                scaleClassnames = ['Dyad', ]
                theFileBase = 'dya'
                cue = [0, 7, 12]
                oneIn = 4
            elif opt == '--descending':
                doDescending = True
                theFileBase = 'dyd'
            elif opt == '--harmonic':
                doHarmonic = True
                theFileBase = 'dyh'
            else:
                print opt,val
                raise Exception, '%s %s?' % (opt,val)

        if len(pargs) > 0:
            raise Exception, '%s?' % [str(pargs),]
            
        # set tonic for first scale (though this gets set again anyway)
        base0 = 60 + key + (keyOctave - 4) * 12
        maker = midimaker.Maker(base0, tempo)

        # command line overrides defaults
        if theFileBase == None:
            theFileBase = 'gm'

        lfp = codecs.open(theFileBase + '.log', 'w', 'utf_16')
            
        doMarker = True

        motifs = []

        # I doubt that nChromatics > 0 is compatible with mustFixPosition
        if nChromatics > 0 and mustFixPosition:
            raise Exception, 'nChromatics > 0 and mustFixPosition'

        for scaleClassname in scaleClassnames:
            if scaleClassname == 'Dyad':
                if doPdb:
                    pdb.set_trace()
                scale = Chromatic()
                lowTonic = 0
                highTonic = 12
                for interval in xrange(1, 12):
                    iName = intervalName[interval]
                    fileBase = '%s_%s' % (theFileBase, iName)
                    footnote = iName
                    shortHalf = interval / 2
                    longHalf = interval - shortHalf
                    for i in xrange(lowTonic - shortHalf, highTonic - longHalf + 1):
                        j = i + interval
                        if doDescending:
                            pitches = [j, i]
                        elif doHarmonic:
                            pitches = [ '=', i, j, '=' ] + ['r',] + [ '=', i, j, '=' ]
                        else:
                            pitches = [i, j]
                        if cue:
                            pitches = cue + ['r',] + pitches
                        motifs.append( (1, pitches, scale, fileBase, footnote) )
            else:
                scale = globals()[scaleClassname]()
                if doPdb:
                    pdb.set_trace()
                if mustSet == None:
                    scaleMustSet = scale.mustPitches
                else:
                    scaleMustSet = mustSet
                if startPitches:
                    scaleStartPitches = map(int, startPitches.split(','))
                else:
                    scaleStartPitches = scale.getPitches()
                if mustFixPosition == None:
                    scaleMustFixPosition = scale.mustFixPosition
                else:
                    scaleMustFixPosition = mustFixPosition
                if nChromatics == 0:
                    scaleNChromatics = scale.nChromatics
                else:
                    scaleNChromatics = nChromatics
                if minNotes == 0:
                    minGrams = scale.minNotes - 1
                else:
                    minGrams = minNotes - 1
                if maxNotes == 0:
                    maxGrams = scale.maxNotes - 1
                else:
                    maxGrams = maxNotes - 1
                if minPcs == 0:
                    scaleMinPcs = scale.minPcs
                else:
                    scaleMinPcs = minPcs
                if cue == None:
                    scaleCue = scale.cue
                else:
                    scaleCue = cue
                if top == 0:
                    scaleTop = scale.top
                else:
                    scaleTop = top

                #pdb.set_trace()
                for startPitch in scaleStartPitches:
                    tops = getTopMotifs(scale, scaleTop, minGrams, maxGrams, scaleCue, startPitch,
                                        conjunct, outside, unisons,
                                        scaleMinPcs, scaleMustFixPosition, scaleMustSet,
                                        scaleNChromatics, begOrEndSet, poisonSets, poisonSequences, theFileBase)
                    motifs.extend(tops)

                #pdb.set_trace()
                motifs.sort(reverse=True)
                motifs = motifs[:scaleTop]

            #pdb.set_trace()                
            # sort by filename?
            countSorted = motifs
            motifs = []
            motifStringSet = set()
            for count, motif, scale, fileBase, footNote in countSorted:
                motifString = scale.stringifyMotif(motif)
                if motifString in motifStringSet:
                    nameBase = motifString + '_'
                    for i in xrange(15):
                        motifString = nameBase+(chr(ord('a')+i))
                        if motifString not in motifStringSet:
                            break
                if motifString in motifStringSet:
                    continue
                motifStringSet.add(motifString)
                motifs.append( (count, motif, scale, motifString, fileBase, footNote) )

            settleTime = 2.0 # time padded between samples
            outputMotifsToFile(lfp, motifs, maker, doMarker, doDump, doPdb, nKeys, base0, settleTime, oneIn, sleepTime, scale, scaleClassname)

        # put a marker at the end to force reaper to continue past the last sample
        maker.addMotif([0,])


        lfp.close()
        #pdb.set_trace()
        maker.endTrack()
        maker.write(theFileBase + '.mid')
        
main()
