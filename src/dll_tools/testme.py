from ctypes import *
import swissephlib
import settings

with swissephlib.SwissephLib() as s:
    jd = (s.get_julian_day(2019, 2, 27, 2.75, 1))
    st = s.get_sidereal_time_UT(jd)
    moon = (c_double * 6)()
    e = create_string_buffer(126)
    s.calculate_planets_UT(jd, 1, settings.SIDEREALMODE, moon, e)
    print(moon[0])
    print(moon[1])
print("Done")
