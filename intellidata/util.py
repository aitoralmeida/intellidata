import datetime

FIELDS = { 'incomes' : 'Incomes', 'numcards' : 'Cards', 'numpay' : 'Payments' }
WEEKS  = [u'201244', u'201245', u'201246', u'201247', u'201248', u'201249', u'201250', u'201251', u'201252', u'201301', u'201302', u'201303', u'201304', u'201305', u'201306', u'201307', u'201308', u'201309', u'201310', u'201311', u'201312', u'201313', u'201314', u'201315', u'201316', u'201317']
MONTHS = [u'201211', u'201212', u'201301', u'201302', u'201303', u'201304']
CATEGORIES = ['es_auto','es_barsandrestaurants','es_contents','es_fashion',
              'es_food','es_health','es_home','es_hotelservices','es_hyper',
              'es_leisure','es_otherservices','es_propertyservices',
              'es_sportsandtoys','es_tech','es_transportation','es_travel',
              'es_wellnessandbeauty']
KMS = [50, 100, 200, 300, 400]


def get_week_borders(week_number, year):
    january_first = datetime.datetime.strptime('%s-01-01' % year, '%Y-%m-%d')

    if january_first.weekday() == 6:
        first_sunday = january_first
    else:
        first_sunday = january_first - datetime.timedelta(days = (january_first.weekday() + 1))

    border_low  = first_sunday + datetime.timedelta(days = 7 * week_number)
    border_high = first_sunday + datetime.timedelta(days = 7 * week_number + 6)
    return border_low, border_high

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
