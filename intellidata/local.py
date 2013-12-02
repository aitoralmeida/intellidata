import json
from operator import itemgetter
from collections import OrderedDict

from flask import Blueprint, render_template, url_for, request

from intellidata import mongo
from .geotools import generate_zipcodes_map, Algorithms
from .util import get_week_borders, generate_color_code, generate_timetable, FIELDS, WEEKS, MONTHS, CATEGORIES, KMS

local_blueprint = Blueprint('local', __name__)

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

@local_blueprint.route('/zipcodes/<zipcode>/map/')
def zipcode_map(zipcode):
    return zipcode_map_algorithm(zipcode, Algorithms.DEFAULT, 'incomes')


@local_blueprint.route('/zipcodes/<zipcode>/map/<algorithm>/<field>/')
def zipcode_map_algorithm(zipcode, algorithm, field):
    link_tpl = url_for('.zipcode_map_algorithm', zipcode = zipcode, algorithm = 'ALGORITHM', field = 'FIELD')
    return _zipcode_map_algorithm_impl(zipcode, algorithm, field, link = link_tpl)

@local_blueprint.route('/zipcodes/<zipcode>/map/<algorithm>/<field>/week/<week>/')
def zipcode_map_algorithm_week(zipcode, algorithm, field, week):
    link_tpl = url_for('.zipcode_map_algorithm_week', zipcode = zipcode, algorithm = 'ALGORITHM', field = 'FIELD', week = week)
    return _zipcode_map_algorithm_impl(zipcode, algorithm, field, link = link_tpl, week = week)

@local_blueprint.route('/zipcodes/<zipcode>/map/<algorithm>/<field>/month/<month>/')
def zipcode_map_algorithm_month(zipcode, algorithm, field, month):
    link_tpl = url_for('.zipcode_map_algorithm_month', zipcode = zipcode, algorithm = 'ALGORITHM', field = 'FIELD', month = month)
    return _zipcode_map_algorithm_impl(zipcode, algorithm, field, link = link_tpl, month = month)


def _zipcode_map_algorithm_impl(zipcode, algorithm, field, link, week = None, month = None):
    error, data = _retrieve_data(zipcode, algorithm, field, week, month)
    if error:
        return error

    incomes  = map(itemgetter('incomes'), data.values())
    numpay   = map(itemgetter('numpay'), data.values())
    numcards = map(itemgetter('numcards'), data.values())

    field_data = sorted(map(itemgetter(field), data.values()))
    # So as to create the timeline, we need to show:
    # axis X: each value
    # axis Y: aggregated value
    # TODO

    summary = {
        'incomes.total' : sum(incomes),
        'numpay.total' : sum(numpay),
        'numcards.total' : sum(numcards),
        'timeline_headers' : range(len(field_data)),
        'timeline_values'  : field_data,
    }

    if week is not None:
        file_link_path = url_for('.zipcode_map_file_week', zipcode = zipcode, algorithm = algorithm, field = field, week = week)
    elif month is not None:
        file_link_path = url_for('.zipcode_map_file_month', zipcode = zipcode, algorithm = algorithm, field = field, month = month)
    else:
        file_link_path = url_for('.zipcode_map_file', zipcode = zipcode, algorithm = algorithm, field = field)

    weeks = OrderedDict()
    for week_id in WEEKS:
        year = int(week_id[:4])
        week_number = int(week_id[-2:])
        start_day, _ = get_week_borders(week_number, year)
        weeks[week_id] = start_day

    months = OrderedDict()
    for month_id in MONTHS:
        year = int(month_id[:4])
        month_number = int(month_id[-2:])
        months[month_id] = '%s/%s' % (month_number, year)

    return render_template("basic/map.html", zipcode = zipcode, algorithm = algorithm, algorithms = Algorithms.ALGORITHMS, field = field, fields = FIELDS, months = months, weeks = weeks, week = week, month = month, link_template = link, file_link_path = file_link_path, summary = summary)


@local_blueprint.route('/zipcodes/<zipcode>/map/filepath/<algorithm>/<field>/')
def zipcode_map_file(zipcode, algorithm, field):
    return _zipcode_map_file_impl(zipcode, algorithm, field)

@local_blueprint.route('/zipcodes/<zipcode>/map/filepath/<algorithm>/<field>/week/<week>/')
def zipcode_map_file_week(zipcode, algorithm, field, week):
    return _zipcode_map_file_impl(zipcode, algorithm, field, week = week)

@local_blueprint.route('/zipcodes/<zipcode>/map/filepath/<algorithm>/<field>/month/<month>/')
def zipcode_map_file_month(zipcode, algorithm, field, month):
    return _zipcode_map_file_impl(zipcode, algorithm, field, month = month)

def _retrieve_data(zipcode, algorithm, field, week = None, month = None):
    if algorithm not in Algorithms.ALGORITHMS:
        return render_template("errors.html", message = "Invalid algorithm"), None

    if field not in FIELDS:
        return render_template("errors.html", message = "Invalid field"), None

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

    for zcode, zdata in zipcode_data['value']['home_zipcodes'].iteritems():
        if key in zdata and value in zdata[key]:
            data[zcode] = dict(
                incomes      = zdata[key][value]['total']['incomes'],
                numcards     = int(zdata[key][value]['total']['num_cards']),
                numpay       = int(zdata[key][value]['total']['num_payments'])
            )
    return None, data


def _zipcode_map_file_impl(zipcode, algorithm, field, week = None, month = None):
    error, data = _retrieve_data(zipcode, algorithm, field, week, month)
    if error:
        return error

    svg_file_path = generate_zipcodes_map(data, zipcode, '%s_%s' % (week or 'anyweek', month or 'anymonth'), field, algorithm)
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

    return render_template("basic/zipcode_timeline.html", zipcode = zipcode, data = data)

@local_blueprint.route('/zipcodes/<zipcode>/timetables/')
def zipcode_timetables(zipcode):
    zipcode_data = next(mongo.db.shop_zipcode_summary.find({ '_id' : zipcode }), None)
    if zipcode_data is None:
        return render_template("errors.html", message = "zipcode not found")

    days_data = zipcode_data['value']['total']['days']
    total_timetables = generate_timetable(days_data)

    categories = zipcode_data['value']['categories'].keys()
    return render_template("basic/zipcode_timetable.html", total_timetables = total_timetables, categories = categories, zipcode = zipcode)

@local_blueprint.route('/zipcodes/<zipcode>/timetables/<category>/')
def zipcode_timetables_category(zipcode, category):
    zipcode_data = next(mongo.db.shop_zipcode_summary.find({ '_id' : zipcode }), None)
    if zipcode_data is None:
        return render_template("errors.html", message = "zipcode not found")

    if category not in zipcode_data['value']['categories']:
        return render_template("errors.html", message = "category not found")

    category_data = zipcode_data['value']['categories'][category]
    category_timetable = generate_timetable(category_data['total']['days'])

    return render_template("basic/zipcode_timetable_category.html", category_name = category.title(), category_timetable = category_timetable)

@local_blueprint.route("/zipcodes/<zipcode>/top_clients/")
def zipcode_top_clients(zipcode):
    return ":-)"

