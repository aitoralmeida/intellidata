from flask import Flask, render_template
from flask.ext.pymongo import PyMongo

import config
app = Flask(__name__)
app.config.from_object(config)

mongo = PyMongo(app)

# Frontpage links
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# Basic visualizations
from .local import local_blueprint
from .search import search_blueprint
from .global_summaries import global_blueprint
app.register_blueprint(local_blueprint, url_prefix = '/local')
app.register_blueprint(global_blueprint, url_prefix = '/global')
app.register_blueprint(search_blueprint, url_prefix = '/search')


def run():
    app.run(debug = True, host = '0.0.0.0')
