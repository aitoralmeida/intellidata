#!/usr/bin/env python
import os
import sys
import json
import glob
import urllib2
import traceback


def geo(zipcode):
    content = urllib2.urlopen("http://codigospostales.dices.net/mapacodigopostal.php?codigopostal=%s" % zipcode).read()
    latitud, longitud = content.split('<h3><b>Latitud: ')[1].split('<br>')[0:2]
    latitud = latitud.split('</b>')[0]
    longitud = longitud.split('</b>')[0].split(' ')[-1]
    return json.dumps((latitud, longitud))

for x in range(1000):
    print "Processing %s..." % x, 
    madrid = str(28000 + x)
    barcelona = str(8000 + x).zfill(5)

    try:
        fname = 'output/%s.json' % madrid
        if not os.path.exists(fname):
            content = geo(madrid)
            open(fname, 'w').write(content)
    except:
        print >> sys.stderr, "Error processing %s" % madrid
        traceback.print_exc()

    try:
        fname = 'output/%s.json' % barcelona
        if not os.path.exists(fname):
            content = geo(barcelona)
            open(fname, 'w').write(content)
    except:
        print >> sys.stderr, "Error processing %s" % barcelona
        traceback.print_exc()
    print "[done]"
    sys.stdout.flush()

data = {}
for fname in glob.glob("output/*.json"):
    zip_code = os.path.basename(fname).split('.')[0]
    latitud, longitud = json.load(open(fname))
    if latitud == "" and longitud == "":
        data[zip_code] = None
    else:
        data[zip_code] = latitud, longitud

json.dump(data, open('all_zipcodes.json', 'w'), indent = 4)

