import pendulum
from numpy import round
from timeit import default_timer as timer

from ChartData import ChartData
from ChartManager import ChartManager
from swissephlib import SwissephLib
from tests import fixtures

swiss_lib = SwissephLib()
manager = ChartManager(swiss_lib)

# Test plain charts

# 2019/3/18 22:30:15 Hackensack
ldt = pendulum.datetime(2019, 3, 18, 22, 30, 15, tz='America/New_York')
udt = ldt.in_tz('UTC')
lat = 40.9792
long = -74.1169
chart = manager.create_chartdata(ldt, long, lat)
fixtures.compare_charts(chart, fixtures.transits_2019_3_18_22_30_15_Hackensack, "2019-3-18 22:30:15 NY")

# 2019/3/10 3:30:15am Melbourne
ldt = pendulum.datetime(2019, 3, 18, 22, 30, 15, tz='Australia/Melbourne')
udt = ldt.in_tz('UTC')
lat = 40.9792
long = -74.1169
chart = manager.create_chartdata(ldt, long, lat)
fixtures.compare_charts(chart, fixtures.transits_2019_3_18_22_30_15_Hackensack, "2019-3-18 22:30:15 NY")

# la = manager.create_chartdata(name, ldt, long, lat)
# manager.precess_into_sidereal_framework(radix=mike, transit_chart=la)
#
# dt = pendulum.datetime(2019, 3, 3, 6, 0, 0, tz='America/Argentina/La_Rioja')
# lat = -29.4333
# long = -66.85
#
# test = manager.create_chartdata('', dt, long, lat)
