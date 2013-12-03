import json
import datetime
from operator import itemgetter
from collections import OrderedDict

from flask import Blueprint, render_template, url_for, request

from intellidata import mongo
from .geotools import generate_zipcodes_map, Algorithms
from .util import get_week_borders, generate_color_code, generate_timetable, FIELDS, WEEKS, MONTHS, CATEGORIES, KMS, CATEGORY_NAMES

local_blueprint = Blueprint('local', __name__)

AGES = {
    '0' : '0-18',
    '1' : '19-25',
    '2' : '26-35',
    '3' : '36-45',
    '4' : '46-55',
    '5' : '56-65',
    '6' : '66+',
    'U' : 'unknown',
}

@local_blueprint.route('/zipcodes/')
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

@local_blueprint.route('/zipcodes/<zipcode>/')
def zipcode_summary(zipcode):
    return render_template("basic/zipcode.html", zipcode = zipcode)


@local_blueprint.route('/zipcodes/<zipcode>/single_map/')
def zipcode_simple_map(zipcode):
    field = 'incomes'
    algorithm = 'ranked'
    data = {
        str(zipcode) : {
            str(field) : 0
        }
    }

    svg_file_path = generate_zipcodes_map(data, zipcode, 'single', field, algorithm)
    svg_file_path = 'geo/' + svg_file_path.split('/')[-1]
    return json.dumps({ 'url' : url_for('static', filename = svg_file_path) })


@local_blueprint.route('/zipcodes/<zipcode>/map/')
def zipcode_map(zipcode):
    return zipcode_map_algorithm(zipcode, 'all', Algorithms.DEFAULT, 'incomes', 'any', 'any')

@local_blueprint.route('/zipcodes/<zipcode>/map/<category>/<algorithm>/<field>/<time_filter>/<time_frame>/')
def zipcode_map_algorithm(zipcode, category, algorithm, field, time_filter, time_frame):
    link_tpl = url_for('.zipcode_map_algorithm', zipcode = zipcode, category = category, algorithm = 'ALGORITHM', field = 'FIELD', time_filter = time_filter, time_frame = time_frame)
    week = None
    month = None
    if time_filter == 'week':
        week = time_frame
    elif time_filter == 'month':
        month = time_frame
    elif time_filter != 'any':
        return render_template("errors.html", message = "Invalid time filter")
    return _zipcode_map_algorithm_impl(zipcode, category, algorithm, field, link_tpl, time_filter, time_frame, week, month)

def _zipcode_map_algorithm_impl(zipcode, category, algorithm, field, link, time_filter, time_frame, week, month):
    error, data = _retrieve_data(zipcode, category, algorithm, field, week, month)
    if error:
        return error

    incomes  = [ (k, v['incomes']) for k, v in data.items() ]
    numpay   = [ (k, v['numpay']) for k, v in data.items() ]
    numcards = [ (k, v['numcards']) for k, v in data.items() ]
    avg      = [ (k, v['incomes'] / (v['numpay'] if v['numpay'] > 0 else 1)) for k, v in data.items() ]

    DEFAULT_TOP = 5
    MAX_TOP = 100
    try:
        top_number = int(request.args.get('top', DEFAULT_TOP))
    except:
        top_number = DEFAULT_TOP

    if top_number > MAX_TOP:
        top_number = MAX_TOP

    top_incomes = zip(range(top_number), sorted(incomes, lambda (k1, v1), (k2,v2) : cmp(v2, v1))[:top_number])
    top_pays    = zip(range(top_number), sorted(numpay, lambda (k1, v1), (k2,v2) : cmp(v2, v1))[:top_number])
    top_avg     = zip(range(top_number), sorted(avg, lambda (k1, v1), (k2,v2) : cmp(v2, v1))[:top_number])

    all_field_data = sorted([ (k, v[field]) for k, v in data.items() ], lambda (k1, v1), (k2, v2) : cmp(v1, v2))

    def second_elements(elements):
        return dict(elements).values()

    summary = {
        'top_incomes' : top_incomes,
        'top_pays' : top_pays,
        'top_avg'  : top_avg,
        'incomes.total' : sum(second_elements(incomes)),
        'numpay.total' : sum(second_elements(numpay)),
        'numcards.total' : sum(second_elements(numcards)),
        'avg.total' : sum(second_elements(avg)),
        'timeline_headers' : map(itemgetter(0), all_field_data),
        'timeline_values'  : map(itemgetter(1), all_field_data),
    }

    if week is not None:
        file_link_path = url_for('.zipcode_map_file_week', zipcode = zipcode, category = category, algorithm = algorithm, field = field, week = week)
        mode = 'week'
    elif month is not None:
        file_link_path = url_for('.zipcode_map_file_month', zipcode = zipcode, category = category, algorithm = algorithm, field = field, month = month)
        mode = 'month'
    else:
        file_link_path = url_for('.zipcode_map_file', zipcode = zipcode, category = category, algorithm = algorithm, field = field)
        mode = 'total'

    # 
    # Obtain demography data
    # 
    zipcode_data = next(mongo.db.shop_zipcode_summary.find({ '_id' : zipcode }), None)
    cubes = {}
    cubes_totals = {}
    if zipcode_data is None:
        demography = False
    else:
        value = zipcode_data['value']

        field_translator = {
            'numpay' : 'num_payments',
            'cards'  : 'num_cards',
            'incomes' : 'total'
        }
        current_field = field_translator[field]

        cubes = {
            'male' : {
                '0' : 0, '1' : 0, '2' : 0, '3' : 0, '4' : 0, '5' : 0, '6' : 0, 'U' : 0,
            },
            'female' : {
                '0' : 0, '1' : 0, '2' : 0, '3' : 0, '4' : 0, '5' : 0, '6' : 0, 'U' : 0,
            },
            'enterprise' : {
                'U' : 0,
            },
            'unknown' : {
                '0' : 0, '1' : 0, '2' : 0, '3' : 0, '4' : 0, '5' : 0, '6' : 0, 'U' : 0,
            }
        }
        total = 0

        if mode == 'week':
            for cur_category, category_data in value['categories'].iteritems():
                if category == 'all' or category == cur_category:
                    if week in category_data['weeks']:
                        week_data = category_data['weeks'][week]
                        cube_data = week_data['cubes']['cubes']
                        for gender in cube_data:
                            for age in cube_data[gender]:
                                cubes[gender][age] += cube_data[gender][age][current_field]
                                total += cube_data[gender][age][current_field]

        elif mode == 'month':
            for cur_category, category_data in value['categories'].iteritems():
                if category == 'all' or category == cur_category:
                    if month in category_data['months']:
                        month_data = category_data['months'][month]
                        cube_data = month_data['cubes']['cubes']
                        for gender in cube_data:
                            for age in cube_data[gender]:
                                cubes[gender][age] += cube_data[gender][age][current_field]
                                total += cube_data[gender][age][current_field]

        else:
            for cur_category, category_data in value['categories'].iteritems():
                if category == 'all' or category == cur_category:
                    for month_data in category_data['months'].values():
                        cube_data = month_data['cubes']['cubes']
                        for gender in cube_data:
                            for age in cube_data[gender]:
                                cubes[gender][age] += cube_data[gender][age][current_field]
                                total += cube_data[gender][age][current_field]

        if total == 0:
            demography = False
        else:
            demography = True
            for gender in cubes:
                for age in cubes[gender]:
                    cubes[gender][age] = 100.0 * cubes[gender][age] / total

        cubes_totals = {}
        cubes_totals['male'] = sum(cubes['male'].values())
        cubes_totals['female'] = sum(cubes['female'].values())
        cubes_totals['enterprise'] = sum(cubes['enterprise'].values())
        cubes_totals['unknown'] = sum(cubes['unknown'].values())
        for age in cubes['male']:
            cubes_totals[age] = cubes['male'][age] + cubes['female'][age] + cubes['enterprise'].get(age, 0)
    
    # 
    # Show navigation
    # 

    months_data = {}

    for month_id in MONTHS:
        year = int(month_id[:4])
        month_number = int(month_id[-2:])
    
        MONTH_NAMES = ['-', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

        months_data[month_id] = {
            'year' : year,
            'name' : MONTH_NAMES[month_number],
            'link' : url_for('.zipcode_map_algorithm', zipcode = zipcode, category = category, algorithm = algorithm, field = field, time_filter = 'month', time_frame = month_id),
            'weeks' : []
        }

    for week_id in WEEKS:
        year = int(week_id[:4])
        week_number = int(week_id[-2:])
        start_day, end_day = get_week_borders(week_number, year)

        def generate_week(start_day, current_month, current_month_id):
            week_data = {
                'link' : url_for('.zipcode_map_algorithm', zipcode = zipcode, category = category, algorithm = algorithm, field = field, time_filter = 'week', time_frame = week_id),
                'number' : week_number,
                'selected' : week == week_id or current_month_id == month
            }
            for pos, weekday in enumerate(('sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday')):
                cur_day = start_day + datetime.timedelta(days=pos)
                week_data[weekday] = {
                    'active' : cur_day.month == current_month,
                    'day' : cur_day.day,
                }
            return week_data
        def format_month(date):
            return '%s%s' % (date.year, str(date.month).zfill(2))

        month_id = format_month(start_day)
        week_data = generate_week(start_day, start_day.month, month_id)
        if month_id in months_data:
            months_data[month_id]['weeks'].append(week_data)

        if end_day.month != start_day.month:
            month_id = format_month(end_day)
            week_data = generate_week(start_day, end_day.month, month_id)
            if month_id in months_data:
                months_data[month_id]['weeks'].append(week_data)

    months = []
    for cur_month in MONTHS:
        months.append(months_data[cur_month])

    return render_template("basic/map.html", zipcode = zipcode, category = category, algorithm = algorithm, algorithms = Algorithms.ALGORITHMS, field = field, fields = FIELDS, months = months, week = week, month = month, link_template = link, file_link_path = file_link_path, summary = summary, demography = demography, cubes = cubes, cubes_totals = cubes_totals, ages = AGES, categories = CATEGORIES, category_names = CATEGORY_NAMES, time_frame = time_frame, time_filter = time_filter)


@local_blueprint.route('/zipcodes/<zipcode>/map/filepath/<category>/<algorithm>/<field>/')
def zipcode_map_file(zipcode, category, algorithm, field):
    return _zipcode_map_file_impl(zipcode, category, algorithm, field)

@local_blueprint.route('/zipcodes/<zipcode>/map/filepath/<category>/<algorithm>/<field>/week/<week>/')
def zipcode_map_file_week(zipcode, category, algorithm, field, week):
    return _zipcode_map_file_impl(zipcode, category, algorithm, field, week = week)

@local_blueprint.route('/zipcodes/<zipcode>/map/filepath/<category>/<algorithm>/<field>/month/<month>/')
def zipcode_map_file_month(zipcode, category, algorithm, field, month):
    return _zipcode_map_file_impl(zipcode, category, algorithm, field, month = month)

def _retrieve_data(zipcode, category, algorithm, field, week = None, month = None):
    if algorithm not in Algorithms.ALGORITHMS:
        return render_template("errors.html", message = "Invalid algorithm"), None

    if field not in FIELDS:
        return render_template("errors.html", message = "Invalid field"), None

    if category not in CATEGORIES and category != 'all':
        return render_template("errors.html", message = "Invalid category"), None

    if week is not None and week not in WEEKS:
        return render_template("errors.html", message = "Invalid week"), None

    if month is not None and month not in MONTHS:
        return render_template("errors.html", message = "Invalid month"), None

    zipcode_data = next(mongo.db.top_clients_summary.find({ '_id' : zipcode }), None)
    if zipcode_data is None:
        return render_template("errors.html", message = "zipcode not found"), None

    data = {}

    if month is not None:
        key = 'per_month'
    else:
        key = 'per_week'

    if week is not None:
        value = week
    elif month is not None:
        value = month
    else:
        value = 'total'

    if category == 'all':
        cat_query = 'total'
    else:
        cat_query = category

    for zcode, zdata in zipcode_data['value']['home_zipcodes'].iteritems():
        if key in zdata and value in zdata[key]:
            if zdata[key][value][cat_query]['num_payments'] > 0:
                data[zcode] = dict(
                    incomes      = zdata[key][value][cat_query]['incomes'],
                    numcards     = int(zdata[key][value][cat_query]['num_cards']),
                    numpay       = int(zdata[key][value][cat_query]['num_payments'])
                )
    return None, data


def _zipcode_map_file_impl(zipcode, category, algorithm, field, week = None, month = None):
    error, data = _retrieve_data(zipcode, category, algorithm, field, week, month)
    if error:
        return error

    if len(data) == 0:
        data = {
            str(zipcode) : {
                str(field) : 0
            }
        }

    svg_file_path = generate_zipcodes_map(data, zipcode, '%s_%s_%s' % (category, week or 'anyweek', month or 'anymonth'), field, algorithm)
    svg_file_path = 'geo/' + svg_file_path.split('/')[-1]
    return json.dumps({ 'url' : url_for('static', filename = svg_file_path) })


@local_blueprint.route('/zipcodes/<zipcode>/timeline/')
def zipcode_timeline(zipcode):
    zipcode_data = next(mongo.db.shop_zipcode_summary.find({ '_id' : zipcode }), None)
    if zipcode_data is None:
        return render_template("errors.html", message = "zipcode not found")

    fields = ['avg', 'num_payments', 'total']

    data = {}
    for field in fields:
        data[field] = [], []

    weeks_data = zipcode_data['value']['total']['weeks']
    for week in sorted(weeks_data.keys()):
        year        = int(week[:4])
        week_number = int(week[-2:])
        start_day, _ = get_week_borders(week_number, year)
        
        for field in fields:
            data[field][0].append(start_day.strftime("%d/%m/%Y"))
            data[field][1].append(weeks_data[week]['summary'][field])

    category_data = {}
    for category in CATEGORIES:
        category_data[category] = {}

        for field in fields:
            category_data[category][field] = [], []

        weeks_data = zipcode_data['value']['categories'][category]['weeks']
        for week in sorted(weeks_data.keys()):
            year        = int(week[:4])
            week_number = int(week[-2:])
            start_day, _ = get_week_borders(week_number, year)
            
            for field in fields:
                category_data[category][field][0].append(start_day.strftime("%d/%m/%Y"))
                
                total_data = weeks_data[week]['cubes']['total']['per_gender']
                total_value = 0
                for gender in 'male', 'female', 'enterprise', 'unknown':
                    total_value += total_data[gender][field]

                category_data[category][field][1].append(total_value)

    return render_template("basic/zipcode_timeline.html", zipcode = zipcode, data = data, categories = CATEGORIES, category_names = CATEGORY_NAMES, category_data = category_data)

@local_blueprint.route('/zipcodes/<zipcode>/timetables/')
def zipcode_timetables(zipcode):
    zipcode_data = next(mongo.db.shop_zipcode_summary.find({ '_id' : zipcode }), None)
    if zipcode_data is None:
        return render_template("errors.html", message = "zipcode not found")

    days_data = zipcode_data['value']['total']['days']
    total_timetables = generate_timetable(days_data)

    categories = zipcode_data['value']['categories'].keys()
    return render_template("basic/zipcode_timetable.html", total_timetables = total_timetables, categories = categories, zipcode = zipcode, category_names = CATEGORY_NAMES)

@local_blueprint.route('/zipcodes/<zipcode>/timetables/<category>/')
def zipcode_timetables_category(zipcode, category):
    zipcode_data = next(mongo.db.shop_zipcode_summary.find({ '_id' : zipcode }), None)
    if zipcode_data is None:
        return render_template("errors.html", message = "zipcode not found")

    if category not in zipcode_data['value']['categories']:
        return render_template("errors.html", message = "category not found")

    category_data = zipcode_data['value']['categories'][category]
    category_timetable = generate_timetable(category_data['total']['days'])

    return render_template("basic/zipcode_timetable_category.html", category = category, category_timetable = category_timetable, category_names = CATEGORY_NAMES)

@local_blueprint.route("/zipcodes/<zipcode>/top_clients/")
def zipcode_top_clients(zipcode):
    return ":-)"

