from ctypes import *
import swissephlib
from ChartData import ChartData
import pendulum

import settings

# with swissephlib.SwissephLib() as s:
#     jd = (s.get_julian_day(2019, 2, 27, 2.75, 1))
#     st = s.get_sidereal_time_UT(jd)
#     moon = (c_double * 6)()
#     e = create_string_buffer(126)
#     s.calculate_planets_UT(jd, 1, settings.SIDEREALMODE, moon, e)
#     print(moon[0])
#     print(moon[1])
# print("Done")

name = 'Mike'
ldt = pendulum.datetime(2019, 2, 27, 20, 31, 0, tz='America/New_York')
udt = pendulum.datetime(2019, 2, 28, 1, 31, 0)
lat = 40.9958
long = -74.0435

chart = ChartData(name, ldt, udt, long, lat)
x = chart.get_ecliptical_coords()
for y, z in x.items():
    print(y, z)

print("\n")

a = chart.get_mundane_coords()
for b, c in a.items():
    print(b, c)

print("\n")

d = chart.get_right_ascension_coords()
for e, f in d.items():
    print(e, f)
