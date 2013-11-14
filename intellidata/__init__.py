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
app.register_blueprint(basic_blueprint, url_prefix = '/basic')


def run():
    app.run(debug = True)
