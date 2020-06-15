#!/bin/env python

import sys, pdb, wave, struct, codecs, os, stat, math
import wav64

frameRate = 44100.

lf = u'\240a'

def timeString(frameNumber):
    x = frameNumber / frameRate
    h = int(x / 3600)
    x -= h * 3600
    m = int(x / 60)
    s = x - m * 60
    return "%d:%d:%06.3f" % (h, m, s)

if __name__ == '__main__':
    options = ['help', 'verify', 'threshold=', 'taper', 'subdirs=', 'raw']

    def usage():
        print "clipmotifs.py <basename>"
        print "Options:"
        for word in options:
            print "  ", word
        sys.exit(0)
        
    import getopt
    def main():
        leadTime = .25
        leadFrames = int(leadTime * frameRate)
        startTime = 0.0
        threshold = 150
        taper = True
        taperTime = .25
        subdirs = 1
        nTaperFrames = int(taperTime * frameRate)
        verify = False
        doAgc = True
        opts, pargs = getopt.getopt(sys.argv[1:], '', options)
        for opt, val in opts:
            if opt == '--help':
                usage()
            elif opt == '--verify':
                verify = True
            elif opt == '--threshold':
                threshold = int(val)
            elif opt == '--taper':
                taper = True
            elif opt == '--subdirs':
                subdirs = int(val);
            elif opt == '--raw':
                doAgc = False

        if len(pargs) < 1:
            usage()

        bname = pargs[0]
        lname = bname + '.log'
        wavdir = bname + '_wav'
        mp3dir = bname + '_mp3'
        try:
            os.mkdir(wavdir, 0755)
        except:
            pass
        sfileName = bname + '_mp3.sh'
        sfile = open(sfileName, 'w')
        sfile.write('#!/bin/sh\n')
        sfile.write('mkdir ' + mp3dir + '\n')

        #pdb.set_trace()
        currSeg = -1
        currSubdir = None
        wvi = None
        for line in codecs.open(lname, 'r', 'utf_16'):
            line = line.strip()
            if line.find(lf):
                line = line.split(lf, 1)[0]
            mname, iSeg, start, stop, startFrame, endFrame = line.strip().split()
            if subdirs and mname != 'marker':
                subdir = '_'.join(mname.split('_')[0:subdirs])
                if subdir != currSubdir:
                    try:
                        os.mkdir(wavdir + '/' + subdir, 0755)
                        sfile.write('mkdir ' + mp3dir + '/' + subdir + '\n')
                        currSubdir = subdir
                    except:
                        pass
                mname = subdir + '/' + mname
            iSeg = int(iSeg)
            startFrame0 = int(startFrame)
            endFrame = int(endFrame)
            startFrame = startFrame0
            if iSeg != currSeg:
                if wvi:
                    wvi.close()

                # Before I figured out wav64, I was painfully generating multiple midi-files.
                # At this point, iSeg is always 0
                currSeg = iSeg
                if currSeg == 0:
                    wname = '%s.wav' % (bname,)
                else:
                    wname = '%s%d.wav' % (bname, currSeg)
                    
                wvi = wav64.Wave64()
                #pdb.set_trace()
                wvi.open(wname)
                params = list(wvi.getparams())
                print params
                if params[1] == 2:
                    format = '<hh'
                elif params[1] == 4:
                    format = '<xxhxxh'
                else:
                    raise 'bad header'

                currFrame = -1

                # find marker
                #pdb.set_trace()
                recents = [0]*5
                foundMarker = False
                for i in xrange(int(frameRate * 15 * 60)):
                    frame = wvi.readframes(1)
                    currFrame += 1
                    x = struct.unpack(format, frame)
                    x = max(map(abs, x))

                    recents[i % 5] = x
                    # 3 samples in 5 above threshold
                    y = sum([int(s > threshold ) for s in recents])
                    #print repr(frame), x
                    if y >= 3:
                        foundMarker = True
                        break
                if not foundMarker:
                    raise 'No marker detected'
                doMarkerAdjust = True
                print 'Found marker at %s, opening %s' % (timeString(currFrame), lname)

                markerFrame = currFrame - 5
                zeroFrame = currFrame
                print 'Initial zeroFrame = ', zeroFrame

                if verify:
                    leadTime = .2
                    leadFrames = int(leadTime * frameRate)
                    sampleTime = .1
                    nSampleFrames = int(sampleTime * frameRate)
                    if params[1] == 2:
                        sampleFormat = '<' + 'hh' * nSampleFrames
                    else:
                        sampleFormat = '<' + 'xxhxxh' * nSampleFrames

            if mname == 'marker':
                if doMarkerAdjust:
                    # update zero frame based on marker time
                    markerTime = float(start)
                    zeroFrame -= int(markerTime * frameRate)
                    print 'Skipping marker, adjusting zeroFrame =', zeroFrame
                    doMarkerAdjust = False
                else:
                    print 'Skipping extra marker, no adjusting zeroFrame'
                    
            else:
                #pdb.set_trace()
                start = float(start) - leadTime 
                stop = float(stop) - leadTime
                startFrame -= (leadFrames + zeroFrame)
                endFrame -= (leadFrames + zeroFrame)
                if not verify:
                    nFrames = endFrame - startFrame
                    fname = mname + '.wav'
                    mp3name = mname + '.mp3'
                    print 'Writing %d frames to %s (%s -> %s)' % (nFrames, fname, timeString(startFrame), timeString(endFrame))

                skip = startFrame - currFrame
                if skip > 0:
                    #print 'Skipping %d frames' % (skip,)
                    wvi.readframes(skip)
                    currFrame += skip
                elif skip < 0:
                    print "Warning: can't back up"

                if verify:
                    frames = wvi.readframes(nSampleFrames)
                    x = struct.unpack(sampleFormat, frames)

                    off = max(map(abs, x))

                    frames0 = wvi.readframes(nSampleFrames)
                    frames1 = wvi.readframes(nSampleFrames)
                    x1 = struct.unpack(sampleFormat, frames1)
                    #print x1[:75]
                    
                    frames = wvi.readframes(nSampleFrames)
                    x = struct.unpack(sampleFormat, frames)
                    on = max(map(abs, x))

                    currFrame += 4 * nSampleFrames
                    total = on + off
                    if total > 0:
                        score = float(on) / float(total)
                    else:
                        score = 0.0
                    if score < .05:
                        print '****** Missing start at %s, %f sec, %d samps (score %f) ******' % (timeString(startFrame), startFrame / frameRate, startFrame0, score)
                    else:
                        print 'Found start at %s, %f sec, %d samps (score %f)' % (timeString(startFrame), startFrame / frameRate, startFrame0, score)
                else:
                    frames = wvi.readframes(nFrames)
                    currFrame += nFrames
                    if doAgc:
                        if params[1] == 2:
                            clipFormat = '<' + 'hh' * nFrames
                        else:
                            clipFformat = '<' + 'xxhxxh' * nFrames
                        x = struct.unpack(clipFormat, frames)
                        peak = max(map(abs, x))
                        if peak > 0:
                            gain = .60 * 2**15 / peak
                            gain = min(10.0, max(.1, gain))
                            x = [ int(y * gain) for y in x]
                        x = struct.pack(clipFormat, *x)
                    if taper:
                        if params[1] == 2:
                            clipFormat = '<' + 'hh' * nFrames
                        else:
                            clipFormat = '<' + 'xxhxxh' * nFrames
                        x = struct.unpack(clipFormat, frames)
                        if len(x) > nTaperFrames:
                            nFront = len(x) - nTaperFrames;
                            front = x[0:nFront]
                            back = list(x[nFront:])
                            for iSamp, samp in enumerate(back):
                                t = float(iSamp) / float(nTaperFrames)
                                gain = math.sqrt(1.0 - t)
                                back[iSamp] = int(round(back[iSamp] * gain))
                            frames = struct.pack(clipFormat, *(front + tuple(back)))
                    wvo = wave.open('%s/%s' % (wavdir, fname,), 'w')
                    params[3] = nFrames
                    wvo.setparams(tuple(params))
                    wvo.writeframes(frames)
                    wvo.close()

                    # was using constant bitrate
                    #sfile.write('lame -q0 -b128 %s/%s %s/%s\n' % (wavdir, fname, mp3dir, mp3name))

                    # latest lame recomendations (https://wiki.hydrogenaud.io/index.php?title=LAME)
                    # included -V3 (~175 kbs) or -V4 (~165 kbs)
                    # V3 was lowest quality home setting, V4 was highest quality mobile setting
                    sfile.write('lame -V4 %s/%s %s/%s\n' % (wavdir, fname, mp3dir, mp3name))

        wvi.close()
        sfile.write('cp %s %s\n' % (lname, mp3dir))
        tar = mp3dir + '.tar'
        sfile.write('tar cf %s %s\n''' % (tar, mp3dir))
        sfile.write('echo tagmotifs.py %s\n' % (bname,))
        if subdirs:
            sfile.write('tagmotifs.py --subdirs %d %s\n' % (subdirs, bname,))
        else:
            sfile.write('tagmotifs.py %s\n' % (bname,))
        sfile.close()
        os.chmod(sfileName, stat.S_IRWXU)
                                
    main()
