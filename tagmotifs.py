#!/bin/env python

import sys, pdb, mutagen.id3, codecs, glob, os
# Code located at /usr/lib/python2.7/site-packages/mutagen/id3/
#   class ID3 in __init__.py
#   frames are listed in _frames.py
#   Songs ripped by iTunes seem to use ID3v2.2
#      (song: TT2, artist: TP1, album: TCM, track: TRK) all plain text
#   iTunes sorts by Artist/Album so each set should have it's own album
#   So set TP1 to 'Mr Ear', TCM to bname, and TT2 to mname
#   But I used ID3v2.4 and it's okay. Initially used USLT which is Unicode


lf = u'\240a'

if __name__ == '__main__':
    options = ['help', 'pdb', 'log', 'subdirs=' ]

    def usage():
        print "tagmotifs.py <bname>"
        print "Options:"
        for word in options:
            print "  ", word
        sys.exit(0)
        
    import getopt
    def main():
        doPdb = False
        logOnly = False
        subdirs = 0
        opts, pargs = getopt.getopt(sys.argv[1:], '', options)
        for opt, val in opts:
            if opt == '--help':
                usage()
            elif opt == '--pdb':
                doPdb = True
            elif opt == '--log':
                logOnly = True
            elif opt == '--subdirs':
                subdirs = int(val)

        if len(pargs) < 1:
            usage()

        if doPdb:
            pdb.set_trace()

        bname = pargs[0]
        lname = bname + '.log'
        mp3dir = bname + '_mp3'
        tname = bname + '.tag'

        if not glob.glob(mp3dir + '.tar'):
            print 'you forgot to tar the mp3 directory for safety'
            sys.exit()

        log = codecs.open(tname, 'w', 'utf_16')
            
        for line in codecs.open(lname, 'r', 'utf_16'):
            line = line.strip()
            words = line.split(lf)
            if words[0].startswith(u'marker'):
                continue
            mname, iSeg, start, stop, startFrame, stopFrame = words[0].split()
            if subdirs:
                subdir = '_'.join(mname.split('_')[0:0+subdirs])
                aname = bname + '_' + subdir  # album
                tname = mname                  # title
                mname = subdir + '/' + mname
            else:
                aname = bname
                tname = mname

            lyric = []
            for word in words[1:]:
                label, content = word.split(u':', 1)
                lyric.append(content.strip())
            lyric = u'\n'.join(lyric)
            
            mp3path = "%s/%s.mp3" % (mp3dir, mname)
            log.write(u'%s\n%s\n\n' % (unicode(mp3path), lyric))
            if logOnly:
                continue
            tags = mutagen.id3.ID3()
            tags['TIT2'] = mutagen.id3.TIT2(encoding=3, lang=u'eng', text=tname)
            tags['TPE2'] = mutagen.id3.TPE2(encoding=0, lang=u'eng', text='Mr Ear')
            tags['TALB'] = mutagen.id3.TALB(encoding=0, lang=u'eng', text=aname)
            tags['USLT'] = mutagen.id3.USLT(encoding=3, lang=u'eng', text=lyric)

            tags.save(mp3path)
                                
    main()
