import pendulum
from numpy import round
from timeit import default_timer as timer

from ChartData import ChartData
from ChartManager import ChartManager
from swissephlib import SwissephLib
from tests import fixtures

swiss_lib = SwissephLib()
manager = ChartManager(swiss_lib)


#  Plain charts

# 2019/3/18 22:30:15 Hackensack - Positive latitude, negative longitude
ldt = pendulum.datetime(2019, 3, 18, 22, 30, 15, tz='America/New_York')
lat = 40.9792
long = -74.1169
chart = manager.create_chartdata(ldt, long, lat)
fixtures.compare_charts(chart, fixtures.transits_2019_3_18_22_30_15_Hackensack, "2019-3-18 22:30:15 NY")

# 2019/3/10 3:30:15am Melbourne - Negative latitude, positive longitude
ldt = pendulum.datetime(2019, 3, 18, 22, 30, 15, tz='Australia/Melbourne')
lat = -37.8166
long = 144.9666
chart = manager.create_chartdata(ldt, long, lat)
fixtures.compare_charts(chart, fixtures.transits_2019_3_10_1_30_15_Melbourne, "2019-3-18 22:30:15 Melbourne, AUS")

# 2010/3/23 10:59:59am Murmansk - Latitude above arctic circle
# TODO: Cusps 2-12 do not match SF. Probably do NOT want to switch to equal houses as SF does, but double check.
ldt = pendulum.datetime(2019, 3, 23, 10, 59, 59, tz='Europe/Moscow')
lat = 68.9666
long = 33.0833
chart = manager.create_chartdata(ldt, long, lat)
fixtures.compare_charts(chart, fixtures.transits_2019_3_23_1_30_15_murmansk, "2019-3-23 10:59:59 Murmansk, RUS")

# Test return chart dates

# 2019/3/18 22:30:15 Hackensack
ldt = pendulum.datetime(2019, 3, 18, 22, 30, 15, tz='America/New_York')
lat = 40.9792
long = -74.1169
chart = manager.create_chartdata(ldt, long, lat)
return_date = pendulum.datetime(2019, 3, 24, 10, tz='America/New_York')
chart_list = manager.generate_return_list(chart, return_date, 1, 4, 20)  # Next 20 quarti-lunars

fixtures.compare_return_times(chart_list, fixtures.quarti_lunar_dates_from_2019_3_18_22_30_15_Hackensack,
                              '2019/3/18 22:30:15 Hackensack')

# 2019/3/10 3:30:15am Melbourne
# ldt = pendulum.datetime(2019, 3, 18, 22, 30, 15, tz='Australia/Melbourne')
# lat = -37.8166
# long = 144.9666
# chart = manager.create_chartdata(ldt, long, lat)
# return_date = pendulum.datetime(2019, 9, 24, 10, tz='Australia/Melbourne')
# chart_list = manager.generate_return_list(chart, return_date, 0, 36, 5)

# for x in chart_list:
#     print(x.local_datetime)

