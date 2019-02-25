import os
from ctypes import c_double
import math
import pendulum
from datetime import datetime, timedelta

import settings
from dll_tools.SwissephLib import SwissephLib
from dll_tools.dll_tools import get_ephe_path


class ChartData:
    def __init__(self, name, local_datetime, utc_datetime, longitude, latitude):
        if (type(local_datetime) != pendulum.datetime.Datetime
                or type(utc_datetime) != pendulum.datetime.Datetime):
            raise TypeError("Must initialize with Pendulum datetime instances")

        self.name = name
        self.local_datetime = local_datetime
        self.utc_datetime = utc_datetime
        self.location = {
            "Longitude": longitude,
            "Latitude": latitude
        }
        self.obliquity = None
        self.lst = self._calculate_LST(local_datetime, longitude)
        self.svp = None
        self.ramc = None  # decimal lst * 15

        # TODO: Initialize these as None; calculate and populate them with underscore functions
        self.planets_longitude = {
            # Ecliptical longitude, celestial latitude, distance,
            # Speed in long, speed in lat, speed in dist
            "Sun": (c_double * 6)(),
            "Moon": (c_double * 6)(),
            "Mercury": (c_double * 6)(),
            "Venus": (c_double * 6)(),
            "Mars": (c_double * 6)(),
            "Jupiter": (c_double * 6)(),
            "Saturn": (c_double * 6)(),
            "Uranus": (c_double * 6)(),
            "Neptune": (c_double * 6)(),
            "Pluto": (c_double * 6)()
        }

        self.planets_mundane = {
            # House placement, decimal longitude (out of 360*)
            "Sun": [c_double(), c_double()],
            "Moon": [c_double(), c_double()],
            "Mercury": [c_double(), c_double()],
            "Venus": [c_double(), c_double()],
            "Mars": [c_double(), c_double()],
            "Jupiter": [c_double(), c_double()],
            "Saturn": [c_double(), c_double()],
            "Uranus": [c_double(), c_double()],
            "Neptune": [c_double(), c_double()],
            "Pluto": [c_double(), c_double()],
        }

        self.planets_right_ascension = {
            # Decimal longitude (out of 360*)
            "Sun": c_double(),
            "Moon": c_double(),
            "Mercury": c_double(),
            "Venus": c_double(),
            "Mars": c_double(),
            "Jupiter": c_double(),
            "Saturn": c_double(),
            "Uranus": c_double(),
            "Neptune": c_double(),
            "Pluto": c_double(),
        }

        self.cusps_longitude = None
        self.angles_longitude = None

    def get_ecliptical_coords(self):
        coords = dict()
        for planet, array in self.planets_longitude:
            coords[planet] = array[0]
        return coords

    def get_mundane_coords(self):
        coords = dict()
        for planet, array in self.planets_mundane:
            coords[planet] = array[1]
        return coords

    def get_right_ascension_coords(self):
        return self.planets_right_ascension

    def get_sign(self, longitude):
        """Determine astrological sign from unsigned longitude"""

        zodiac = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
                  "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        key = int(longitude / 30)
        return zodiac[key]

    def _calculate_LST(self, dt, decimal_longitude):
        """Calculate local sidereal time for date, time, location of event"""

        year, month, day = dt.year, dt.month, dt.day
        decimal_hour = self._calculate_decimal_hour(dt.hour, dt.min, dt.sec)
        with SwissephLib('') as s:
            julian_day_0_GMT = s.get_julian_day(year, month, day, 0, 1)

        universal_time = (decimal_hour - dt.offset_hours)
        sidereal_time_at_midnight_julian_day = (julian_day_0_GMT - 2451545.0) / 36525.0

        greenwich_sidereal_time = (6.697374558
                                   + (2400.051336 * sidereal_time_at_midnight_julian_day)
                                   + (0.000024862
                                      * (math.pow(sidereal_time_at_midnight_julian_day, 2)))
                                   + (universal_time * 1.0027379093))
        local_sidereal_time = ((greenwich_sidereal_time
                                + (decimal_longitude / 15)) % 24)

        return local_sidereal_time if local_sidereal_time > 0 else local_sidereal_time + 24

    def _calculate_decimal_hour(self, hour, minute, second):
        decimal_hour = (((((hour * 60)
                           + minute) * 60)
                         + second) / 3600)
        return decimal_hour

    def _convert_decimal_to_dms(self, decimal):
        degree = int(decimal)
        minute = int(math.fabs((decimal - degree) * 60))
        second = int((math.fabs((decimal - degree) * 60) - int(math.fabs((decimal - degree) * 60))) * 60)
        return degree, minute, second

    def _calculate_prime_vertical_longitude(self, planet_latitude, planet_longitude,
                                            ramc, obliquity, decimal_svp,
                                            decimal_geolat):
        """Calculate a planet's prime vertical longitude"""

        # Variable names reference the original angularity spreadsheet posted on Solunars.com.
        # Most do not have official names and are intermediary values used elsewhere.
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

        if calc_ax < 0:
            precessed_right_ascension = calc_ayx_deg + 180
        elif calc_ay < 0:
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

        campanus_longitude = 90 - calc_cz if (calc_cx < 0) else 270 - calc_cz

        planet_pvl = []
        planet_pvl[0] = (int(campanus_longitude / 30) + 1)
        planet_pvl[1] = campanus_longitude
        return planet_pvl

    def _calculate_houses(self, julian_day_UTC, geolatitude, geolongitude):
        """Calculate house cusps and ecliptical longitudes of angles in the Campanus system"""
        cusp_array = (c_double * 13)()
        house_array = (c_double * 8)()

        path_to_ephemeris = get_ephe_path()
        with SwissephLib(path_to_ephemeris) as s:
            s.calculate_houses(julian_day_UTC, settings.SIDEREALMODE,
                               geolatitude, geolongitude, settings.CAMPANUS,
                               cusp_array, house_array)

        cusps_longitude = {
            "1": cusp_array[1].value,
            "2": cusp_array[2].value,
            "3": cusp_array[3].value,
            "4": cusp_array[4].value,
            "5": cusp_array[5].value,
            "6": cusp_array[6].value,
            "7": cusp_array[7].value,
            "8": cusp_array[8].value,
            "9": cusp_array[9].value,
            "10": cusp_array[10].value,
            "11": cusp_array[11].value,
            "12": cusp_array[12].value
        }

        angles_longitude = {
            "Asc" : house_array[0].value,
            "MC" : house_array[1].value,
            "Dsc" : (house_array[0].value + 180) % 360,
            "IC" : (house_array[1].value + 180) % 360,
            "Eq Asc" : house_array[4].value,
            "Eq Dsc" : (house_array[4].value + 180) % 360
        }
        angles_longitude["EP (Ecliptical)"] = (angles_longitude["MC"] + 90) % 360,
        angles_longitude["Zen"] = (angles_longitude["Dsc"] + 90) % 360
        angles_longitude["WP (Ecliptical)"] = (angles_longitude["IC"] + 90) % 360
        angles_longitude["Ndr"] = (angles_longitude["Asc"] + 90) % 360

        return cusps_longitude, angles_longitude
