import os
import json
import glob

from bbvalib import create_mongoclient

#############################################################################
# 
# 
#     Import flat data (regular tables)
# 
# 


def process_origin_flat():
    bbva = create_mongoclient()

    bbva.drop_collection('top_clients_week')
    bbva.drop_collection('top_clients_month')

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
                    bbva.top_clients_month.insert(cur_data)
                else:
                    print "Error: %s is not (month, key)" % by

def process_cube_flat():
    bbva = create_mongoclient()
    bbva.drop_collection('cube_week')
    bbva.drop_collection('cube_month')

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

def process_patterns_flat():
    bbva = create_mongoclient()
    bbva.drop_collection('patterns_month')

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

DELETE_ALL = False
if DELETE_ALL:
    process_origin_flat()
    process_cube_flat()
    process_patterns_flat()


#############################################################################
# 
# 
#       Aggregate data (map reduce)
# 
# 

def top_clients_summary():
    from bson.code import Code
    from bson.son import SON

    bbva = create_mongoclient()
    bbva.drop_collection('top_clients_summary')

    categories = bbva.top_clients_week.find().distinct('category')
    categories = json.dumps(categories)

    map_func = Code("""function () {            
            // Create the summaries (one with the data, the other empty)
            var summary = {
                'incomes'      : this.incomes,
                'num_cards'    : this.num_cards,
                'num_payments' : this.num_payments
            };

            var empty_summary = {
                'incomes'      : 0,
                'num_cards'    : 0,
                'num_payments' : 0
            };

            // self will be useful in inner functions
            var self = this;

            // Select by (per_week, per_month) and the current date (the week or the month)
            var by, date, empty_by;
            if (this.week === undefined) {
                if (this.month === undefined ) {
                    throw new Error("this.month or this.week must exist");
                } else {
                    // Month exists; week doesn't
                    by = 'per_month';
                    empty_by = 'per_week';
                    date = this.month;
                }
            } else {
                // Week exists
                by = 'per_week';
                empty_by = 'per_month';
                date = this.week;
            }

            // Start adding data
            // Create the basic infrastructure, and add the register with this zipcode
            var value = {
                'home_zipcodes' : {}
            };
            value['home_zipcodes'][this.home_zipcode] = {
                'per_week'  : {
                    'total' : {
                        // Later on, it will have this:
                        // total: (incomes, num_cards, num_payments)
                        // category1 : (incomes, num_cards, num_payments)
                        // category2 : (incomes, num_cards, num_payments)
                    }
                },
                'per_month' : {
                    'total' : {
                        // Later on, it will have this:
                        // total: (incomes, num_cards, num_payments)
                        // category1 : (incomes, num_cards, num_payments)
                        // category2 : (incomes, num_cards, num_payments)
                    }
                } 
            };

            // Right now, we don't have added any data. We start now.

            // Fill all the categories (except for "total") of total with zeros
            %(CATEGORIES)s.forEach(function(category) { 
                value['home_zipcodes'][self.home_zipcode]['per_week']['total'][category] = empty_summary;
                value['home_zipcodes'][self.home_zipcode]['per_month']['total'][category] = empty_summary;
            });

            // Add the total value
            value['home_zipcodes'][self.home_zipcode][by]['total']['total'] = summary;
            value['home_zipcodes'][self.home_zipcode][empty_by]['total']['total'] = empty_summary;
            
            // Add the category value (it existed, but was initialized to empty)
            value['home_zipcodes'][self.home_zipcode][by]['total'][this.category] = summary;

            // 
            // Now, total has been filled. We start with each week (or month)
            // 

            value['home_zipcodes'][self.home_zipcode][by][date] = {
                'total' : summary
                // It will also be filled with:
                // category1: (incomes, num_cards, num_payments)
                // category2: (incomes, num_cards, num_payments)
            };

            // First, we clear all the categories (except for total):
            %(CATEGORIES)s.forEach(function(category) {
                value['home_zipcodes'][self.home_zipcode][by][date][category] = empty_summary;
            });

            // Then, we add the category data
            value['home_zipcodes'][this.home_zipcode][by][date][this.category] = summary;
            
            emit(this.shop_zipcode, value);
    }""" % dict(
        CATEGORIES = categories,
    ))

    reduce_func = Code("""function (key, values) {
        
        var deepcopy = function (obj) {
            return JSON.parse(JSON.stringify(obj));
        }

        var return_value = {
            'home_zipcodes' : {}
        };

        var return_home_zipcodes = return_value['home_zipcodes'];

        values.forEach(function(value) {

            /* Each value has the following structure:
            {
                'home_zipcodes' : {
                    '28004' : {
                        'per_week' : {
                            'total' : {
                                'category1' : {
                                    income, num_cards, num_payments
                                },
                                'category2' : {
                                    income, num_cards, num_payments
                                },
                                'total' : {
                                    income, num_cards, num_payments
                                }
                            },
                            '201301' : {
                                'category1' : {
                                    income, num_cards, num_payments
                                },
                                'category2' : {
                                    income, num_cards, num_payments
                                },
                                'total' : {
                                    income, num_cards, num_payments
                                }                               
                            }
                        }
                        'per_month' :  (same as in per_week)
                    }
                }
            }
            */

            // For each zipcode in the value
            for (var home_zipcode in value['home_zipcodes']) {
                // If that zipcode was previously unknown, just copy the data.
                if (return_home_zipcodes[home_zipcode] == undefined) {
                    return_home_zipcodes[home_zipcode] = deepcopy(value['home_zipcodes'][home_zipcode]);
                } else {

                    // If it existed, the merge it. "me" is the current zipcode data, other is the 
                    // existing zipcode data.

                    var me = value['home_zipcodes'][home_zipcode];
                    var other = return_home_zipcodes[home_zipcode];
                   
                    // We're gonna sum everything. 'total' is just yet another category for us
                    var categories = %(CATEGORIES)s;
                    categories.push('total');

                    ['per_week', 'per_month'].forEach(function(by) {
                        
                        // First, the total numbers

                        // Both in per_week and per_month, sum the existing total data for 
                        // every category (including total).
                        categories.forEach(function(category) {
                            other[by]['total'][category]['incomes']      += me[by]['total'][category]['incomes'];
                            other[by]['total'][category]['num_cards']    += me[by]['total'][category]['num_cards'];
                            other[by]['total'][category]['num_payments'] += me[by]['total'][category]['num_payments'];
                        });

                        // Second, the week / month numbers
                        
                        // For each date in the current data (the existing data does not need any change)
                        for (var date in me[by]) {

                            // If this new data is not present in the existing data, just copy it.
                            if (other[by][date] == undefined) {
                                // Those only in me (and not in other)
                                other[by][date] = deepcopy(me[by][date]);
                            } else {

                                // If it exists in both, merge it. cur_other and cur_me are the particular data.
                                // e.g. other = 'home_zipcodes' / '28004';
                                //      cur_other = 'home_zipcodes' / '28004' / 'per_week' / '201301'
                                var cur_other = other[by][date];
                                var cur_me    = me[by][date];

                                // For each category (including total), sum the data
                                categories.forEach(function(category) {
                                    cur_other[category]['incomes']      += cur_me[category]['incomes'];
                                    cur_other[category]['num_cards']    += cur_me[category]['num_cards'];
                                    cur_other[category]['num_payments'] += cur_me[category]['num_payments'];
                                });
                            }
                        }
                        
                    });
                }
            }
        });

        if ( key == "28760" ) {
            var cur_zipcode = return_value['home_zipcodes']['28760'];
            if (cur_zipcode != undefined ) {
                var cur_data = cur_zipcode['per_week']['201301'];
                if (cur_data != undefined ) {

                    if (cur_zipcode['per_week']['total']['es_home']['incomes'] != 0) {
                        print("---------------------------------------------------------------------");
                        printjson(cur_zipcode['per_week']['total']['es_home']);
                        print("");
                        print("=>");
                        print("");
                        printjson(cur_data['es_home']);
                        print("");

                        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++");
                        print("++++++++++++++++++V A L U E S++++++++++++++++++++++++++++++++++++++++");
                        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++");
                        printjson(values);
                        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++");
                        print("++++++++++++++++++R E T U R N I N G++++++++++++++++++++++++++++++++++");
                        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++");
                        printjson(return_value);
                    }
                }
            }
        }



        return return_value;
    }""" % dict( CATEGORIES = categories ))

    # print map_func
    # print reduce_func

    nonAtomic = True

    print "Procesando 1"
    bbva.top_clients_week.map_reduce(
        map_func,       
        reduce_func, 
        out=SON([("reduce", "top_clients_summary"), ('nonAtomic', nonAtomic)]))

    print "Procesando 2"
    bbva.top_clients_month.map_reduce(
        map_func,       
        reduce_func, 
        out=SON([("reduce", "top_clients_summary"), ('nonAtomic', nonAtomic)]))
    print "Hecho"

top_clients_summary()
