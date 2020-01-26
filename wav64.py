#!/usr/bin/env python

import sys, pdb, struct, os, traceback

def makeHash16(sig):
    sig = list(sig)
    for i in xrange(4):
        sig[i] = ord(sig[i])
    guid = ''.join([ chr(x) for x in sig])
    return guid

riffGuid = makeHash16( ('r', 'i', 'f', 'f',
                        0x2E, 0x91, 0xCF, 0x11, 0xA5, 0xD6, 0x28, 0xDB, 0x04, 0xC1, 0x00, 0x00) )
waveGuid = makeHash16( ('w', 'a', 'v', 'e',
                        0xF3, 0xAC, 0xD3, 0x11, 0x8C, 0xD1, 0x00, 0xC0, 0x4F, 0x8E, 0xDB, 0x8A) )

fmtGuid = makeHash16( ('f', 'm', 't', ' ',
                       0xF3, 0xAC, 0xD3, 0x11, 0x8C, 0xD1, 0x00, 0xC0, 0x4F, 0x8E, 0xDB, 0x8A) )

dataGuid = makeHash16( ('d', 'a', 't', 'a',
                        0xF3, 0xAC, 0xD3, 0x11, 0x8C, 0xD1, 0x00, 0xC0, 0x4F, 0x8E, 0xDB, 0x8A) )

bextGuid = makeHash16( ('b', 'e', 'x', 't',
                        0xf3, 0xac, 0xd3, 0xaa, 0xd1, 0x8c, 0x00, 0xC0, 0x4F, 0x8E, 0xDB, 0x8A) )

def printGuid(guid):
    print guid[:4], ''.join([ "%02x" % (ord(c), ) for c in guid ])

class Wave64(object):
    def __init__(self):
        self.init()

    def init(self):
        self.framesRemaining = 0
        self.frameSize = 0
        self.wav = None

    def open(self, name):
        #pdb.set_trace()
        self.init()
        self.name = name
        self.wfile = open(self.name, 'rb')
        self.offset = 0
        try:
            guid = self.getChunk()
        except:
            guid = None
        if guid != riffGuid:
            self.wfile.close()
            import wave
            self.wav = wave.open(self.name)
            return
        # Go ahead and injest guids to data (need params)
        haveFmt = False
        while True:
            guid = self.getChunk()
            if not guid:
                raise Exception, "No data chunk"
            if guid == fmtGuid:
                haveFmt = True
            if guid == dataGuid:
                break
        if not haveFmt:
            raise Exception, "No fmt chunk"

    def close(self):
        self.wfile.close()
        self.wfile = None
    
    def readframes(self, nframes):
        if self.wav:
            return self.wav.readframes(nframes)
        if nframes > self.framesRemaining:
            nToRead = self.framesRemaining
        else:
            nToRead = nframes
        nBytes = nToRead * self.frameSize
        data = self.read(nBytes)
        if len(data) != nBytes:
            raise Exception, "Truncated file (only read %d of %d)" % (len(data), nBytes)
        nframes -= nToRead
        self.framesRemaining -= nToRead
        return data

    def read(self, nBytes):
        if nBytes < 0:
            raise Exception, "Bug"
        bytes = self.wfile.read(nBytes)
        if len(bytes) < nBytes:
            return ''
        self.offset += nBytes
        return bytes
    
    def readSize(self):
        sz = self.read(8)
        least,most = struct.unpack('<II', sz)
        sz = most * 0x100000000 + least
        return sz

    def getChunk(self):
        partial = self.offset % 8
        if partial:
            self.read(8 - partial)
        guid = self.read(16)
        if len(guid) < 16:
            return ''
        #printGuid(guid)
        if guid == riffGuid:
            fsize = self.readSize()
            #print 'file size', fsize
            wguid = self.read(16)
            #printGuid(wguid)
        elif guid == fmtGuid:
            nBytes = self.readSize()
            if nBytes != 40:
                raise Exception, "Bad fmt chunk"
            bytes = self.read(nBytes-24)
            self.format, self.nChan, self.sampleRate, self.byteRate, self.frameSize, self.bitsPerSample \
                = struct.unpack("<HHIIHH", bytes)
            #print 'fmt', self.format, self.nChan, self.sampleRate, self.byteRate, self.frameSize, self.bitsPerSample
            self.bytesPerSample = self.frameSize / self.nChan
            if self.bitsPerSample != 8 * self.bytesPerSample:
                raise Exception, "bitsPerSample != 8 * bytesPerSample"
        elif guid == dataGuid:
            nBytes = self.readSize() - 24
            if nBytes % self.frameSize != 0:
                raise Exception, "Data chunk size not multiple of frame size"
            self.nFrames = nBytes / self.frameSize
            self.framesRemaining = self.nFrames
        else:
            skip = self.readSize()
            self.read(skip - 24) # size includes guid and size already read
        return guid
        
    def getparams(self):
        if self.wav:
            return self.wav.getparams()
        return (self.nChan, self.bytesPerSample, self.sampleRate, self.nFrames, 'NONE', 'not compressed')

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
        wav = Wave64()
        wav.open(pargs[0])
        #pdb.set_trace()
        nFrames = 0
        while True:
            frame = wav.readframes(1)
            if len(frame) == 0:
                break
            nFrames += 1
            if nFrames % 1000000 == 0:
                print nFrames
        print nFrames, 'frames read'
        
            
    main()

