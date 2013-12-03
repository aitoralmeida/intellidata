#!/usr/bin/env python

import os
import sys

sys.stdout = sys.stderr

INTELLIDATA_DIR = os.path.dirname(__file__)

sys.path.insert(0, INTELLIDATA_DIR)
os.chdir(INTELLIDATA_DIR)

import config

from intellidata import app as application
application.config.from_object('config')
