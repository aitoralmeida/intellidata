#!/usr/bin/env python
import os
import glob

cache_files = glob.glob("data/geo/28*") + glob.glob("data/geo/08*") + glob.glob("intellidata/static/geo/28*") + glob.glob("intellidata/static/geo/08*")
for f in cache_files:
    os.remove(f)

