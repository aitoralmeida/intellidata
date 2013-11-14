import json
from bbvalib import create_mongoclient


db = create_mongoclient()
zipcodes = set()
zipcodes.update(db.top_clients_week.find().distinct("shop_zipcode"))
zipcodes.update(db.top_clients_month.find().distinct("shop_zipcode"))
zipcodes.update(db.top_clients_week.find().distinct("home_zipcode"))
zipcodes.update(db.top_clients_month.find().distinct("home_zipcode"))
json.dump(list(zipcodes), open('home_zipcodes.json', 'w'))
