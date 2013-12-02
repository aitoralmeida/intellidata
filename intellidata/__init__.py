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
from .basic import basic_blueprint
from .global_summaries import global_blueprint
app.register_blueprint(basic_blueprint, url_prefix = '/basic')
app.register_blueprint(global_blueprint, url_prefix = '/global')


def run():
    app.run(debug = True)
