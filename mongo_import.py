import os
import json
import glob

from bbvalib import create_mongoclient

DELETE_ALL   = False
TOP_CLIENTS  = False
DATA_SUMMARY = True

#############################################################################
# 
# 
#     Import flat data (regular tables)
# 
# 


def process_origin_flat():
    db = create_mongoclient()

    db.drop_collection('top_clients_week')
    db.drop_collection('top_clients_month')

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
                    db.top_clients_week.insert(cur_data)
                elif by == 'month':
                    db.top_clients_month.insert(cur_data)
                else:
                    print "Error: %s is not (month, key)" % by

def process_cube_flat():
    db = create_mongoclient()
    db.drop_collection('cube_week')
    db.drop_collection('cube_month')

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
                    db.cube_week.insert(cur_data)
                elif by == 'month':
                    db.cube_month.insert(cur_data)
                else:
                    print "Error: %s is not in (week, month)" % by

def process_patterns_flat():
    db = create_mongoclient()
    db.drop_collection('patterns_month')

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
                db.patterns_month.insert(cur_data)


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

    db = create_mongoclient()
    db.drop_collection('top_clients_summary')

    categories = db.top_clients_week.find().distinct('category')
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
                            if (date == 'total')
                                continue;

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

    nonAtomic = False

    print "Procesando 1"
    db.top_clients_week.map_reduce(
        map_func,       
        reduce_func, 
        out=SON([("reduce", "top_clients_summary"), ('nonAtomic', nonAtomic)]))

    print "Procesando 2"
    db.top_clients_month.map_reduce(
        map_func,       
        reduce_func, 
        out=SON([("reduce", "top_clients_summary"), ('nonAtomic', nonAtomic)]))
    print "Hecho"



if TOP_CLIENTS:
    top_clients_summary()


def data_summary():
    from bson.code import Code
    from bson.son import SON

    db = create_mongoclient()
    db.drop_collection('data_summary')

    categories = db.cube_month.find().distinct('category')
    categories = json.dumps(categories)

    shared_code = """
        var MIN = 100000000000;

        var deepcopy = function (obj) {
            return JSON.parse(JSON.stringify(obj));
        }

        // Auxiliar data

        var self = this;

        var empty_summary = function() {
            return {
                            'avg' : 0.0,
                            'num_payments' : 0,
                            'min' : MIN,
                            'max' : 0,
                            'total' : 0.0,
                            'hours' : {
                                // 08 : ...
                            }
            };
        };

        var empty_cube_data = function() {
            return {
                'avg'          : 0,
                'num_cards'    : 0,
                'num_payments' : 0,
                'total'        : 0
            };
        };

        var empty_total_cube_data = function() {
            return {
                'avg'          : 0,
                'num_payments' : 0,
                'total'        : 0
            };
        };


        var empty_cube = function() { 
            return {
                'total' : {
                    'per_age' : {
                        '1' : empty_total_cube_data(),
                        '2' : empty_total_cube_data(),
                        '3' : empty_total_cube_data(),
                        '4' : empty_total_cube_data(),
                        '5' : empty_total_cube_data(),
                        '6' : empty_total_cube_data(),
                        'U' : empty_total_cube_data()
                    },
                    'per_gender' : {
                        'male'       : empty_total_cube_data(),
                        'female'     : empty_total_cube_data(),
                        'enterprise' : empty_total_cube_data()
                    }
                },
                'cubes' : {
                    'male' : {
                        '1' : empty_cube_data(),
                        '2' : empty_cube_data(),
                        '3' : empty_cube_data(),
                        '4' : empty_cube_data(),
                        '5' : empty_cube_data(),
                        '6' : empty_cube_data(),
                        'U' : empty_cube_data()
                    },
                    'female' : {
                        '1' : empty_cube_data(),
                        '2' : empty_cube_data(),
                        '3' : empty_cube_data(),
                        '4' : empty_cube_data(),
                        '5' : empty_cube_data(),
                        '6' : empty_cube_data(),
                        'U' : empty_cube_data()
                    },
                    'enterprise' : {
                        'U' : empty_cube_data()
                    }
                }
            }; 
        };



        // 
        // We have an empty value
        // 
        var value = {};

        //
        // We fill the fields (empty categories)
        // 
        value['categories'] = {};
        %(CATEGORIES)s.forEach(function(category){
            value['categories'][category] = {
                'months' : {},
                'weeks'  : {},
                'total'  : {
                    'days'  : {},
                    'total' : empty_summary()
                }
            }
        });
        
        // 
        // We fill the fields (total)
        value['total'] = {
            'days'  : {},
            'total' : empty_summary()
        };


    """ % dict(CATEGORIES = categories)


    map_patterns_func = Code("""function () {
        %(SHARED)s
        // Precalculation of hours
        var hours_data = {};
        this.hours.forEach(function(hour_data) {
            hours_data[hour_data['hour']] = {
                'std'          : hour_data['std'],
                'min'          : hour_data['min'],
                'max'          : hour_data['max'],
                'num_cards'    : hour_data['num_cards'],
                'mode'         : hour_data['mode'],
                'num_payments' : hour_data['num_payments'],
                'avg'          : hour_data['avg'],
                'total'        : hour_data['num_payments'] * hour_data['avg']
            }
        });

        // And now, we fill the real data.
        value['categories'][self.category]['months'][self.month] = {
            'days'  : {},
            'cubes' : empty_cube(),
            'total' : empty_summary()
        };
        
        value['categories'][self.category]['months'][self.month]['days'][self.day] = {
            'avg' : self.avg,
            'std' : self.std,
            'num_payments' : self.num_payments,
            'min' : self.min,
            'max' : self.max,
            'num_cards' : self.num_cards,
            'mode' : self.mode,
            'hours' : hours_data,
            'total' : self.avg * self.num_payments
        };

        value['categories'][self.category]['months'][self.month]['total'] = {
            'avg' : self.avg,
            'num_payments' : self.num_payments,
            'min' : self.min,
            'max' : self.max,
            'total' : self.avg * self.num_payments,
            'hours' : {}
        };
        for (var hour in hours_data) {
            var cur_hour_data = hours_data[hour];
            value['categories'][self.category]['months'][self.month]['total']['hours'][hour] = {
                'min'          : cur_hour_data['min'],
                'max'          : cur_hour_data['max'],
                'num_payments' : cur_hour_data['num_payments'],
                'avg'          : cur_hour_data['avg'],
                'total'        : cur_hour_data['num_payments'] * cur_hour_data['avg']
            };
        }

        value['categories'][self.category]['total']['days'][self.day] = {
            'avg' : self.avg,
            'num_payments' : self.num_payments,
            'min' : self.min,
            'max' : self.max,
            'hours' : hours_data,
            'total' : self.avg * self.num_payments
        };

        var summary_total = function() {
            return {
                'avg'          : self.avg,
                'num_payments' : self.num_payments,
                'min'          : self.min,
                'max'          : self.max,
                'hours'        : hours_data,
                'total'        : self.avg * self.num_payments
            };
        };

        value['categories'][self.category]['total']['total'] = summary_total();

        value['total']['days'][self.day] = summary_total(); 
        value['total']['total'] = summary_total(); 

        emit(this.shop_zipcode, value);
    }""" % dict(
        CATEGORIES = categories,
        SHARED     = shared_code
    ))

    reduce_func = Code("""function (key, values) {
        %(SHARED)s

        // Take the initial value, and fill it with the easy data
        var reduced_value = value;

        var mergeTotalTotal = function (other_total, me_total) {
            if (other_total['hours'] == undefined ) {
                print("Expected total structure as first argument. Got:");
                printjson(other_total);
                throw new Error("Expected total structure as first argument. See the logs.");
            } else if (me_total['hours'] == undefined ) {
                print("Expected total structure as second argument. Got:");
                printjson(me_total);
                throw new Error("Expected total structure as second argument. See the logs.");
            }
            

            // First, the basic data
            var total        = other_total['total'] + me_total['total'];
            var num_payments = other_total['num_payments'] + me_total['num_payments'];
            var avg;
            if (num_payments == 0)
                avg = 0.0;
            else
                avg = 1.0 * total / num_payments;

            other_total['total'] = total;
            other_total['avg']   = avg;
            other_total['num_payments'] = num_payments;

            if (me_total['min'] < other_total['min'])
                other_total['min'] = me_total['min'];
            if (me_total['max'] > other_total['max'])
                other_total['max'] = me_total['max'];

            // And now the hours:
            for (var hour in me_total['hours'] ){
                // If the hours do no exist, copy them
                if (other_total['hours'][hour] == undefined) {
                    other_total['hours'][hour] = deepcopy(me_total['hours'][hour]);
                } else {
                    // Otherwise, merge
                    var other_hour = other_total['hours'][hour];
                    var me_hour    = me_total['hours'][hour];

                    var total        = other_hour['total'] + me_hour['total'];
                    var num_payments = other_hour['num_payments'] + me_hour['num_payments'];
                    var avg;
                    if (num_payments == 0)
                        avg = 0.0;
                    else
                        avg = 1.0 * total / num_payments;

                    other_hour['total'] = total;
                    other_hour['avg']   = avg;
                    other_hour['num_payments'] = num_payments;

                    if (me_hour['min'] < other_hour['min'])
                        other_hour['min'] = me_hour['min'];
                    if (me_hour['max'] > other_hour['max'])
                        other_hour['max'] = me_hour['max'];                           
                }
            }
        };

         var mergeTotalDays = function(other_days, me_days) {
            for (var day in me_days) {
                // If the day does not exist, copy it
                if (other_days[day] == undefined) {
                    other_days[day] = deepcopy(me_days[day]);
                } else {
                    // Otherwise, merge each day
                    mergeTotalTotal(other_days[day], me_days[day]);
                }
            }
        };       
        // Take all values, and merge them one by one in reduced_value
        values.forEach(function(value) {
            // First, merge categories
            %(CATEGORIES)s.forEach(function(category) {
                // Take the data to be merged
                var me_category = value['categories'][category];
                var other_category = reduced_value['categories'][category];

                // First, merge months
                for (var month in me_category['months']) {
                    // If the month doesn't exist in reduced_value, copy it
                    if (other_category['months'][month] == undefined) {
                        other_category['months'][month] = deepcopy(me_category['months'][month]);
                        continue;
                    }
                    // Otherwise, merge. 
                    var me_month = me_category['months'][month];
                    var other_month = other_category['months'][month];

                    // First, days
                    for (var day in me_month['days']) {
                        // If day does not exist, or it exists but it's empty, copy it
                        if (other_month['days'][day] == undefined || other_month['days'][day]['num_cards'] < 1) {
                            other_month['days'][day] = deepcopy(me_month['days'][day]);
                            continue;
                        } else {
                            // If the other data is not empty but this data is
                            // empty, skip it.
                            if (me_month['days'][day]['num_cards'] < 1) {
                                continue;
                            }
                            // It's impossible that the days are replicated, since 
                            // for a zipcode::category::month::day, there is a single set 
                            // of data. If this happens, we're summing information
                            // twice, which is an error.
                            print("Replicated data found. shop_zipcode " + key + ", category " + category + ", month " + month + ", day " + day + " already had data. See the logs for comparison.");
                            printjson(other_month['days'][day]);
                            printjson(me_month['days'][day]);
                            throw new Error("Replicated data found. shop_zipcode " + key + ", category " + category + ", month " + month + ", day " + day + " already had data. See the logs for comparison.");
                        }
                    }

                    // Then, cubes. 
                    // First cubes/cubes
                    for (var gender in me_month['cubes']['cubes']) {
                        // If the gender doesn't exist, copy it
                        if (other_month['cubes']['cubes'][gender] == undefined) {
                            other_month['cubes']['cubes'][gender] = deepcopy(me_month['cubes']['cubes'][gender]);
                            continue;
                        } else {
                            // Merge a gender, age (except for total)
                            for (var age in me_month['cubes']['cubes'][gender]) {
                                // If the age doesn't exist or it's empty, copy it
                                if (other_month['cubes']['cubes'][gender][age] == undefined || other_month['cubes']['cubes'][gender][age]['num_cards'] < 1) {
                                    other_month['cubes']['cubes'][gender][age] = deepcopy(me_month['cubes']['cubes'][gender][age]);
                                    continue;        
                                } else {
                                    // If the existing data has something and the 
                                    // current data is empty, just skip this one.
                                    if (me_month['cubes']['cubes'][gender][age]['num_cards'] < 1) {
                                        continue;
                                    }
                                    // It's impossible that this particular exist is replicated
                                    // since for a zipcode::category::month::cubes::gender::age there is a 
                                    // single registry.
                                    print("Replicated data found. shop_zipcode " + key + ", category " + category + ", month " + month + ", cube (gender = " + gender + ", age = " + age + ") already had data. See the logs for comparison");
                                    printjson(other_month['cubes']['cubes'][gender][age]);
                                    printjson(me_month['cubes']['cubes'][gender][age]);
                                    throw new Error("Replicated data found. shop_zipcode " + key + ", category " + category + ", month " + month + ", cube (gender = " + gender + ", age = " + age + ") already had data. See the logs for comparison");
                                }
                            }
                        }
                    }

                    // Then, cubes/total. First cubes/total/per_age
                    var other_per_age = other_month['cubes']['total']['per_age'];
                    var me_per_age   = me_month['cubes']['total']['per_age'];
                    for (var age in me_per_age) {
                        // If the existing is empty or does not exist, copy it
                        if (other_per_age[age] == undefined) {
                            other_per_age[age] = deepcopy(me_per_age[age]);
                        } else {
                            // Otherwise, merge
                            var total        = other_per_age[age]['total'] + me_per_age[age]['total'];
                            var num_payments = other_per_age[age]['num_payments'] + me_per_age[age]['num_payments'];
                            var avg;
                            if (num_payments == 0)
                                avg = 0.0;
                            else
                                avg = 1.0 * total / num_payments;
                            other_per_age[age]['total']        = total;
                            other_per_age[age]['num_payments'] = num_payments;
                            other_per_age[age]['avg']          = avg;
                        }
                    }
                    

                    // Then cubes/total/per_gender
                    var other_per_gender = other_month['cubes']['total']['per_gender'];
                    var me_per_gender    = me_month['cubes']['total']['per_gender'];
                    for (var gender in me_per_gender) {
                        // If the existing is empty or does not exist, copy it
                        if (other_per_gender[gender] == undefined) {
                            other_per_gender[gender] = deepcopy(me_per_gender[gender]);
                        } else {
                            // Otherwise, merge
                            var total        = other_per_gender[gender]['total'] + me_per_gender[gender]['total'];
                            var num_payments = other_per_gender[gender]['num_payments'] + me_per_gender[gender]['num_payments'];
                            var avg;
                            if (num_payments == 0)
                                avg = 0.0;
                            else
                                avg = 1.0 * total / num_payments;
                            other_per_gender[gender]['total']        = total;
                            other_per_gender[gender]['num_payments'] = num_payments;
                            other_per_gender[gender]['avg']          = avg;
                        }
                    }

                    // Then, merge month/total.
                    // print("Calling total from category/month/total/total");
                    mergeTotalTotal(other_month['total'], me_month['total']);
                }

                // Then, merge weeks
                // (Not done yet). TODO

                // Then, merge category/total:
                // print("Calling days from category/total/days");
                mergeTotalDays(other_category['total']['days'], me_category['total']['days']);
                // print("Calling total from category/total/total");
                mergeTotalTotal(other_category['total']['total'], me_category['total']['total']);
            });

            // Then, merge total
            // print("Calling days from total");
            mergeTotalDays(reduced_value['total']['days'], value['total']['days']);
            // print("Calling total from total");
            mergeTotalTotal(reduced_value['total']['total'], value['total']['total']);
        });
        

        return reduced_value;
    }""" % dict( CATEGORIES = categories, SHARED = shared_code ))

    # dummy_reduce = Code("""function(key, values) { return values[0] }""")
    # reduce_func = dummy_reduce

    # print map_patterns_func
    # print reduce_func

    nonAtomic = False

    print "Procesando 1"
    db.patterns_month.map_reduce(
        map_patterns_func,
        reduce_func, 
        out=SON([("reduce", "data_summary"), ('nonAtomic', nonAtomic)]))

    print "Hecho"

if DATA_SUMMARY:
    data_summary()

