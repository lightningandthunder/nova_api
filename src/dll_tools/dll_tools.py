from math import fabs
import pendulum
from ctypes import c_double, create_string_buffer

from dll_tools.swissephlib import SwissephLib


def calculate_harmonic_return(planet, planet_longitude, harmonic, dt_utc):

    def nearest(items, pivot):
        return min(items, key=lambda x: abs(x - pivot))

    natal_pos = planet_longitude

    startdate = dt_utc.datetime.subtract(hours=24)
    enddate = dt_utc.datetime.add(hours=24)

    period = pendulum.period(startdate, enddate)

    searchlist = [x for x in range(startdate.diff(enddate).in_seconds())]

    returnarray = (c_double * 6)()
    found = False
    while found == False:
        midpoint = len(searchlist) // 2
        errorstring = create_string_buffer(126)

        if len(searchlist) > 0:
            test_date = startdate.add(seconds=searchlist[midpoint])

            # Conversion from local time to UTC
            # This can probably just be done with pendulum
            (outyear, outmonth, outday,
                outhour, outmin, outsec) = (c_int32(), c_int32(), c_int32(),
                                            c_int32(), c_int32(), c_double())
            py_local_time_to_UTC(test_date.year, test_date.month, test_date.day,
                                    test_date.hour, test_date.minute, test_date.second,
                                    test_date.offset_hours, outyear, outmonth, outday, outhour,
                                    outmin, outsec)

            decimalhour_UTC = (((((outhour.value * 60)
                                    + outmin.value) * 60)
                                    + outsec.value) / 3600)

            # Using the new UTC time to get a correct Julian Day Number
            time_julian_day = py_get_julian_day(outyear, outmonth, outday,
                                                decimalhour_UTC, 1)

            py_calculate_planets_UT(time_julian_day, 0, SIDEREALMODE, returnarray, errorstring)

        if len(searchlist) < 2:
            print("found SSR Date! {} {} {} {} {} {}".format(test_date.year, test_date.month, test_date.day, test_date.hour, test_date.minute, test_date.second))
            return time_julian_day

        elif returnarray[0] > natal_pos:
            if fabs(returnarray[0] - natal_pos) <= 180:
                try:
                    searchlist = searchlist[:(midpoint - 1)]
                    print(len(searchlist))
                except:
                    return None
            else:
                try:
                    searchlist = searchlist[(midpoint + 1):]
                    print(len(searchlist))
                except:
                    return None

        elif returnarray[0] < natal_pos:
            if fabs(returnarray[0] - natal_pos) <= 180:
                try:
                    searchlist = searchlist[(midpoint + 1):]
                    print(len(searchlist))
                except:
                    return None
            else:
                try:
                    searchlist = searchlist[:(midpoint - 1)]
                    print(len(searchlist))
                except:
                    return None
    return None


def calculate_list_of_harmonics():
    # For SSR: find closest to entered date.
    # For SLR: Make list, starting at previous and going to X, the max number, based on harmonic chosen (2 or 4)

    pass
