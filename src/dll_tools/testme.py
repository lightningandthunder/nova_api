import pendulum
from numpy import round
from timeit import default_timer as timer

from ChartData import ChartData
from ChartManager import ChartManager
from swissephlib import SwissephLib

swiss_lib = SwissephLib()
manager = ChartManager(swiss_lib)

name = 'Mike'
ldt = pendulum.datetime(1989, 12, 20, 22, 20, 0, tz='America/New_York')
udt = ldt.in_tz('UTC')
lat = 40.9792
long = -74.1169

mike = manager.create_chartdata(name, ldt, long, lat)

name = 'Transits in LA'
ldt = pendulum.datetime(2019, 3, 3, 22, 40, 24, tz='America/Los_Angeles')
udt = ldt.in_timezone('UTC')
lat = 34.0522
long = -118.2427

la = manager.create_chartdata(name, ldt, long, lat)
manager.precess_into_sidereal_framework(radix=mike, transit_chart=la)

dt = pendulum.datetime(2019, 3, 3, 6, 0, 0, tz='America/Argentina/La_Rioja')
lat = -29.4333
long = -66.85

test = manager.create_chartdata('', dt, long, lat)


name = 'Mike'
ldt = pendulum.datetime(1989, 12, 20, 22, 20, 0, tz='America/New_York')
udt = ldt.in_tz('UTC')
lat = 40.9792
long = -74.1169
mike = manager.create_chartdata(name, ldt, long, lat)

now = pendulum.datetime(2019, 3, 11)
start = timer()
L = manager.generate_return_list(mike, date=now, body=1, harmonic=4, return_quantity=10)
end = timer()
print(end - start)
for x in L:
    print(x.utc_datetime)
