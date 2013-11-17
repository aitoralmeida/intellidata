from flask import Blueprint, render_template

from intellidata import mongo

basic_blueprint = Blueprint('basic', __name__)

def generate_color_code(value, max_value):
    # white to red
    percent = 1.0 * value / max_value
    blue  = hex(int(256 - 256 * percent)).split('x')[1].zfill(2)
    green = hex(int(256 - 256 * percent)).split('x')[1].zfill(2)
    return 'ff%s%s' % (green, blue)


def generate_timetable(days_data):
    fields = 'total', 'max', 'num_payments', 'avg'

    timetables = {}
    max_values = {}
    for field in fields:
        timetables[field] = {
            'hours' : {},
            'empty_hours' : set()
            # hours:{
            #    hour : { 
            #        day : {
            #            value : 513,
            #            color : 'ffffff',
            #        }
            #    },
            # },
            # empty_hours : set(['01', '02', '03'])
        }
        max_values[field] = 0
    timetables['num_payments']['format'] = '%i'

    for day in days_data:
        day_data = days_data[day]
        hours_data = day_data['hours']
        for hour in hours_data:
            hour_data = hours_data[hour]
            
            for field in fields:
                if hour not in timetables[field]['hours']:
                    timetables[field]['hours'][hour] = {}
                timetables[field]['hours'][hour][day] = dict(value = hour_data[field], color = '000000')
                if hour_data[field] > max_values[field]:
                    max_values[field] = hour_data[field]

    # Fill empty_hours
    for field in fields:
        for hour_number in range(24):
            hour = str(hour_number).zfill(2)
            if not hour in timetables[field]['hours']:
                timetables[field]['empty_hours'].add(hour)


    for field in fields:
        max_value = max_values[field]
        for hour in timetables[field]['hours']:
            for day in timetables[field]['hours'][hour]:
                cur_data = timetables[field]['hours'][hour][day]
                cur_data['color'] = generate_color_code(cur_data['value'], max_value)
    return timetables

@basic_blueprint.route('/zipcodes/')
def zipcodes():
    madrid_zipcodes    = []
    barcelona_zipcodes = []
    for zc in mongo.db.shop_zipcode_summary.find({}, fields=('_id',)):
        zipcode = zc['_id']
        if zipcode.startswith('08'):
            barcelona_zipcodes.append(zipcode)
        else:
            madrid_zipcodes.append(zipcode)
    return render_template("basic/zipcodes.html", madrid_zipcodes = sorted(madrid_zipcodes), barcelona_zipcodes = sorted(barcelona_zipcodes))

@basic_blueprint.route('/zipcodes/<zipcode>')
def zipcode(zipcode):
    zipcode_data = next(mongo.db.shop_zipcode_summary.find({ '_id' : zipcode }), None)
    if zipcode_data is None:
        return render_template("errors.html", message = "zipcode not found")

    days_data = zipcode_data['value']['total']['days']

    total_timetables = generate_timetable(days_data)

    category_timetables = {}
    for category in zipcode_data['value']['categories']:
        days_data = zipcode_data['value']['categories'][category]['total']['days']
        category_timetables[category] = generate_timetable(days_data)

    return render_template("basic/zipcode.html", total_timetables = total_timetables, category_timetables = category_timetables)
