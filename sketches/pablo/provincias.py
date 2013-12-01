import os
import math
import glob
import json
import StringIO
import hashlib
import shapefile
import xml.etree.ElementTree as ET
from collections import OrderedDict

from kartograph import Kartograph
from kartograph.options import read_map_config

def obtain_shp_file():
    all_coordinates = obtain_kml_coordinates()

    fields = [('DeletionFlag', 'C', 1, 0), ['Name', 'C', 15, 0]]

    records = []
    polygons = []
    w = shapefile.Writer(shapefile.POLYGON)

    for pos, coordinates in enumerate(all_coordinates):
        records.append([ 'Name %s' % pos ])
        w.poly(parts=[ coordinates[::-1] ])
    
    for field in fields:
        w.field(*field)

    for record in records:
        w.record(*record)

    prj_contents = open("../../data/geo/template.prj").read()
    open('provincias.prj', 'w').write(prj_contents)
    w.save('../../data/geo/provincias')
    print "done"
        

def obtain_kml_coordinates():
    root = ET.fromstring(open("provincias.kml").read())
    all_coordinates = []
    for node in root.findall(".//{http://earth.google.com/kml/2.1}coordinates"):
        coordinates = node.text.split()

        final_coordinates = []
        for coord_line in coordinates:
            coord_line = coord_line.strip()
            if coord_line:
                longitude, latitude = coord_line.split(',')
                final_coordinates.append([float(longitude), float(latitude)])
        all_coordinates.append(final_coordinates)
    print all_coordinates
    return all_coordinates

if __name__ == '__main__':
    obtain_shp_file()
