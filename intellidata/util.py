import datetime

def get_week_borders(week_number, year):
    january_first = datetime.datetime.strptime('%s-01-01' % year, '%Y-%m-%d')

    if january_first.weekday() == 6:
        first_sunday = january_first
    else:
        first_sunday = january_first - datetime.timedelta(days = (january_first.weekday() + 1))

    border_low  = first_sunday + datetime.timedelta(days = 7 * week_number)
    border_high = first_sunday + datetime.timedelta(days = 7 * week_number + 6)
    return border_low, border_high
