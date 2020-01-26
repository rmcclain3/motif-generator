#!/usr/bin/env python

import sys, pdb

if __name__ == '__main__':
    options = ['help']

    def usage():
        print 'ngrams.py n1 [n2]'
        print 'Options:'
        for word in options:
            print '  ', word
        sys.exit(0)
        
    import getopt
    def main():
        # I use reformatted datasets from:
        #    http://www.peachnote.com/datasets.html
        #    created by Vladimir Viro
        # Purpose of reformatting is to order by popularity

        opts, pargs = getopt.getopt(sys.argv[1:], '', options)
        for opt, val in opts:
            if opt == '--help':
                usage()

        if len(pargs) < 2:
            usage()
        n1 = n2 = int(pargs[0])
        if len(pargs) == 2:
            n2 = int(pargs[1])


        for i in xrange(n1, n2+1):
            db = {}
            # I let Vladimir know I can't unzip the 14ngram file (has been no problem for my use)
            if i == 14:
                continue
            name = 'imslp-interval-%dgram-20110401.csv' % (i,)
            print name
            f = open(name)
            line = f.readline()
            while line:
                line = line.rstrip()
                ng, year, count = line.split('\t')
                count = int(count)
                ng = ng.split()
                ng = map(int, ng)
                ng = tuple(ng)
                if ng in db:
                    db[ ng ] += count
                else:
                    db[ ng ] = count
                line = f.readline()
            f.close()

            array = [ (count, ng) for ng, count in db.iteritems() ]
            db = None
            array.sort(reverse=True)

            name = 'ngram%d.csv' % (i,)
            f = open(name, 'w')
            for count, ng in array:
                for jump in ng:
                    f.write('%d ' % (jump,))
                f.write('\t2012\t%d\n' % (count,))
            f.close()
            array = None

main()
