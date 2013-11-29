from bbvalib import create_mongoclient
import json

db = create_mongoclient()

home_zipcodes = set()

home_zipcodes.update(set(db.top_clients_week.find().distinct('home_zipcode')))
home_zipcodes.update(set(db.top_clients_month.find().distinct('home_zipcode')))
home_zipcodes.update(set(db.top_clients_week.find().distinct('shop_zipcode')))
home_zipcodes.update(set(db.top_clients_month.find().distinct('shop_zipcode')))


json.dump(list(home_zipcodes), open('home_zipcodes.json', 'w'))

