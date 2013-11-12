import os
import json
import glob

from bbvalib import create_mongoclient

def process_origin_flat():
    bbva = create_mongoclient()

    bbva.top_clients_week.remove()
    bbva.top_clients_month.remove()

    origin_files = glob.glob("data/scraped/origin-*.json")
    for f in origin_files:
        _, by, category, shop_zipcode = os.path.basename(f)[:-5].split('-')
        contents = json.load(open(f))

        stats = contents['data']['stats']

        for period in stats:
            cur_date = period['date']

            for home_zipcode_data in period['zipcodes']:
                cur_data = dict(
                        category = category,
                        shop_zipcode = shop_zipcode,
                        home_zipcode = home_zipcode_data['label'],
                        incomes      = home_zipcode_data['incomes'],
                        num_cards    = home_zipcode_data['num_cards'],
                        num_payments = home_zipcode_data['num_payments'],
                    )
                cur_data[by] = cur_date

                if by == 'week':
                    bbva.top_clients_week.insert(cur_data)
                elif by == 'month':
                    bbva.top_clients_moth.insert(cur_data)
                else:
                    print "Error: %s is not (month, key)" % by

def process_cube_flat():
    bbva = create_mongoclient()
    bbva.cube_week.remove()
    bbva.cube_month.remove()

    genders = {
        'U' : 'unknown',
        'F' : 'female',
        'M' : 'male',
        'E' : 'enterprise'
    }

    ages = {
        '0' : {
            'min_age' : 0,
            'max_age' : 18,
        },
        '1' : {
            'min_age' : 19,
            'max_age' : 25
        }, 
        '2' : {
            'min_age' : 26,
            'max_age' : 35
        },
        '3' : {
            'min_age' : 36,
            'max_age' : 45
        },
        '4' : {
            'min_age' : 46,
            'max_age' : 55,
        },
        '5' : {
            'min_age' : 56,
            'max_age' : 65
        },
        '6' : {
            'min_age' : 66,
            'max_age' : 100
        },
        'U' : {
            'min_age' : 0,
            'max_age' : 100
        }
    }

    origin_files = glob.glob("data/scraped/cube-*.json")
    for f in origin_files:
        # cube-week-es_auto-28004.json
        _, by, category, shop_zipcode = os.path.basename(f)[:-5].split('-')
        contents = json.load(open(f))

        stats = contents['data']['stats']

        for period in stats:
            cur_date = period['date']

            for cube in period['cube']:
                gender_code, age_code = cube['hash'].split('#')

                cur_data = dict(
                    category     = category,
                    shop_zipcode = shop_zipcode,
                    hash         = cube['hash'],
                    gender       = genders[gender_code],
                    age_code     = age_code,
                    min_age      = ages[age_code]['min_age'],
                    max_age      = ages[age_code]['max_age'],
                    avg          = cube['avg'],
                    num_cards    = cube['num_cards'],
                    num_payments = cube['num_payments'],
                )
                cur_data[by] = cur_date

                if by == 'week':
                    bbva.cube_week.insert(cur_data)
                elif by == 'month':
                    bbva.cube_month.insert(cur_data)
                else:
                    print "Error: %s is not in (week, month)" % by

def process_patterns():
    bbva = create_mongoclient()
    bbva.patterns_month.remove()

    origin_files = glob.glob("data/scraped/patterns-*.json")
    for f in origin_files:
        # patterns-month-es_barsandrestaurants-28004.json
        _, by, category, shop_zipcode = os.path.basename(f)[:-5].split('-')
        if by != 'month':
            print "Error: %s is not in (month)" % by
            continue

        contents = json.load(open(f))

        stats = contents['data']['stats']

        for period in stats:
            for day_data in period['days']:
                cur_data = dict(
                    month        = period['date'],
                    category     = category,
                    shop_zipcode = shop_zipcode,
                    key          = '%s#%s' % (day_data['day'].lower(), period['date']),
                    day          = day_data['day'].lower(),
                    mode         = day_data['mode'],
                    num_payments = day_data['num_payments'],
                    avg          = day_data['avg'],
                    std          = day_data['std'],
                    min          = day_data['min'],
                    max          = day_data['max'],
                    num_cards    = day_data['num_cards'],
                    hours        = day_data['hours'],
                )
                bbva.patterns_month.insert(cur_data)

# process_origin_flat()
process_cube_flat()
process_patterns()

