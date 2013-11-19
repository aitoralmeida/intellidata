from bbvalib import create_mongoclient
import json

db = create_mongoclient()
json.dump(db.top_clients_week.find().distinct('home_zipcode'), open('home_zipcodes.json', 'w'))

