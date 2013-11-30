import os
import glob
import json
import StringIO
import hashlib
import shapefile
import xml.etree.ElementTree as ET
from kartograph import Kartograph
from kartograph.options import read_map_config

# TODO: Put to True
USE_CACHE = False
CACHE_KML = USE_CACHE and True
CACHE_SHP = CACHE_KML  and True
CACHE_MAP = CACHE_SHP  and True



def generate_zipcodes_map(data, zipcode, identifier, key_field):
    """
    Generate a map with provided data. It will cache the maps based on the 
    identifier, which will be the name. The zipcode is used to find the kml.

    The key_field will be the field taken into account for the heat map.

    Example. Providing this data:
    {

        '28004' : { # Each external zipcode

            'key1' : 154,
            'key2' : 153,
            'key3' : 155,
        },
        '28009' : { # Each external zipcode

            'key1' : 300,
            'key2' : 100,
            'key3' :  50,
        }
    }
    
    A zipcode called '28008', an identifier 'heatmap_incomes', and a key_field 'key1', it will generate and cache a map where the zipcodes 28004 and 28009 will appear, being the latter closer to red since its 'key1' is higher.
    """
    data_hash = hashlib.new("md5", repr(data)).hexdigest()

    svg_file = 'intellidata/static/geo/%s_%s_%s_%s.svg' % (zipcode, identifier, key_field, data_hash)

    if CACHE_MAP and os.path.exists(svg_file):
        return svg_file

    shp_file_path = obtain_shp_file(data, zipcode, identifier, key_field, data_hash)

    # TODO: improve this. It's already done before
    all_fields = set()

    for zdata in data.values():
        for field in zdata:
            all_fields.add(field)

    sorted_fields = sorted(list(all_fields))
    attributes = {'Fullposition' : 'Fullposition'}
    for sorted_field in sorted_fields:
        attributes[sorted_field] = sorted_field
        attributes[sorted_field.title()] = sorted_field.title()

    kartograph_settings = {
    "proj": {
            "id": "sinusoidal",
            "lon0": 20
      },
       "layers": {
       "background": {"special": "sea"},
       "graticule":{ 
            "special": "graticule", 
            "latitudes": 1, 
            "longitudes": 1, 
            "styles": { "stroke-width": "0.3px" } 
       },
#        "world":{
#             "src": "data/geo/ne_10m_admin_0_countries.shp"
#         },
       "world" : {
           "src" : "data/geo/ne_50m_admin_0_countries.shp"
       },

       "zipcodes":{
           "src": shp_file_path,
           "attributes": attributes
       }
       },
      "bounds": {
        "mode": "bbox",
        "data": [-10, 36, 5, 44],
        "crop": [-12, 34, 7, 46]
      }
    }

    kartograph_settings_sio = StringIO.StringIO(json.dumps(kartograph_settings))
    kartograph_settings_sio.name = svg_file + '.json'
    K = Kartograph()
    css = open("intellidata/static/geo/maps.css").read()
    cfg = read_map_config(kartograph_settings_sio)
    K.generate(cfg, outfile=svg_file, format='svg', stylesheet=css)
    return svg_file


def obtain_shp_file(data, zipcode, identifier, key_field, data_hash):
    """Generate shapefile with the same format as generate_zipcodes_map. Return the
    URL"""

    shp_file_without_extension = 'data/geo/%s_%s_%s_%s' % (zipcode, identifier, key_field, data_hash)
    shp_file_with_extension = shp_file_without_extension + '.shp'

    if CACHE_SHP and os.path.exists(shp_file_with_extension):
        return shp_file_with_extension
    
    fields = [('DeletionFlag', 'C', 1, 0), ['Fullposition', 'N', 10, 0], ['Zipcode', 'C', 5, 0]]

    positions = {}
    max_value = 0
    all_fields = set()

    for zcode, zdata in data.iteritems():
        coordinates = obtain_kml_coordinates(zcode)
        if coordinates is None:
            print "Error with zcode", zcode
            # TODO 
            fake_data = [[-3.691456382, 40.4257756531], [-3.692212419, 40.4260832871], [-3.693450755, 40.4267022431], [-3.69508936, 40.4275437201], [-3.695139107, 40.4278736111], [-3.695333688, 40.4280358781], [-3.695822313, 40.4282056771], [-3.696128986, 40.4282059731], [-3.696351159, 40.4281309091], [-3.696539296, 40.4279775601], [-3.69716058, 40.4281197451], [-3.698165722, 40.4283647961], [-3.698330451, 40.4283873451], [-3.699714574, 40.4286606651], [-3.700071756, 40.4287363011], [-3.700960129, 40.4289244191], [-3.70155328, 40.4290605971], [-3.701719851, 40.4293331391], [-3.702168696, 40.4293964771], [-3.703547438, 40.4293864751], [-3.704687035, 40.4295841771], [-3.705133968, 40.4296670271], [-3.705260734, 40.4298176001], [-3.705274616, 40.4293455611], [-3.705472976, 40.4291782241], [-3.705705033, 40.4291351871], [-3.70580649, 40.4289814921], [-3.705853702, 40.4287895451], [-3.705971017, 40.4283125771], [-3.706052636, 40.4279807401], [-3.706240225, 40.4273020301], [-3.706305368, 40.4271821231], [-3.706675631, 40.4265006001], [-3.706930485, 40.4260315031], [-3.706962092, 40.4259831591], [-3.707140709, 40.4257099521], [-3.707147119, 40.4256876551], [-3.707282307, 40.4252173841], [-3.707322854, 40.4250763331], [-3.707318335, 40.4250311161], [-3.707275916, 40.4249987551], [-3.707289996, 40.4247475131], [-3.70725075, 40.4243317701], [-3.707287707, 40.4239379801], [-3.707328613, 40.4235021061], [-3.707363185, 40.4231337271], [-3.707451814, 40.4227520721], [-3.707494643, 40.4225676421], [-3.707663239, 40.4220575711], [-3.707778864, 40.4216636181], [-3.706823875, 40.4210678741], [-3.70633047, 40.4207700801], [-3.706128893, 40.4205845621], [-3.705968931, 40.4204967621], [-3.705500453, 40.4204674951], [-3.705257305, 40.4204523051], [-3.705031495, 40.4204381981], [-3.704734007, 40.4204259111], [-3.704316826, 40.4203922051], [-3.704063922, 40.4203717711], [-3.704289608, 40.4196945351], [-3.70425594, 40.4196854711], [-3.703793649, 40.4203446681], [-3.702998346, 40.4203084021], [-3.701867048, 40.4202329831], [-3.70105992, 40.4201590121], [-3.70040934, 40.4200447381], [-3.699870984, 40.4199501751], [-3.699758165, 40.4198695491], [-3.699526046, 40.4198565271], [-3.698359669, 40.4195398651], [-3.697378284, 40.4192939481], [-3.696994724, 40.4192351511], [-3.696650607, 40.4191824011], [-3.694493089, 40.4195356861], [-3.692935746, 40.4197906951], [-3.691450473, 40.4228102561], [-3.690483211, 40.4247766991], [-3.691548683, 40.4250327211], [-3.691456382, 40.4257756531]][::-1]
            positions[zcode] = fake_data
            continue
        # [::-1] is because KML provides the data in a format and kartography expects other (clockwise vs. not clockwise)
        positions[zcode] = coordinates[::-1]
        for field in zdata:
            all_fields.add(field)
        max_value = max(max_value, zdata[key_field])

    steps = max_value / 256.0
    sorted_fields = sorted(list(all_fields))
    for field in sorted_fields:
        fields.append([field, 'C', 32, 0])

    records = []
    polygons = []

    w = shapefile.Writer(shapefile.POLYGON)

    for zcode, zdata in data.iteritems():
        step = int(zdata[key_field] / steps)
        record = [step,zcode]
        for field in sorted_fields:
            record.append(str(zdata[field]))
        records.append(record)
        w.poly(parts=[ positions[zcode] ])
    
    for field in fields:
        w.field(*field)

    for record in records:
        w.record(*record)

    prj_contents = open("data/geo/template.prj").read()
    open(shp_file_without_extension + '.prj', 'w').write(prj_contents)
    w.save(shp_file_without_extension)
    return shp_file_with_extension
        

def obtain_kml_coordinates(zipcode):
    zipcode = str(zipcode)
    # TODO: could change this directory to a non public one
    json_path = 'intellidata/static/kml/%s.json' % zipcode
    if CACHE_KML and os.path.exists(json_path):
        return json.load(open(json_path))

    # If it does not exist, generate it
    kml_file = "intellidata/static/kml/%s.kml" % zipcode
    if not os.path.exists(kml_file):
        print "KML file for zipcode %s not found. Expected at %s" % (zipcode, kml_file)
        return None

    # Convert the KML file into a SHP file
    open(kml_file).read()
    root = ET.fromstring(open("intellidata/static/kml/%s.kml" % zipcode).read())
    coordinates = root.findall(".//{http://www.opengis.net/kml/2.2}coordinates")[0].text.splitlines()

    final_coordinates = []
    for coord_line in coordinates:
        coord_line = coord_line.strip()
        if coord_line:
            longitude, latitude, altitude = coord_line.split(',')
            final_coordinates.append([float(longitude), float(latitude)])

    json.dump(final_coordinates, open(json_path, 'w'))
    return final_coordinates

print "Creating KML cache"
for kml in glob.glob("intellidata/static/kmls/*.kml"):
    zipcode = os.path.basename(kml).split('.')[0]
    obtain_kml_coordinates(zipcode)

