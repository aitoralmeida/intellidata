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

    if latitud == '' or longitud == '':
        content = urllib2.urlopen("http://www.codigospostales.com/%s").read()
        if ("%s </title>" % zipcode) not in content: # Otherwise, it does not exist
            pass

    return json.dumps((latitud, longitud))

def kml(zipcode):
    print "Downloading KML of %s..." % zipcode,
    fname = 'kmls/%s.kml' % zipcode
    if os.path.exists(fname):
        print "[loaded]"
    else:
        try:
            content = urllib2.urlopen("http://www.codigospostales.com/kml/%s/%s.kml" % (zipcode[:2], zipcode)).read()
        except urllib2.HTTPError:
            print "[not found]"
        except:
            print "Error"
            traceback.print_exc()
        else:
            open(fname, 'w').write(content)
            print "[done]"
    sys.stdout.flush()
    sys.stderr.flush()

USE_HOME_ZIPCODES = True
home_zipcodes = json.load(open('home_zipcodes.json'))

for x in range(1000, 51000):
    ciudad = str(x).zfill(5)
    must_process = False
    if USE_HOME_ZIPCODES:
        if ciudad in home_zipcodes or str(x) in home_zipcodes:
            must_process = True
    else:
        must_process = True

    if must_process:
        print "Processing %s..." % ciudad, 

        try:
            fname = 'output/%s.json' % ciudad
            if os.path.exists(fname):
                print "[loaded]"
            else:
                content = geo(ciudad)
                if content != json.dumps(['','']):
                    open(fname, 'w').write(content)
                    print "[done]"
                else:
                    print "[not found]"
        except:
            print >> sys.stderr, "Error processing %s" % ciudad
            traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        kml(ciudad)

data = {}
for fname in glob.glob("output/*.json"):
    zip_code = os.path.basename(fname).split('.')[0]
    latitud, longitud = json.load(open(fname))
    if latitud == "" and longitud == "":
        data[zip_code] = None
    else:
        data[zip_code] = latitud, longitud

json.dump(data, open('all_zipcodes.json', 'w'), indent = 4)

