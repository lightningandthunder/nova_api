import os
import struct
from ctypes import c_double, create_string_buffer
from math import sin, cos, tan, asin, acos, atan, degrees, radians, fabs
import pendulum
from logging import getLogger

import settings
from src.dll_tools.swissephlib import SwissephLib
from src.dll_tools.dll_tools import get_planet_dict

logger = getLogger(__name__)


class ChartData:
    def __init__(self, name, local_datetime, utc_datetime, geo_longitude, geo_latitude):
        self.name = name
        self.local_datetime = local_datetime
        self.utc_datetime = utc_datetime
        self.longitude = geo_longitude
        self.latitude = geo_latitude
        self.obliquity = None
        self.LST = self._calculate_LST(local_datetime, geo_longitude)
        self.svp = None
        self.ayanamsa = None
        self.ramc = None

        # Ecliptical longitude, celestial latitude, distance,
        # Speed in long, speed in lat, speed in dist
        self.planets_ecliptic = get_planet_dict()

        # House placement, decimal longitude (out of 360*)
        self.planets_mundane = get_planet_dict()

        # Decimal longitude (out of 360*)
        self.planets_right_ascension = get_planet_dict()

        self.cusps_longitude = None
        self.angles_longitude = None

        # self._populate_ecliptic_values()
        self.__rewritten_populate_ecliptic()
        self._populate_ramc()
        self._populate_mundane_values()
        self._populate_right_ascension_values()

    def get_ecliptical_coords(self):
        coords = dict()
        for planet in self.planets_ecliptic.keys():
            coords[planet] = self.planets_ecliptic[planet][0]
        return coords

    def get_mundane_coords(self):
        coords = dict()
        for planet in self.planets_mundane.keys():
            coords[planet] = self.planets_mundane[planet][1]
        return coords

    def get_right_ascension_coords(self):
        return self.planets_right_ascension

    def get_sign(self, longitude):
        """Determine astrological sign from unsigned longitude"""

        zodiac = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
                  "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        key = int(longitude / 30)
        return zodiac[key]

    #

    def _calculate_LST(self, dt, decimal_longitude):
        """Calculate local sidereal time for date, time, location of event"""

        year, month, day = dt.year, dt.month, dt.day
        decimal_hour = self._convert_hms_to_decimal(dt.hour, dt.minute, dt.second)

        # Julian Day number at midnight
        with SwissephLib() as s:
            julian_day_0_GMT = s.get_julian_day(year, month, day, 0, 1)

        universal_time = (decimal_hour - dt.offset_hours)
        sidereal_time_at_midnight_julian_day = (julian_day_0_GMT - 2451545.0) / 36525.0

        greenwich_sidereal_time = (6.697374558
                                   + (2400.051336 * sidereal_time_at_midnight_julian_day)
                                   + (0.000024862
                                      * (pow(sidereal_time_at_midnight_julian_day, 2)))
                                   + (universal_time * 1.0027379093))
        local_sidereal_time = ((greenwich_sidereal_time
                                + (decimal_longitude / 15)) % 24)

        return local_sidereal_time if local_sidereal_time > 0 else local_sidereal_time + 24

    def _convert_hms_to_decimal(self, hour, minute, second):
        decimal_hour = (((((hour * 60)
                           + minute) * 60)
                         + second) / 3600)
        return decimal_hour

    def _convert_decimal_to_dms(self, decimal):
        degree = int(decimal)
        minute = int(fabs((decimal - degree) * 60))
        second = int((fabs((decimal - degree) * 60) - int(fabs((decimal - degree) * 60))) * 60)
        return degree, minute, second

    def _calculate_prime_vertical_longitude(self, planet_longitude, planet_latitude,
                                            ramc, obliquity, decimal_svp,
                                            decimal_geolat):
        """Calculate a planet's prime vertical longitude"""

        # Variable names reference the original angularity spreadsheet posted on Solunars.com.
        # Most do not have official names and are intermediary values used elsewhere.
        calc_ax = (cos(radians(planet_longitude
                               + (360 - (330 + decimal_svp)))))

        precessed_declination = (degrees(asin
                                         (sin(radians(planet_latitude))
                                          * cos(radians(obliquity))
                                          + cos(radians(planet_latitude))
                                          * sin(radians(obliquity))
                                          * sin(radians(planet_longitude
                                                        + (360 - (330 + decimal_svp)))))))

        calc_ay = (sin(radians((planet_longitude
                                + (360 - (330 + decimal_svp)))))
                   * cos(radians(obliquity))
                   - tan(radians(planet_latitude))
                   * sin(radians(obliquity)))

        calc_ayx_deg = degrees(atan(calc_ay / calc_ax))

        if calc_ax < 0:
            precessed_right_ascension = calc_ayx_deg + 180
        else:
            if calc_ay < 0:
                precessed_right_ascension = calc_ayx_deg + 360
            else:
                precessed_right_ascension = calc_ayx_deg

        hour_angle_degree = ramc - precessed_right_ascension

        calc_cz = (degrees(atan(1
                                / (cos(radians(decimal_geolat))
                                   / tan(radians(hour_angle_degree))
                                   + sin(radians(decimal_geolat))
                                   * tan(radians(precessed_declination))
                                   / sin(radians(hour_angle_degree))))))

        calc_cx = (cos(radians(decimal_geolat))
                   * cos(radians(hour_angle_degree))
                   + sin(radians(decimal_geolat))
                   * tan(radians(precessed_declination)))

        campanus_longitude = 90 - calc_cz if (calc_cx < 0) else 270 - calc_cz

        planet_pvl_house = (int(campanus_longitude / 30) + 1)
        return [planet_pvl_house, campanus_longitude]

    def populate_houses_and_cusps(self, julian_day_utc, geolatitude, geolongitude):
        """Calculate house cusps and ecliptical longitudes of angles in the Campanus system"""
        cusp_array = (c_double * 13)()
        house_array = (c_double * 8)()

        with SwissephLib() as s:
            s.calculate_houses(julian_day_utc, settings.SIDEREALMODE, geolatitude, geolongitude, settings.CAMPANUS,
                               cusp_array, house_array)

        self.cusps_longitude = {
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

        self.angles_longitude = {
            "Asc": house_array[0].value,
            "MC": house_array[1].value,
            "Dsc": (house_array[0].value + 180) % 360,
            "IC": (house_array[1].value + 180) % 360,
            "Eq Asc": house_array[4].value,
            "Eq Dsc": (house_array[4].value + 180) % 360
        }
        self.angles_longitude["EP (Ecliptical)"] = (self.angles_longitude["MC"] + 90) % 360,
        self.angles_longitude["Zen"] = (self.angles_longitude["Dsc"] + 90) % 360
        self.angles_longitude["WP (Ecliptical)"] = (self.angles_longitude["IC"] + 90) % 360
        self.angles_longitude["Ndr"] = (self.angles_longitude["Asc"] + 90) % 360

    def _populate_ecliptic_values(self):
        """Calculates and populates ecliptic longitude, the SVP, and obliquity for a chart instance."""

        decimal_hour_utc = self._convert_hms_to_decimal(self.utc_datetime.hour, self.utc_datetime.minute,
                                                        self.utc_datetime.second)
        with SwissephLib() as s:
            time_julian_day = s.get_julian_day(self.utc_datetime.year, self.utc_datetime.month, self.utc_datetime.day,
                                               decimal_hour_utc, 1)
            errorstring = create_string_buffer(126)

            # svp is a destination for the Swiss Ephemeris function to write to
            svp = c_double()
            ayanamsa_return = s.get_ayanamsa_UT(time_julian_day, settings.SIDEREALMODE, svp, errorstring)
            if ayanamsa_return < 0:
                logger.error("Error retrieving ayanamsa: " + str(errorstring))

            self.svp = (30 - svp.value)

            planet_number = 0
            returnarray = [(c_double * 6)() for _ in range(10)]
            for planet_name in settings.SWISSEPH_BODY_NUMBER_MAP:

                # dll.swe_calc_ut uses ints as identifiers; 0-9 is Sun-Pluto
                if planet_number <= 9:
                    s.calculate_planets_UT(time_julian_day, planet_number, settings.SIDEREALMODE,
                                           returnarray[planet_number], errorstring)
                    self.planets_ecliptic[planet_name] = returnarray[planet_number]
                    planet_number += 1
                else:
                    break

            obliquity_array = (c_double * 6)()

            # -1 is the special "planetary body" for calculating obliquity
            s.calculate_planets_UT(time_julian_day, -1, settings.SIDEREALMODE, obliquity_array, errorstring)
            self.obliquity = obliquity_array[0]

    def _populate_ramc(self):
        self.ramc = self.LST * 15

    def _populate_mundane_values(self):
        for body_name in settings.SWISSEPH_BODY_NUMBER_MAP:
            planet_longitude = self.planets_ecliptic[body_name][0]
            planet_latitude = self.planets_ecliptic[body_name][1]
            house, long = self._calculate_prime_vertical_longitude(planet_longitude, planet_latitude,
                                                                                   self.ramc, self.obliquity,
                                                                                   self.svp, self.latitude)

            self.planets_mundane[body_name] = house, long

    def _calculate_right_ascension(self, planet_latitude, planet_longitude):

        circle_minus_ayanamsa = 360 - (330 + self.svp)

        precessed_longitude = planet_longitude + (circle_minus_ayanamsa)  # C8
        calcs_ay = (sin(radians(precessed_longitude)) * cos(radians(self.obliquity))
                    - tan(radians(planet_latitude)) * sin(radians(self.obliquity)))
        calcs_ax = cos(radians(precessed_longitude))
        calcs_o = degrees(atan(calcs_ay / calcs_ax))

        if calcs_ax < 0:
            precessed_right_ascension = calcs_o + 180
        else:
            if calcs_ay < 0:
                precessed_right_ascension = calcs_o + 360
            else:
                precessed_right_ascension = calcs_o

        return precessed_right_ascension

    def _populate_right_ascension_values(self):
        for body_name in settings.SWISSEPH_BODY_NUMBER_MAP:
            planet_longitude = self.planets_ecliptic[body_name][0]
            planet_latitude = self.planets_ecliptic[body_name][1]
            planet_right_ascension = self._calculate_right_ascension(planet_latitude, planet_longitude)

            self.planets_right_ascension[body_name] = planet_right_ascension

    def __rewritten_populate_ecliptic(self):
        decimal_hour_utc = self._convert_hms_to_decimal(self.utc_datetime.hour, self.utc_datetime.minute,
                                                        self.utc_datetime.second)

        with SwissephLib() as s:
            time_julian_day = s.get_julian_day(self.utc_datetime.year, self.utc_datetime.month, self.utc_datetime.day,
                                               decimal_hour_utc, 1)
            errorstring = create_string_buffer(126)

            svp = c_double()  # svp is a destination for the Swiss Ephemeris function to write to
            ayanamsa_return = s.get_ayanamsa_UT(time_julian_day, settings.SIDEREALMODE, svp, errorstring)
            if ayanamsa_return < 0:
                logger.error("Error retrieving ayanamsa: " + str(errorstring))
            self.svp = (30 - svp.value)

            returnarray = [(c_double * 6)() for _ in range(10)]

            for body_number, body_name in enumerate(settings.SWISSEPH_BODY_NUMBER_MAP):
                s.calculate_planets_UT(time_julian_day, body_number, settings.SIDEREALMODE,
                                       returnarray[body_number], errorstring)
                self.planets_ecliptic[body_name] = returnarray[body_number]

            obliquity_array = (c_double * 6)()

            # -1 is the special "planetary body" for calculating obliquity
            s.calculate_planets_UT(time_julian_day, -1, settings.SIDEREALMODE, obliquity_array, errorstring)
            self.obliquity = obliquity_array[0]
