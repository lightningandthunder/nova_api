from ctypes import c_int, c_int32, c_double, create_string_buffer
from ctypes.wintypes import *
import math
import os
import pendulum
import calendar
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim

from . import settings


def get_sign(longitude):
    """Determine zodiacal sign from unsigned longitude"""

    zodiac = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
              "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
    key = int(longitude / 30)
    return zodiac[key]


def get_orb(longitude_one, longitude_two, lowbound, highbound):  # TODO: test revised code
    """Return the orb, or distance from exact, of an aspect"""

    aspect = math.fabs(longitude_one - longitude_two)

    # Catch situations where one longitude is near 360* and the other is near 0*
    aspect360 = math.fabs(aspect - 360)
    aspect_average = (lowbound + highbound) / 2

    if lowbound <= aspect <= highbound:
        return math.fabs(aspect - aspect_average) if lowbound != 0 else aspect

    elif lowbound <= aspect360 <= highbound:
        return math.fabs(aspect360 - aspect_average) if lowbound != 0 else aspect360



# Stopped editing here

def get_solar_return_julian_day(natal_classname, return_classname):
    """Calculate the Julian Day for a solar return within several seconds of accuracy"""

    natal_pos = natal_classname.planet_dictionary["Sun"][0]

    startdate = return_classname.datetime.subtract(hours=24)
    enddate = return_classname.datetime.add(hours=24)

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
            found = True
            return_classname.datetime = test_date
            print("found SSR Date! {} {} {} {} {} {}".format(test_date.year, test_date.month, test_date.day,
                                                             test_date.hour, test_date.minute, test_date.second))
            return time_julian_day

        elif returnarray[0] > natal_pos:
            if math.fabs(returnarray[0] - natal_pos) <= 180:
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
            if math.fabs(returnarray[0] - natal_pos) <= 180:
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


def old_get_lunar_return_julian_day(natal_classname, return_classname, startdate, enddate, type_lunar_return):
    """Acquires lunar return Julian Day number to hour and then second accuracy"""

    if type_lunar_return == "Lunar Return":
        natal_pos = natal_classname.planet_dictionary["Moon"][0]
    elif type_lunar_return == "Demi-Lunar Return":
        natal_pos = (natal_classname.planet_dictionary["Moon"][0] + 180) % 360

    print("Radical Moon: {}".format(natal_pos))

    if startdate.diff(enddate).in_days() >= 1:
        found = False
        searchlist = [x for x in range(startdate.diff(enddate).in_hours())]
        returnarray = (c_double * 6)()

        while found == False:
            midpoint = len(searchlist) // 2
            errorstring = create_string_buffer(126)

            if len(searchlist) > 0:
                test_date = startdate.add(hours=searchlist[midpoint])

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

                py_calculate_planets_UT(time_julian_day, 1, SIDEREALMODE, returnarray, errorstring)

            if len(searchlist) < 2:
                # The moon moves about 13.2 degrees per hour
                if returnarray[0] > natal_pos or (returnarray[0] <= 14 and natal_pos >= 346):
                    test_date = test_date.subtract(hours=1)
                    return_classname.datetime = test_date
                    found = True
                    break
                else:
                    return_classname.datetime = test_date
                    found = True
                    break

            elif returnarray[0] > natal_pos or (returnarray[0] <= 14 and natal_pos >= 346):
                try:
                    searchlist = searchlist[:(midpoint - 1)]
                except:
                    return None

            else:
                try:
                    searchlist = searchlist[(midpoint + 1):]
                except:
                    return None

    # 3,600 seconds per hour
    searchlist = [x for x in range(3610)]

    found = False
    while found == False:
        midpoint = len(searchlist) // 2
        returnarray = (c_double * 6)()
        errorstring = create_string_buffer(126)

        if len(searchlist) > 0:
            test_date = return_classname.datetime.add(seconds=searchlist[midpoint])

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

            py_calculate_planets_UT(time_julian_day, 1, SIDEREALMODE, returnarray, errorstring)

        # base case: the most accurate time identifiable down to about a second of real time
        if len(searchlist) < 2:
            # if math.fabs(returnarray[0] - natal_pos) <= 1 or math.fabs((returnarray[0] - natal_pos) - 360) <= 1:
            found = True
            return_classname.datetime = test_date
            print("Julian day search complete!")
            return time_julian_day
        # else:
        #    raise IndexError("Unable to identify accurate date!")

        elif returnarray[0] > natal_pos or (returnarray[0] <= 14 and natal_pos >= 346):
            try:
                searchlist = searchlist[:(midpoint - 1)]
            except:
                return None

        else:
            try:
                searchlist = searchlist[(midpoint + 1):]
            except:
                return None

    return None


def get_lunar_return_julian_day(natal_classname, return_classname, startdate, enddate, type_lunar_return):
    """Acquires lunar return Julian Day number with accuracy within several seconds"""

    if type_lunar_return == "SLR":
        natal_pos = natal_classname.planet_dictionary["Moon"][0]
    elif type_lunar_return == "DSLR":
        natal_pos = (natal_classname.planet_dictionary["Moon"][0] + 180) % 360

    print("Radical Moon: {}".format(natal_pos))

    searchlist = [x for x in range(startdate.diff(enddate).in_seconds())]
    print("Size of search list... {}".format(len(searchlist)))
    returnarray = (c_double * 6)()
    test_date = startdate
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

            py_calculate_planets_UT(time_julian_day, 1, SIDEREALMODE, returnarray, errorstring)

        # base case: the most accurate time identifiable down to about a second of real time
        if len(searchlist) < 2:
            print("Settled on: {}".format(returnarray[0]))
            if math.fabs(natal_pos - returnarray[0]) <= 4 or math.fabs(natal_pos - returnarray[0] - 360) <= 4:
                found = True
                return_classname.datetime = test_date
                print("Julian day search complete!")
                return time_julian_day
            else:
                return (get_lunar_return_julian_day(natal_classname, return_classname,
                                                    startdate.add(days=14), enddate.add(days=14), type_lunar_return))

        elif returnarray[0] > natal_pos:
            if math.fabs(returnarray[0] - natal_pos) <= 180:
                try:
                    searchlist = searchlist[:(midpoint - 1)]
                    print(len(searchlist))
                    print("Testing... {}".format(returnarray[0]))
                except:
                    return None
            else:
                try:
                    searchlist = searchlist[(midpoint + 1):]
                    print(len(searchlist))
                    print("Testing... {}".format(returnarray[0]))
                except:
                    return None

        elif returnarray[0] < natal_pos:
            if math.fabs(returnarray[0] - natal_pos) <= 180:
                try:
                    searchlist = searchlist[(midpoint + 1):]
                    print(len(searchlist))
                    print("Testing... {}".format(returnarray[0]))
                except:
                    return None
            else:
                try:
                    searchlist = searchlist[:(midpoint - 1)]
                    print(len(searchlist))
                    print("Testing... {}".format(returnarray[0]))
                except:
                    return None

    return None


def get_sp_julian_day(natal_classname, prog_date):
    """Calculate the Julian Day number to use for Q2 secondary progressions"""

    # prog_offset = natal_classname.datetime.diff(prog_date).in_minutes() * Q2
    # prog_calendar_day = natal_classname.datetime.add(minutes=prog_offset)
    # prog_jul_day = py_get_julian_day(prog_calendar_day.year, prog_calendar_day.month, prog_calendar_day.hour, 1)
    # return prog_jul_day

    pass


def get_LST(year, month, day, decimalhour, timezone, decimal_longitude):
    """Calculate local sidereal time for date, time, location of event"""

    # Julian Day number for midnight
    julian_day_0_GMT = py_get_julian_day(year, month, day, 0, 1)

    # Local time converted to UT/GMT
    universal_time = (decimalhour - timezone)

    # Sidereal time for the Julian day number, at midnight
    sidereal_time_0_GMT = (julian_day_0_GMT - 2451545.0) / 36525.0

    # "LST" for the Greenwich Meridian, not local yet
    greenwich_sidereal_time = (6.697374558
                               + (2400.051336 * sidereal_time_0_GMT)
                               + (0.000024862
                                  * (math.pow(sidereal_time_0_GMT, 2)))
                               + (universal_time * 1.0027379093))

    local_sidereal_time = ((greenwich_sidereal_time
                            + (decimal_longitude / 15)) % 24)

    if local_sidereal_time < 0:
        local_sidereal_time += 24

    return local_sidereal_time


def parse_aspect(pname1, plong1, pname2, plong2, aspect_category):
    """Check two longitudes for a valid aspect; return as a string if found"""

    if pname1 == pname2:
        return None

    orb = 0
    tier = None
    aspect_type = ""

    # Case: conjunction
    if get_orb(plong1, plong2, 0, 10) != None:
        aspect_type = "Cnj"
        orb = get_orb(plong1, plong2, 0, 10)
        if orb <= 1:
            tier = 0
        if orb <= 4:
            tier = 1
        elif orb <= 7:
            tier = 2
        elif orb <= 10:
            tier = 3
        priority_placeholder = get_priority(pname1, pname2, tier, aspect_type, (orb / 5))
    else:
        pass

    # Case: opposition
    if get_orb(plong1, plong2, 170, 190) != None:
        aspect_type = "Opp"
        orb = (get_orb(plong1, plong2, 170, 190) % 180)
        if orb <= 1:
            tier = 0
        if orb <= 4:
            tier = 1
        elif orb <= 7:
            tier = 2
        elif orb <= 10:
            tier = 3
        priority_placeholder = get_priority(pname1, pname2, tier, aspect_type, (orb / 5))
    else:
        pass

    # Case: square
    if get_orb(plong1, plong2, 82.5, 97.5) != None:
        aspect_type = "Sqr"
        orb = (get_orb(plong1, plong2, 82.5, 97.5) % 90)
        if orb <= 1:
            tier = 0
        if orb <= 3:
            tier = 1
        elif orb <= 6:
            tier = 2
        elif orb <= 7.5:
            tier = 3
        priority_placeholder = get_priority(pname1, pname2, tier, aspect_type, (orb / 4.8))
    else:
        pass

    # Case: trine
    if get_orb(plong1, plong2, 115, 125) != None:
        aspect_type = "Tri"
        orb = (get_orb(plong1, plong2, 115, 125) % 120)
        if orb <= 1:
            tier = 0
        if orb <= 3:
            tier = 1
        elif orb <= 5:
            tier = 2
        else:
            tier = None
        priority_placeholder = get_priority(pname1, pname2, tier, aspect_type, (orb / 4.5))
    else:
        pass

    # Case: sextile
    if get_orb(plong1, plong2, 55, 65) != None:
        aspect_type = "Sxt"
        orb = (get_orb(plong1, plong2, 55, 65) % 60)
        if orb <= 1:
            tier = 0
        if orb <= 3:
            tier = 1
        elif orb <= 5:
            tier = 2
        else:
            tier = None
        priority_placeholder = get_priority(pname1, pname2, tier, aspect_type, (orb / 4.5))
    else:
        pass

    # Case: semisquare
    if get_orb(plong1, plong2, 43, 47) != None:
        aspect_type = "Sms"
        orb = (get_orb(plong1, plong2, 43, 47) % 45)
        if orb <= 1:
            tier = 0
        if orb <= 2:
            tier = 1
        else:
            tier = None
        priority_placeholder = get_priority(pname1, pname2, tier, aspect_type, (orb / 3.5))
    else:
        pass

    # Case: sesquisquare
    if get_orb(plong1, plong2, 133, 137) != None:
        aspect_type = "Ssq"
        orb = (get_orb(plong1, plong2, 133, 137) % 135)
        if orb <= 1:
            tier = 0
        if orb <= 2:
            tier = 1
        else:
            tier = None
        priority_placeholder = get_priority(pname1, pname2, tier, aspect_type, (orb / 3.5))
    else:
        pass

    if orb != 0 and tier is not None:
        returnvalue = []
        orb_deg = math.trunc(orb)
        orb_min = math.trunc((orb - (math.trunc(orb))) * 60)

        if aspect_category == "Natal":
            returnvalue += pname1 + " " + aspect_type + " " + pname2 + " " + str(orb_deg) + "* " + str(orb_min) + "'"

        elif aspect_category == "SSR to Natal":
            if orb_deg < 6 and aspect_type in ["Cnj", "Opp", "Sqr", "Sms",
                                               "Ssq"] and pname1 != "Sun" and pname2 not in ANGLES:
                returnvalue += "t. " + pname1 + " " + aspect_type + " " + "r. " + pname2 + " " + str(
                    orb_deg) + "* " + str(orb_min) + "'"
            elif ((orb_deg * 60) + orb_min <= 70) and aspect_type == "Cnj" and pname1 != "Sun" and pname2 in ANGLES:
                returnvalue += "t. " + pname1 + " " + aspect_type + " " + "r. " + pname2 + " " + str(
                    orb_deg) + "* " + str(orb_min) + "'"
            else:
                priority_placeholder = 0
                return None
            if pname1 == "Moon":
                priority_placeholder += 0.5

        elif aspect_category == "SLR to Natal":
            if orb_deg < 6 and aspect_type in ["Cnj", "Opp", "Sqr", "Sms",
                                               "Ssq"] and pname1 != "Moon" and pname2 not in ANGLES:
                returnvalue += "t. " + pname1 + " " + aspect_type + " " + "r. " + pname2 + " " + str(
                    orb_deg) + "* " + str(orb_min) + "'"
            elif ((orb_deg * 60) + orb_min <= 70) and aspect_type == "Cnj" and pname1 != "Moon" and pname2 in ANGLES:
                returnvalue += "t. " + pname1 + " " + aspect_type + " " + "r. " + pname2 + " " + str(
                    orb_deg) + "* " + str(orb_min) + "'"
            else:
                priority_placeholder = 0
                return None
            if pname1 == "Sun":
                priority_placeholder += 0.5

        elif aspect_category == "Transit to Transit":
            if orb_deg < 6:
                returnvalue += "t. " + pname1 + " " + aspect_type + " " + "t. " + pname2 + " " + str(
                    orb_deg) + "* " + str(orb_min) + "'"
                if (pname1 or pname2) == ("Sun" or "Moon"):
                    priority_placeholder += 0.5
            else:
                return None

        elif aspect_category == "Transit to Natal":
            if (orb_deg < 1 and (pname1 != "Moon" and (
                    pname2 not in ANGLES and (aspect_type in ["Cnj", "Opp", "Sqr", "Sms", "Ssq"])))):
                returnvalue += "t. " + pname1 + " " + aspect_type + " " + "r. " + pname2 + " " + str(
                    orb_deg) + "* " + str(orb_min) + "'"
                if pname1 in ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
                    priority_placeholder += 0.5
                elif pname1 in ["Mercury", "Venus"]:
                    priority_placeholder -= 0.5
            elif (orb_deg < 1 and (pname1 != "Moon" and (pname2 in ANGLES and (aspect_type == "Cnj")))):
                returnvalue += "t. " + pname1 + " " + aspect_type + " " + "r. " + pname2 + " " + str(
                    orb_deg) + "* " + str(orb_min) + "'"
                if pname1 in ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
                    priority_placeholder += 0.5
                elif pname1 in ["Mercury", "Venus"]:
                    priority_placeholder -= 0.5
            else:
                return None

        elif aspect_category == "Transit to Local":
            if (orb_deg < 1 and (pname1 != "Moon" and (pname2 in ANGLES and (aspect_type == "Cnj")))):
                returnvalue += "t. " + pname1 + " " + aspect_type + " " + "l. " + pname2 + " " + str(
                    orb_deg) + "* " + str(orb_min) + "'"
                if pname1 in ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
                    priority_placeholder += 0.5
                elif pname1 in ["Mercury", "Venus"]:
                    priority_placeholder -= 0.5
            else:
                return None

        elif aspect_category == "Transit to SSR":
            if (orb_deg < 1 and (pname1 != "Moon" and (
                    pname2 not in ANGLES and (aspect_type in ["Cnj", "Opp", "Sqr", "Sms", "Ssq"])))):
                returnvalue += "t. " + pname1 + " " + aspect_type + " " + "s. " + pname2 + " " + str(
                    orb_deg) + "* " + str(orb_min) + "'"
                if pname1 in ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
                    priority_placeholder += 0.5
                elif pname1 in ["Mercury", "Venus"]:
                    priority_placeholder -= 0.5
            elif (orb_deg < 1 and (pname1 != "Moon" and (pname2 in ANGLES and (aspect_type == "Cnj")))):
                returnvalue += "t. " + pname1 + " " + aspect_type + " " + "s. " + pname2 + " " + str(
                    orb_deg) + "* " + str(orb_min) + "'"
                if pname1 in ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
                    priority_placeholder += 0.5
                elif pname1 in ["Mercury", "Venus"]:
                    priority_placeholder -= 0.5
            else:
                return None

        elif aspect_cateogry == "Transit to SP":
            pass

        aspect_return = "".join(returnvalue)
        return (priority_placeholder, aspect_return)
    else:
        return None


def convert_decimal_to_dms(decimal):
    degree = int(decimal)
    minute = int(math.fabs((decimal - degree) * 60))
    second = int((math.fabs((decimal - degree) * 60) - int(math.fabs((decimal - degree) * 60))) * 60)
    return (degree, minute, second)


# The calculate_ functions flesh out chart data for a specific chart instance

def calculate_mundane_positions(planet_latitude, planet_longitude,
                                LST, obliquity, decimal_svp,
                                decimal_geolat, planet_pvl):
    """Calculate a planet's prime vertical longitude"""

    # Variable names reference the original angularity spreadsheet.
    # Most do not have official names and are intermediary values used elsewhere.

    ramc = LST * 15

    calc_ax = (math.cos(math.radians(planet_longitude
                                     + (360 - (330 + decimal_svp)))))

    precessed_declination = (math.degrees(math.asin
                                          (math.sin(math.radians(planet_latitude))
                                           * math.cos(math.radians(obliquity))
                                           + math.cos(math.radians(planet_latitude))
                                           * math.sin(math.radians(obliquity))
                                           * math.sin(math.radians(planet_longitude
                                                                   + (360 - (330 + decimal_svp)))))))

    calc_ay = (math.sin(math.radians((planet_longitude
                                      + (360 - (330 + decimal_svp)))))
               * math.cos(math.radians(obliquity))
               - math.tan(math.radians(planet_latitude))
               * math.sin(math.radians(obliquity)))

    calc_ayx_deg = math.degrees(math.atan(calc_ay / calc_ax))

    precessed_right_ascension = None
    if (calc_ax < 0):
        precessed_right_ascension = calc_ayx_deg + 180
    else:
        if (calc_ay < 0):
            precessed_right_ascension = calc_ayx_deg + 360
        else:
            precessed_right_ascension = calc_ayx_deg

    hour_angle_degree = ramc - precessed_right_ascension

    calc_cz = (math.degrees(math.atan(1
                                      / (math.cos(math.radians(decimal_geolat))
                                         / math.tan(math.radians(hour_angle_degree))
                                         + math.sin(math.radians(decimal_geolat))
                                         * math.tan(math.radians(precessed_declination))
                                         / math.sin(math.radians(hour_angle_degree))))))

    calc_cx = (math.cos(math.radians(decimal_geolat))
               * math.cos(math.radians(hour_angle_degree))
               + math.sin(math.radians(decimal_geolat))
               * math.tan(math.radians(precessed_declination)))

    campanus_longitude = ()
    if (calc_cx < 0):
        campanus_longitude = 90 - calc_cz
    else:
        campanus_longitude = 270 - calc_cz

    planet_pvl[0] = (int(campanus_longitude / 30) + 1)
    planet_pvl[1] = campanus_longitude
    return None


def calculate_houses(julian_day_number, geolatitude, geolongitude,
                     classname):
    """Calculate house cusps and ecliptical longitudes of angles in the Campanus system"""

    # Swiss Ephemeris documentation specifies 8 doubles for houses, 13 for cusps
    cusp_array = (c_double * 13)()
    house_array = (c_double * 8)()
    py_calculate_houses(julian_day_number, SIDEREALMODE,
                        geolatitude, geolongitude, CAMPANUS,
                        cusp_array, house_array)
    classname.angles["Asc"] = house_array[0]
    classname.angles["MC"] = house_array[1]
    classname.angles["Dsc"] = (house_array[0] + 180) % 360
    classname.angles["IC"] = (house_array[1] + 180) % 360
    classname.angles["Eq Asc"] = house_array[4]
    classname.angles["Eq Dsc"] = (house_array[4] + 180) % 360
    classname.angles["EP (Ecliptical)"] = (classname.angles["MC"] + 90) % 360
    classname.angles["Zen"] = (classname.angles["Dsc"] + 90) % 360
    classname.angles["WP (Ecliptical)"] = (classname.angles["IC"] + 90) % 360
    classname.angles["Ndr"] = (classname.angles["Asc"] + 90) % 360

    return None


def calculate_foreground_planets(classname):
    """Calculate foreground and background planets, and return as a tuple"""

    # These lists will actually be printed to the document
    foregroundlist = []
    backgroundlist = []

    # Possible house locations that would make a planet foreground
    primary_angles = {
        "Asc": (12, 1),
        "MC": (9, 10),
        "Dsc": (6, 7),
        "IC": (3, 4)
    }
    secondary_angles = ["Eq Asc", "Eq Dsc", "EP (Ecliptical)", "Zen", "WP (Ecliptical)", "Ndr"]
    background_angles = [(2, 3), (5, 6), (8, 9), (11, 12)]

    # Planet proximity to primary angles, measured in prime vertical longitude
    for angle in primary_angles.keys():
        for planet in classname.mundane_positions.keys():
            house = classname.mundane_positions[planet][0]
            longitude = classname.mundane_positions[planet][1] % 30
            if ((house == primary_angles[angle][0] and longitude >= 20)
                    or (house == primary_angles[angle][1] and longitude <= 10)):

                if longitude >= 20:
                    orb = math.fabs(longitude - 30)
                else:
                    orb = longitude
                returnvalue = []
                orb_deg = math.trunc(orb)
                orb_min = math.trunc((orb - (math.trunc(orb))) * 60)
                returnvalue += planet + " Cnj " + angle + " " + str(orb_deg) + "* " + str(orb_min) + "'"
                foreground_planet = "".join(returnvalue)
                priority = get_priority(planet, angle, 0, "Cnj", orb / 6)
                foregroundlist.append((priority, foreground_planet))

    # Planet proximity to background cusps, measured in prime vertical longitude
    for angle in background_angles:
        for planet in classname.mundane_positions.keys():
            house = classname.mundane_positions[planet][0]
            longitude = classname.mundane_positions[planet][1] % 30
            if (house == angle[0] and longitude >= 20) or (house == angle[1] and longitude <= 10):
                if longitude >= 20:
                    orb = math.fabs(longitude - 30)
                else:
                    orb = longitude
                returnvalue = []
                orb_deg = math.trunc(orb)
                orb_min = math.trunc((orb - (math.trunc(orb))) * 60)
                returnvalue += planet + " background " + str(orb_deg) + "* " + str(orb_min) + "'"
                background_planet = "".join(returnvalue)
                priority = get_priority(planet, angle, 0, "Cnj", orb / 2)
                backgroundlist.append((priority, background_planet))

    # Planet proximity to secondary angles, measured in ecliptical longitude
    for angle in secondary_angles:
        for key in PLANETLIST:
            ecliptical_longitude = classname.planet_dictionary[key][0]
            point = classname.angles[angle]

            # So we don't have to deal with longitudes near 360* as such
            if ecliptical_longitude >= 355:
                ecliptical_longitude -= 360
            if point >= 355:
                point -= 360

            if ecliptical_longitude >= point - 3 and ecliptical_longitude <= point + 3:
                returnvalue = []
                orb = math.fabs(ecliptical_longitude - point)
                orb_deg = math.trunc(orb)
                orb_min = math.trunc((orb - (math.trunc(orb))) * 60)
                returnvalue += key + " Cnj " + angle + " " + str(orb_deg) + "* " + str(orb_min) + "'"
                foreground_planet = "".join(returnvalue)
                priority = get_priority(planet, angle, 0, "Cnj", orb / 3)
                foregroundlist.append((priority, foreground_planet))

    foregroundlist.sort(reverse=True)
    backgroundlist.sort(reverse=True)
    return (foregroundlist, backgroundlist)


def calculate_natal_data(classname):
    """Populate class instance with birth info, planetary coordinates"""

    # Re-write using a with-as block?
    year = classname.datetime.year
    month = classname.datetime.month
    day = classname.datetime.day
    hour = classname.datetime.hour
    minute = classname.datetime.minute
    second = classname.datetime.second

    decimal_longitude = classname.location["Longitude"]
    decimal_latitude = classname.location["Latitude"]

    decimalhour_local = (((((hour * 60)
                            + minute) * 60)
                          + second) / 3600)

    LST = get_LST(year, month, day, decimalhour_local,
                  classname.datetime.offset_hours, decimal_longitude)

    # Conversion from local time to UTC
    # This can probably just be done with pendulum
    (outyear, outmonth, outday,
     outhour, outmin, outsec) = (c_int32(), c_int32(), c_int32(),
                                 c_int32(), c_int32(), c_double())
    py_local_time_to_UTC(year, month, day, hour, minute, second,
                         classname.datetime.offset_hours, outyear, outmonth, outday, outhour,
                         outmin, outsec)

    decimalhour_UTC = (((((outhour.value * 60)
                          + outmin.value) * 60)
                        + outsec.value) / 3600)

    # Using the new UTC time to get a correct Julian Day Number
    time_julian_day = py_get_julian_day(outyear, outmonth, outday,
                                        decimalhour_UTC, 1)

    errorstring = create_string_buffer(126)

    SVP = c_double()
    ayanamsa_return = py_get_ayanamsa_UT(time_julian_day,
                                         SIDEREALMODE, SVP, errorstring)
    if (ayanamsa_return < 0):
        print("Error retrieving ayanamsa")

    # Difference in tropical and sidereal positions desired,
    # not the longitude of one point in the other zodiac
    SVP = (30 - SVP.value)

    planet_number = 0
    returnarray = [(c_double * 6)() for x in range(10)]
    obliquity_array = (c_double * 6)()
    for key in classname.planet_dictionary.keys():

        # dll.swe_calc_ut uses ints as identifiers; 0-9 is Sun-Pluto
        if planet_number <= 9:
            py_calculate_planets_UT(time_julian_day,
                                    planet_number, SIDEREALMODE,
                                    returnarray[planet_number],
                                    errorstring)
            classname.planet_dictionary[key] = returnarray[planet_number]
            planet_number += 1

        else:

            break

            # -1 is the special "planetary body" for calculating obliquity
    py_calculate_planets_UT(time_julian_day, -1, SIDEREALMODE,
                            obliquity_array,
                            errorstring)

    for key in classname.mundane_positions.keys():
        calculate_mundane_positions(classname.planet_dictionary[key][1],
                                    classname.planet_dictionary[key][0],
                                    LST, obliquity_array[0],
                                    SVP, decimal_latitude,
                                    classname.mundane_positions[key])
    classname.obliquity = obliquity_array[0]
    classname.svp = SVP
    classname.lst = LST
    # classname.planet_dictionary["Longitude"] = decimal_longitude
    # classname.planet_dictionary["Latitude"] = decimal_latitude

    calculate_houses(time_julian_day, decimal_latitude, decimal_longitude, classname)

    return None


def calculate_and_sort_aspects(classname, transit_type=None):
    """Prioritize the order of aspects based on their importance"""

    aspect_list = []
    aspect_priority = 0
    loopcount = 0
    for key in PLANETLIST:
        for planetcounter in range(loopcount, 10):
            planetname = str(PLANETLIST[planetcounter])
            potential_aspect = (parse_aspect(str(key), classname.planet_dictionary[key][0], planetname,
                                             classname.planet_dictionary[planetname][0],
                                             "Natal" if transit_type == None else transit_type))
            if potential_aspect is not None:
                aspect_list.append(potential_aspect)
            planetcounter += 1
        loopcount += 1
    aspect_list.sort(reverse=True)
    return aspect_list


def calculate_and_sort_aspects_dual_chart(natal_classname, return_classname, type_of_transit):
    aspect_list = []
    aspect_priority = 0

    for ssr_planet in PLANETLIST:
        for natal_planet in PLANETLIST:
            potential_aspect = (parse_aspect(ssr_planet,
                                             return_classname.planet_dictionary[ssr_planet][0],
                                             natal_planet, natal_classname.planet_dictionary[natal_planet][0],
                                             type_of_transit))
            if potential_aspect is not None:
                aspect_list.append(potential_aspect)

        for natal_angle in ANGLES:
            potential_aspect = (parse_aspect(ssr_planet,
                                             return_classname.planet_dictionary[ssr_planet][0],
                                             natal_angle, natal_classname.angles[natal_angle], type_of_transit))
            if potential_aspect is not None:
                aspect_list.append(potential_aspect)

    aspect_list.sort(reverse=True)
    return aspect_list


def calculate_and_sort_transits_and_progs(natal_classname, transit_classname, transit_date, type_of_transit):
    """Under construction. Will return an aspect list involving progressed planets."""

    aspect_list = []
    aspect_priority = 0

    ### Under construction...outer loop needs to be SSR planets, inner loop natal planets.

    for transiting_planet in PLANETLIST:
        for natal_planet in PLANETLIST:
            potential_aspect = (parse_aspect(transiting_planet,
                                             transit_classname.planet_dictionary[transiting_planet][0],
                                             natal_planet, natal_classname.planet_dictionary[natal_planet][0],
                                             type_of_transit))
            if potential_aspect is not None:
                aspect_list.append(potential_aspect)

        for natal_angle in ANGLES:
            potential_aspect = (parse_aspect(transiting_planet,
                                             transit_classname.planet_dictionary[transiting_planet][0],
                                             natal_angle, natal_classname.angles[natal_angle], type_of_transit))
            if potential_aspect is not None:
                aspect_list.append(potential_aspect)

    aspect_list.sort(reverse=True)
    return aspect_list

    pass


def calculate_ssr_chart(natal_classname, return_classname):
    """Populate return class instance with return chart info"""

    ssr_julian_day = get_solar_return_julian_day(natal_classname, return_classname)
    calculate_natal_data(return_classname)
    print("SSR calculation complete")

    return None


def calculate_slr_chart(natal_classname, return_classname, startdate, enddate, type_lunar_return):
    """Populate return class instance with return chart info"""

    ssr_julian_day = get_lunar_return_julian_day(natal_classname, return_classname, startdate, enddate,
                                                 type_lunar_return)
    calculate_natal_data(return_classname)
    print("SLR calculation complete")

    return None


def print_chart_data(classname, chart_type):
    """Print all relevant natal information to a .txt file"""

    datetime = classname.datetime
    natalfile = open("{}.txt".format(classname.name), "w+")
    natalfile.write("~* AstroNova v. {} *~\n".format(VERSION_NUMBER))
    natalfile.write("Time of report: {}\n".format((pendulum.now()).to_day_datetime_string()))
    natalfile.write("Natal instance: {}\n".format(classname.name))
    natalfile.write("Birth data: {}\n".format(datetime.to_day_datetime_string()))
    natalfile.write("Long: {}   Lat: {}\n\n\n".format(classname.location["Longitude"],
                                                      classname.location["Latitude"]))
    natalfile.write("Sign Placements: \n\n")
    for key in PLANETLIST:
        natalfile.write("{}: {}*{}' {}".format(key,
                                               int((classname.planet_dictionary[key][0] % 30)),
                                               (int(round(((classname.planet_dictionary[key][0] % 30)
                                                           - math.floor(
                                                           (classname.planet_dictionary[key][0] % 30))) * 60))),
                                               get_sign(classname.planet_dictionary[key][0])))
        natalfile.write("\n")
    natalfile.write("\n")

    natalfile.write("\nPrimary Angles (Eclipto): \n\n")
    for key in classname.angles.keys():
        if key == "Asc" or key == "Dsc" or key == "MC" or key == "IC":
            natalfile.write("{} {}* {}' {}".format(key,
                                                   ((math.floor(classname.angles[key])) % 30),
                                                   round((classname.angles[key]
                                                          - math.floor(classname.angles[key])) * 60),
                                                   get_sign(classname.angles[key])))
            natalfile.write("\n")
    natalfile.write("\n")

    # For debugging, in order to see the prime vertical longitudes of planets

    #    natalfile.write("\nPrime Vertical Placements: \n\n")
    #    for key in PLANETLIST:
    #        natalfile.write("{} house position: {}, {}* {}'".format(key, classname.mundane_positions[key][0],
    #                                                        int(classname.mundane_positions[key][1]
    #                                                            - (int(classname.mundane_positions[key][1]/30)) * 30),
    #                                                        (int((classname.mundane_positions[key][1]
    #                                                        - int(classname.mundane_positions[key][1])) * 60))))
    #        natalfile.write("\n")

    angularity_list = calculate_foreground_planets(classname)

    natalfile.write("\nForeground Planets: \n\n")
    for placement in angularity_list[0]:
        natalfile.write(placement[1])
        natalfile.write("\n")

    natalfile.write("\n")

    natalfile.write("\nBackground Planets: \n\n")
    for placement in angularity_list[1]:
        natalfile.write(placement[1])
        natalfile.write("\n")
    natalfile.write("\n")

    natalfile.write("\nList of Aspects: \n\n")
    sorted_aspect_list = calculate_and_sort_aspects(classname)
    for priority, aspect in sorted_aspect_list:
        natalfile.write("{} \n".format(aspect))
        # natalfile.write(" --priority: {}\n".format(priority))

    natalfile.close()


def print_full_solunar_return(natal_classname, return_classname, type_solunar_return):
    """Print all relevant chart data for a solunar return to a .txt file"""

    # print_chart_data(return_classname, "{}".format(type_solunar_return))
    # print("{} initial file written".format(type_solunar_return))

    datetime = return_classname.datetime
    return_longitude = convert_decimal_to_dms(return_classname.location["Longitude"])
    return_latitude = convert_decimal_to_dms(return_classname.location["Latitude"])

    # Should redo this using a "with" block
    natalfile = open(
        "{}.txt".format(natal_classname.name + " Full {} ".format(type_solunar_return) + str(datetime.year)), "w+")
    natalfile.write("~* AstroNova v. {} *~\n".format(VERSION_NUMBER))
    natalfile.write("Time of report: {}\n".format((pendulum.now()).to_day_datetime_string()))
    natalfile.write("Return instance: {}\n".format(
        natal_classname.name + " " + str(type_solunar_return) + " " + str(datetime.year)))
    natalfile.write("{} Date: {}\n".format(type_solunar_return, datetime.to_day_datetime_string()))
    natalfile.write("Long: {}*{}'{}\"   Lat: {}*{}'{}\" \n\n\n".format(return_longitude[0], return_longitude[1],
                                                                       return_longitude[2],
                                                                       return_latitude[0], return_latitude[1],
                                                                       return_latitude[2]))

    natalfile.write("\nPrimary Angles (Eclipto): \n\n")
    for key in return_classname.angles.keys():
        if key in ["Asc", "Dsc", "MC", "IC"]:
            natalfile.write("{} {}* {}' {}".format(key,
                                                   ((math.floor(return_classname.angles[key])) % 30),
                                                   round((return_classname.angles[key]
                                                          - math.floor(return_classname.angles[key])) * 60),
                                                   get_sign(return_classname.angles[key])))
            natalfile.write("\n")
    natalfile.write("\n")

    # Eventually: rewrite the angularity calculator to NOT sort data;
    # implement a prioritizing function, return a tuple that gets sorted by the function asking for it
    angularity_list = calculate_foreground_planets(return_classname)

    # Allows for precession of natal chart into the framework of the return chart
    natal_classname.location = return_classname.location
    natal_classname.obliquity = return_classname.obliquity
    natal_classname.lst = return_classname.lst
    natal_classname.svp = return_classname.svp
    natal_classname.datetime = return_classname.datetime
    original_angles = natal_classname.angles
    natal_classname.angles = return_classname.angles

    for key in natal_classname.mundane_positions.keys():
        calculate_mundane_positions(natal_classname.planet_dictionary[key][1],
                                    natal_classname.planet_dictionary[key][0],
                                    natal_classname.lst,
                                    natal_classname.obliquity,
                                    natal_classname.svp, natal_classname.location["Latitude"],
                                    natal_classname.mundane_positions[key])

    angularity_list_natal = calculate_foreground_planets(natal_classname)

    natalfile.write("\nForeground Planets: \n\n")
    for placement in angularity_list[0]:
        natalfile.write("t. " + placement[1])
        natalfile.write("\n")

    for placement in angularity_list_natal[0]:
        natalfile.write("r. " + placement[1])
        natalfile.write("\n")

    natalfile.write("\n")

    natalfile.write("\nBackground Planets: \n\n")
    for placement in angularity_list[1]:
        natalfile.write("t. " + placement[1])
        natalfile.write("\n")
    natalfile.write("\n")

    for placement in angularity_list_natal[1]:
        natalfile.write("r. " + placement[1])
        natalfile.write("\n")
    natalfile.write("\n")

    natal_classname.angles = original_angles

    natalfile.write("\nList of Aspects: \n\n")
    transit_aspects = calculate_and_sort_aspects(return_classname, "Transit to Transit")
    for priority, aspect in transit_aspects:
        natalfile.write("{} \n".format(aspect))

    natalfile.write("\n\n")

    sorted_aspect_list = calculate_and_sort_aspects_dual_chart(natal_classname, return_classname,
                                                               "SSR to Natal" if type_solunar_return == "SSR" else "SLR to Natal")
    for priority, aspect in sorted_aspect_list:
        natalfile.write("{} \n".format(aspect))
        # natalfile.write(" -- priority: {}\n".format(priority))

    natalfile.close()
    print("Full {} File Written".format(type_solunar_return))


def print_active_transits(natal_classname, local_classname, solar_classname, transit_instance, transit_date):
    """Print active transits to natal and SSR to a .txt file"""

    calculate_natal_data(natal_classname)
    if local_classname != None:
        calculate_natal_data(local_classname)

    calculate_natal_data(solar_classname)
    calculate_natal_data(transit_instance)
    transits_to_natal = calculate_and_sort_transits_and_progs(natal_classname, transit_instance,
                                                              natal_classname.datetime, "Transit to Natal")
    transits_to_ssr = calculate_and_sort_transits_and_progs(solar_classname, transit_instance, transit_date,
                                                            "Transit to SSR")

    # Copied and pasted from print_full_solunar_return with no alteration

    # Should redo this using a "with" block
    natalfile = open("{}.txt".format(natal_classname.name + " Transit Report"), "w+")
    natalfile.write("~* AstroNova v. {} *~\n".format(VERSION_NUMBER))
    natalfile.write("Time of report: {}\n".format((pendulum.now()).to_day_datetime_string()))
    natalfile.write("Transit Analysis Date: {}\n".format(transit_instance.datetime.to_day_datetime_string()))
    natalfile.write("Long: {}   Lat: {} \n\n\n".format(solar_classname.location["Longitude"],
                                                       solar_classname.location["Latitude"]))

    natalfile.write("\n")

    natalfile.write("\nList of Aspects: \n\n")
    sorted_aspect_list = calculate_and_sort_aspects_dual_chart(natal_classname, transit_instance,
                                                               "Transit to Natal")

    if local_classname != None:
        sorted_aspect_list_local = calculate_and_sort_aspects_dual_chart(local_classname, transit_instance,
                                                                         "Transit to Local")

    sorted_aspect_list_ssr = calculate_and_sort_aspects_dual_chart(solar_classname, transit_instance,
                                                                   "Transit to SSR")

    for entry in sorted_aspect_list_ssr:
        sorted_aspect_list.append(entry)
    if local_classname != None:
        for entry in sorted_aspect_list_local:
            sorted_aspect_list.append(entry)

    sorted_aspect_list.sort(reverse=True)

    for priority, aspect in sorted_aspect_list:
        natalfile.write("{} \n".format(aspect))
        # natalfile.write(" -- priority: {}\n".format(priority))

    natalfile.close()
    print("Full Transit Report Written")
