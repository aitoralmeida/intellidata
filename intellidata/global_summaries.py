import json
from flask import Blueprint, render_template, url_for, request
from .util import get_week_borders, generate_color_code, generate_timetable, FIELDS, WEEKS, MONTHS, CATEGORIES, KMS

global_blueprint = Blueprint('global', __name__)

@global_blueprint.route('/summary/')
def summary():
    return ":-)"

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

