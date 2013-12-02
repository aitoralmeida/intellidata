import json
from flask import Blueprint, render_template, url_for, request
from .util import get_week_borders, generate_color_code, generate_timetable, FIELDS, WEEKS, MONTHS, CATEGORIES, KMS, CATEGORY_NAMES


from intellidata import mongo

global_blueprint = Blueprint('global', __name__)


SUMMARY = json.load(open('data/summary.json'))

SUMMARY_WEEKS = None
SUMMARY_WEEKS_CATEGORIES = None

def _get_weeks():
    global SUMMARY_WEEKS, SUMMARY_WEEKS_CATEGORIES

    if SUMMARY_WEEKS is None:
        weeks = {
            # '201314' : { 
            #      'incomes' : 0, 
            #      'num_payments' : 0, 
            #      'avg' : 0 
            # }
        }
        category_weeks = {
            # 'category1' : {
            #      '201314'  : {
            #         'incomes' : 0,
            #         'num_payments' : 0,
            #         'avg' : 0,
            #      }
        }
        for result in mongo.db.cube_week.find():
            week = result['week']

            if week in weeks:
                weeks[week]['incomes']      += result['num_payments'] * result['avg']
                weeks[week]['num_payments'] += result['num_payments']
                weeks[week]['avg']          = 1.0 * weeks[week]['incomes'] / weeks[week]['num_payments']
            else:
                weeks[week] = { 'incomes' : result['num_payments'] * result['avg'],
                                'num_payments' : result['num_payments'],
                                'avg'          : result['avg'] }

            category = result['category']
            if category not in category_weeks:
                category_weeks[category] = {}

            if week in category_weeks[category]:
                category_weeks[category][week]['incomes']      += result['num_payments'] * result['avg']
                category_weeks[category][week]['num_payments'] += result['num_payments']
                category_weeks[category][week]['avg']          = 1.0 * category_weeks[category][week]['incomes'] / category_weeks[category][week]['num_payments']
            else:
                category_weeks[category][week] = { 'incomes' : result['num_payments'] * result['avg'],
                                'num_payments' : result['num_payments'],
                                'avg'          : result['avg'] }

        SUMMARY_WEEKS_CATEGORIES = category_weeks
        SUMMARY_WEEKS = weeks
    else:
        weeks = SUMMARY_WEEKS
        category_weeks = SUMMARY_WEEKS_CATEGORIES

    return weeks, category_weeks


@global_blueprint.route('/summary/')
def summary():
    weeks, _ = _get_weeks()
    sorted_weeks = sorted(weeks.keys())

    formatted_weeks = []

    for week in sorted_weeks:
        year        = int(week[:4])
        week_number = int(week[-2:])
        start_day, _ = get_week_borders(week_number, year)
        formatted_week = start_day.strftime("%d/%m/%Y")
        formatted_weeks.append(formatted_week)


    timelines = {
        'sorted_weeks' : formatted_weeks,
        'incomes'      : [ weeks[week]['incomes'] for week in sorted_weeks ],
        'num_payments' : [ weeks[week]['num_payments'] for week in sorted_weeks ],
        'avg'          : [ weeks[week]['avg'] for week in sorted_weeks ]
    }

    return render_template('global/summary.html', summary = SUMMARY, categories = [ 'complete' ] + CATEGORIES, category_names = CATEGORY_NAMES, timelines = timelines)

@global_blueprint.route('/summary/timelines/')
def summary_timeline():
    weeks, category_weeks = _get_weeks()
    sorted_weeks = sorted(weeks.keys())

    formatted_weeks = []

    for week in sorted_weeks:
        year        = int(week[:4])
        week_number = int(week[-2:])
        start_day, _ = get_week_borders(week_number, year)
        formatted_week = start_day.strftime("%d/%m/%Y")
        formatted_weeks.append(formatted_week)

    timelines = {}
    timelines['sorted_weeks'] = sorted_weeks

    for category in CATEGORIES:
        timelines[category] = {
            'incomes'      : [ 0.0 for week in sorted_weeks ],
            'num_payments' : [ 0   for week in sorted_weeks ],
            'avg'          : [ 0.0 for week in sorted_weeks ],
        }

    for category in category_weeks:
        print category
        timelines[category] = {
            'incomes'      : [ category_weeks[category][week]['incomes'] for week in sorted_weeks ],
            'num_payments' : [ category_weeks[category][week]['num_payments'] for week in sorted_weeks ],
            'avg'          : [ category_weeks[category][week]['avg'] for week in sorted_weeks ]
        }  

    return render_template('global/timelines.html', sorted_categories = CATEGORIES, category_names = CATEGORY_NAMES, timelines = timelines)


@global_blueprint.route('/adjacency/')
def adjacency():
    return render_template("basic/adjacency_index.html", kms = KMS, categories = CATEGORIES)

@global_blueprint.route('/adjacency/<category>/<int:kms>/')
def adjacency_category(category, kms):
    if kms not in KMS:
        return render_template("errors.html", message = "Invalid kilometers")

    if category not in CATEGORIES:
        return render_template("errors.html", message = "Invalid category")
    
    fname = 'matrix/%s%s.json' % (kms, category)
    size = len(json.load(open('intellidata/static/' + fname))['nodes']) * 13.5

    return render_template("basic/adjacency.html", json_filename = url_for('static', filename = fname), kms = kms, category = category, width = size, height = size)

@global_blueprint.route('/geodataviz/')
def geodataviz():
    return render_template("geoviz/index.html")

@global_blueprint.route('/geodataviz/geodata.js')
def geodataviz_script():
    return render_template("geoviz/loxawebsite-0.9.1.js")

