try:
    import config
except ImportError:
    print "Copia config.py.dist a config.py, cenutrio"

def create_mongoclient():
    from pymongo import MongoClient
    client = MongoClient(port=config.MONGODB_PORT)
    db = client.bbva
    return db

