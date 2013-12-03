import json
import datetime
from operator import itemgetter
from collections import OrderedDict

from bson.code import Code

from flask import Blueprint, render_template, url_for, request

from intellidata import mongo
from .geotools import generate_zipcodes_map, Algorithms
from .util import get_week_borders, generate_color_code, generate_timetable, FIELDS, WEEKS, MONTHS, CATEGORIES, KMS, CATEGORY_NAMES

search_blueprint = Blueprint('search', __name__)

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

@search_blueprint.route('/')
def index():
    age = request.args.get('age', 'all')
    gender = request.args.get('gender', 'all')
    category = request.args.get('category', 'all')
    return render_template("search/index.html", categories = CATEGORIES, category_names = CATEGORY_NAMES, age = age, gender = gender, category = category)

@search_blueprint.route('/basic/')
def basic_results():
    age = request.args.get('age', 'all')
    gender = request.args.get('gender', 'all')
    category = request.args.get('category', 'all')
    criteria = request.args.get('criteria', 'total')
    preference = request.args.get('preference', 'absolute')

    default_top_results = 20
    try:
        top_results = int(request.args.get('top', default_top_results))
    except:
        top_results = default_top_results
    if top_results > 100:
        top_results = 100

    # for zipcode_data in mongo.db.shop_zipcode_summary.find({ '$where' : Code("""function() { return this.value.total.total.total > 9000000; }""")}, fields = '_id'):
    #    print zipcode_data

    query = {}
    if age != 'all':
        query['age_code'] = age
    if gender != 'all':
        query['gender'] = gender
    if category != 'all':
        query['category'] = category

    reducer = Code("""
    function(obj, prev) {
        prev.total += obj.num_payments * obj.avg;
        prev.num_payments += obj.num_payments;
        prev.avg = prev.total / prev.num_payments;
    }
    """)

    elements = mongo.db.cube_month.group(key = { 'shop_zipcode' : 1}, condition = query, initial = { 'num_payments' : 0, 'total' : 0, 'avg' : 0 }, reduce = reducer)
    results = sorted(elements, lambda v1, v2 : cmp(v2[criteria], v1[criteria]))[:top_results]

    return render_template("search/index.html", categories = CATEGORIES, category_names = CATEGORY_NAMES, age = age, gender = gender, category = category, results = results, query_processed = True)


