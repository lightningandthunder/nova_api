from ctypes import c_double, create_string_buffer
from math import sin, cos, tan, asin, atan, degrees, radians, fabs
import copy

from chartdata import ChartData
from logging import getLogger
from sidereal_framework import SiderealFramework
from swissephlib import SwissephLib

import settings

logger = getLogger(__name__)

"""
Singleton that manages chart data sets. Initialized with an instance of a SwissephLib library wrapper class.
"""


class ChartManager:

    def __init__(self):
        self.lib = SwissephLib()

    def __del__(self):
        self.lib.close()

    # =============================================================================================================== #
    # =========================================   Public functions   ================================================ #
    # =============================================================================================================== #

    def create_chartdata(self, local_datetime, geo_longitude, geo_latitude):
        """Create a ChartData instance representing an astrological chart.
        :param name: String
        :param local_datetime: pendulum.datetime
        :param geo_longitude: Float
        :param geo_latitude: Float
        :returns: ChartData instance"""

        utc_datetime = local_datetime.in_tz('UTC')
        julian_day = self._calculate_julian_day(utc_datetime)
        chart = ChartData(local_datetime, utc_datetime, julian_day)
        chart.sidereal_framework = self._initialize_sidereal_framework(utc_datetime, local_datetime, geo_longitude,
                                                                       geo_latitude)
        chart.planets_ecliptic = self._populate_ecliptic_values(julian_day)
        chart.planets_mundane = self._populate_mundane_values(chart)
        chart.planets_right_ascension = self._populate_right_ascension_values(chart)
        chart.angles_longitude, chart.cusps_longitude = self._populate_ecliptical_angles_and_cusps(chart)

        return chart

    def relocate(self, radix, geo_longitude, geo_latitude, timezone):
        radix.sidereal_framework.geo_longitude = geo_longitude
        radix.sidereal_framework.geo_latitude = geo_latitude
        radix.local_datetime = radix.local_datetime.in_tz(timezone)
        radix.planets_mundane = self._populate_mundane_values(radix)
        radix.planets_right_ascension = self._populate_right_ascension_values(radix)
        radix.angles_longitude, radix.cusps_longitude = self._populate_ecliptical_angles_and_cusps(radix)

    def precess_into_sidereal_framework(self, radix, transit_chart):
        """Recalculate prime vertical longitude, right ascension, and ecliptical angles and cusps against another
        sidereal framework. Done on the radix chart in place.
        :param radix: ChartData instance to be precessed
        :param transit_chart: ChartData instance
        :returns: None"""

        radix.sidereal_framework = transit_chart.sidereal_framework
        radix.local_datetime = radix.local_datetime.in_tz(transit_chart.local_datetime.tz)
        radix.planets_mundane = self._populate_mundane_values(radix)
        radix.planets_right_ascension = self._populate_right_ascension_values(radix)
        radix.angles_longitude, radix.cusps_longitude = self._populate_ecliptical_angles_and_cusps(radix)

    def get_transit_sensitive_charts(self, radix, local_dt, geo_longitude, geo_latitude):
        local_natal = copy.deepcopy(radix)
        self.relocate(local_natal, geo_longitude, geo_latitude, local_dt.tz)
        ssr_dt = local_dt
        active_ssr = \
        self._generate_return_list(radix=local_natal, geo_longitude=geo_longitude, geo_latitude=geo_latitude,
                                   date=ssr_dt, body=0, harmonic=1, return_quantity=1)[0]

        # Re-generate if the SSR identified is in the future
        if active_ssr.local_datetime > local_dt:
            ssr_dt = ssr_dt.subtract(years=1)
            active_ssr = \
                self._generate_return_list(radix=local_natal, geo_longitude=geo_longitude, geo_latitude=geo_latitude,
                                           date=ssr_dt, body=0, harmonic=1, return_quantity=1)[0]

        transits = self.create_chartdata(local_dt, geo_longitude, geo_latitude)


        # Secondary progressions
        sp_radix = self.get_progressions(radix, local_dt, geo_longitude, geo_latitude)
        sp_ssr = self.get_progressions(active_ssr, local_dt, geo_longitude, geo_latitude)

        return radix, local_natal, sp_radix, active_ssr, sp_ssr, transits  # add progressed natal, progressed SSR
        # TODO: Test me

    def get_progressions(self, radix, local_dt, geo_longitude, geo_latitude):
        progressed_time = (local_dt.in_tz('UTC') - radix.utc_datetime).in_minutes() * settings.Q2
        progressed_dt = radix.utc_datetime.add(minutes=progressed_time)

        # Create chart based on progressed date
        chart = self.create_chartdata(progressed_dt, geo_longitude, geo_latitude)

        # Precess chart into actual date
        chart.local_datetime = local_dt
        chart.utc_datetime = local_dt.in_tz('UTC')
        chart.sidereal_framework = self._initialize_sidereal_framework(local_dt.in_tz('UTC'), local_dt,
                                                                                 geo_longitude, geo_latitude)
        chart.planets_mundane = self._populate_mundane_values(chart)
        chart.planets_right_ascension = self._populate_right_ascension_values(chart)
        return chart

    def generate_radix_return_pairs(self, radix, geo_longitude, geo_latitude, date, body, harmonic, return_quantity):
        return_list = self._generate_return_list(radix, geo_longitude, geo_latitude, date, body, harmonic,
                                                 return_quantity)
        pairs = list()
        for _return in return_list:
            radix_copy = copy.deepcopy(radix)
            self.precess_into_sidereal_framework(radix_copy, _return)
            pairs.append((radix_copy, _return))
        return pairs

    @staticmethod
    def get_sign(longitude):
        """Determine astrological sign from unsigned longitude.
        :param longitude: Float 0-359.9~
        :returns: String"""

        zodiac = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
                  "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        key = int(longitude / 30)
        return zodiac[key]

    @staticmethod
    def convert_dms_to_decimal(degree, minute, second):
        """Convert hour/degree, minute, and second into a decimal hour or decimal degree.
        :param degree: Int
        :param minute: Int
        :param second: Int
        :returns: Float"""

        return degree + (minute / 60) + (second / 3600)

    @staticmethod
    def convert_decimal_to_dms(decimal):
        """Convert a decimal hour or degree into degree/hour, minute, second.
        :param decimal: Float
        :returns: Int Degree/hour, Int minute, Int second"""
        degree = int(decimal)
        minute = int(fabs((decimal - degree) * 60))
        second = int((fabs((decimal - degree) * 60) - int(fabs((decimal - degree) * 60))) * 60)
        return degree, minute, second

    # =============================================================================================================== #
    # ============================   Functions to populate coordinate data sets   =================================== #
    # =============================================================================================================== #

    def _populate_ecliptic_values(self, julian_day):
        """Calculate ecliptical longitude for planets.
        :param chart: ChartData instance.
        :returns: Dict ecliptical longitude by planet"""
        errorstring = create_string_buffer(126)
        returnarray = [(c_double * 6)() for _ in range(10)]

        ecliptic_dict = dict()
        for body_number, body_name in enumerate(settings.INT_TO_STRING_PLANET_MAP):
            self.lib.calculate_planets_UT(julian_day, body_number, settings.SIDEREALMODE,
                                          returnarray[body_number], errorstring)
            ecliptic_dict[body_name] = returnarray[body_number]

        return ecliptic_dict

    def _populate_mundane_values(self, chart):
        """Calculate prime vertical longitude for planets.
        :param chart: ChartData instance.
        :returns: Dict prime vertical longitude by planet"""

        mundane_dict = dict()
        for body_name in settings.INT_TO_STRING_PLANET_MAP:
            planet_longitude = chart.planets_ecliptic[body_name][0]
            planet_latitude = chart.planets_ecliptic[body_name][1]
            house, long = self._calculate_prime_vertical_longitude(planet_longitude, planet_latitude,
                                                                   chart.sidereal_framework.ramc,
                                                                   chart.sidereal_framework.obliquity,
                                                                   chart.sidereal_framework.svp,
                                                                   chart.sidereal_framework.geo_latitude)

            mundane_dict[body_name] = house, long
        return mundane_dict

    def _populate_right_ascension_values(self, chart):
        """Calculate right ascension values for planets.
        :param chart: ChartData instance.
        :returns: Dict right ascension values by planet"""

        right_ascension_dict = dict()
        for body_name in settings.INT_TO_STRING_PLANET_MAP:
            planet_longitude = chart.planets_ecliptic[body_name][0]
            planet_latitude = chart.planets_ecliptic[body_name][1]
            planet_right_ascension = self._calculate_right_ascension(planet_latitude, planet_longitude,
                                                                     chart.sidereal_framework.svp,
                                                                     chart.sidereal_framework.obliquity)

            right_ascension_dict[body_name] = planet_right_ascension
        return right_ascension_dict

    def _populate_ecliptical_angles_and_cusps(self, chart):
        """Calculate house cusps and ecliptical longitudes of angles in the Campanus system.
        :param chart: ChartData instance.
        :returns: List angles, list cusps"""

        julian_day_utc = chart.julian_day
        geo_longitude = chart.sidereal_framework.geo_longitude
        geo_latitude = chart.sidereal_framework.geo_latitude

        cusp_array = (c_double * 13)()
        house_array = (c_double * 10)()

        self.lib.calculate_houses(julian_day_utc, settings.SIDEREALMODE, geo_latitude, geo_longitude, settings.CAMPANUS,
                                  cusp_array, house_array)

        cusps_longitude = {
            "1": cusp_array[1],
            "2": cusp_array[2],
            "3": cusp_array[3],
            "4": cusp_array[4],
            "5": cusp_array[5],
            "6": cusp_array[6],
            "7": cusp_array[7],
            "8": cusp_array[8],
            "9": cusp_array[9],
            "10": cusp_array[10],
            "11": cusp_array[11],
            "12": cusp_array[12]
        }

        angles_longitude = {
            "Asc": house_array[0],
            "MC": house_array[1],
            "Dsc": (house_array[0] + 180) % 360,
            "IC": (house_array[1] + 180) % 360,
            "Eq Asc": house_array[4],
            "Eq Dsc": (house_array[4] + 180) % 360
        }
        angles_longitude["EP (Ecliptical)"] = (angles_longitude["MC"] + 90) % 360
        angles_longitude["Zen"] = (angles_longitude["Dsc"] + 90) % 360
        angles_longitude["WP (Ecliptical)"] = (angles_longitude["IC"] + 90) % 360
        angles_longitude["Ndr"] = (angles_longitude["Asc"] + 90) % 360

        return angles_longitude, cusps_longitude

    # =============================================================================================================== #
    # =============================   Functions for harmonic return calculation   =================================== #
    # =============================================================================================================== #

    def _is_past(self, transit_longitude, natal_longitude, harmonic):
        """Determine if a transit longitude is 'past' a radical one in the context of a harmonic.
        :param transit_longitude: Float 0-359.9~
        :param natal_longitude: Float 0-359.9~
        :param harmonic: Int 1-36
        :returns: Boolean"""

        harmonic_of_natal_pos = self._get_closest_harmonic_pos(natal_longitude, transit_longitude, harmonic)
        half_coordinate_range = (360 / harmonic) / 2
        distance = fabs(transit_longitude - harmonic_of_natal_pos)

        past = True if transit_longitude > harmonic_of_natal_pos else False
        # If the longitudes are in same half of range, expected behavior; otherwise, reverse
        return past if distance <= half_coordinate_range else not past

    def _get_closest_harmonic_pos(self, radix_pos, transit_pos, harmonic):
        """Calculate the closest valid harmonic position of a radical longitude to a transiting longitude.
        :param radix_pos: Float 0-359.9~
        :param transit_pos: Float 0-359.9~
        :param harmonic: Int 1-36
        returns: Float 0-359.9~"""

        harmonic_positions = set()
        coordinate_range = 360 / harmonic
        next_harmonic_pos = (radix_pos + coordinate_range) % 360
        while next_harmonic_pos not in harmonic_positions:
            harmonic_positions.add(next_harmonic_pos)
            next_harmonic_pos = (next_harmonic_pos + coordinate_range) % 360

        return min(harmonic_positions, key=lambda x: abs(x - transit_pos))

    def _get_nearest_return(self, body, radix_position, dt, harmonic):
        """Get nearest harmonic return date to a given date, to start a list of return dates.
        :param body: Int 0-9
        :param radix_position: Float 0-359.9~
        :param dt: pendulum.datetime
        :param harmonic: Int 1-36
        :returns: pendulum.datetime"""

        delta = (settings.ORBITAL_PERIODS_HOURS[body] // harmonic) - 24
        earliest_dt = dt.subtract(hours=delta)
        latest_dt = dt.add(hours=delta)
        return_in_past = self._find_harmonic_in_date_range(harmonic, body, radix_position, earliest_dt, dt,
                                                           precision='hours')
        return_in_future = self._find_harmonic_in_date_range(harmonic, body, radix_position, dt, latest_dt,
                                                             precision='hours')

        if return_in_past and return_in_future:
            return min([return_in_past, return_in_future], key=lambda x: abs(x - dt))
        else:
            return return_in_past if return_in_past else return_in_future

    def _find_harmonic_in_date_range(self, harmonic, body, natal_longitude, start_dt, end_dt, precision):
        """Finds a harmonic return within a pair of dates, to a specified precision.
        :param harmonic: Int 1-36
        :param body: Int 0-9 (referring to planetary body)
        :param natal_longitude: Float 0-359.9~
        :param start_dt: Pendulum.Datetime instance
        :param end_dt: Pendulum.Datetime instance
        :param precision: String, e.g. 'hours', 'seconds'
        :returns: pendulum.datetime instance for harmonic return"""

        if type(harmonic) != int:
            raise ValueError('Cannot calculate harmonic returns with a non-integer harmonic')
        elif harmonic > 36 or harmonic < 1:
            raise ValueError('Can only safely calculate harmonic returns with harmonic between 1-36')
        elif harmonic > 4 and body == 1:
            raise ValueError('Cannot search for return harmonics greater than 4 on the Moon')

        if precision not in settings.PENDULUM_FUNCS.keys():
            raise ValueError('Precision must be a unit of time as a string: \'hours\', \'seconds\', etc')

        #  Calculate a list of hours/seconds/etc to add to a base datetime, rather than a list of actual datetimes
        period = end_dt - start_dt
        dt_difference = getattr(period, settings.PENDULUM_FUNCS[precision])  # period.in_seconds(), .in_hours(), etc
        increment_list = [x for x in range(dt_difference())]

        # Binary search for a planetary return to a specific precision
        midpoint_dt = None
        while len(increment_list) >= 1:
            midpoint_dt = start_dt
            midpoint_index = len(increment_list) // 2
            midpoint_dt = midpoint_dt.add(**{precision: increment_list[midpoint_index]})  # e.g. .add(hours=some_int)
            return_array = self._get_planet_array(body, midpoint_dt)
            test_pos = return_array[0]
            if self._is_past(test_pos, natal_longitude, harmonic) == True:
                increment_list = increment_list[: (midpoint_index - 1)]
            else:
                increment_list = increment_list[(midpoint_index + 1):]

        return midpoint_dt

    def _get_return_time_list(self, body, radix_position, dt, harmonic, return_quantity):
        """Calculate a list of harmonic return times to second precision.
        :param body: Int 0-9
        :param radix_position: Float 0-359.9~
        :param dt: Pendulum.Datetime instance
        :param harmonic: Int 1-36.
        :param return_quantity: Int
        :returns: List of pendulum.datetimes
        """
        return_time_list_hour_precision = list()
        initial_return_hour = self._get_nearest_return(body, radix_position, dt, harmonic)
        return_time_list_hour_precision.append(initial_return_hour)

        delta = (settings.ORBITAL_PERIODS_HOURS[body] // harmonic) - 24  # Approx how far away next return is
        buffer = delta // 2.5  # Create a window of a few hours on either side of delta
        period_begin = initial_return_hour.add(hours=delta - buffer)
        period_end = initial_return_hour.add(hours=delta + buffer)

        while len(return_time_list_hour_precision) < return_quantity:
            next_return = self._find_harmonic_in_date_range(harmonic, body, radix_position, period_begin, period_end,
                                                            precision='hours')

            if next_return:
                return_time_list_hour_precision.append(next_return)
            else:
                raise RuntimeError(f'Failed to find a return between {period_begin} and {period_end}')
            period_begin = next_return.add(hours=delta - buffer)
            period_end = next_return.add(hours=delta + buffer)

        return_time_list_second_precision = list()

        for hour in return_time_list_hour_precision:
            period_begin = hour.subtract(hours=2)
            period_end = hour.add(hours=2)
            match = self._find_harmonic_in_date_range(harmonic, body, radix_position, period_begin, period_end,
                                                      precision='seconds')
            return_time_list_second_precision.append(match)

        return return_time_list_second_precision

    def _generate_return_list(self, radix, geo_longitude, geo_latitude, date, body, harmonic, return_quantity):
        """Generate a list of harmonic return datetimes.
        :param radix: ChartData instance
        :param date: pendulum.datetime
        :param body: Int 0-9
        :param harmonic: Int 1-36
        :param return_quantity: Int
        :returns: List of second-precision harmonic returns"""

        body_name = settings.INT_TO_STRING_PLANET_MAP[body]
        radix_position = radix.planets_ecliptic[body_name][0]
        # date = date.in_tz('UTC')

        self.relocate(radix, geo_longitude, geo_latitude, date.tz)
        geo_longitude = radix.sidereal_framework.geo_longitude
        geo_latitude = radix.sidereal_framework.geo_latitude
        return_time_list = self._get_return_time_list(body, radix_position, date, harmonic, return_quantity)

        return_chart_list = list()
        for chart_time in return_time_list:
            chart = self.create_chartdata(chart_time, geo_longitude, geo_latitude)
            return_chart_list.append(chart)

        for chart in return_chart_list:
            chart.local_datetime = chart.local_datetime.in_tz(date.tz)
        return return_chart_list

    # =============================================================================================================== #
    # =======================================   Internal calculations   ============================================= #
    # =============================================================================================================== #

    def _calculate_julian_day(self, dt_utc):
        """Calculate Julian Day for a given UTC datetime.
        :param dt_utc: pendulum.datetime in UTC
        :returns: Float"""
        decimal_hour_utc = self.convert_dms_to_decimal(dt_utc.hour, dt_utc.minute, dt_utc.second)
        time_julian_day = self.lib.get_julian_day(dt_utc.year, dt_utc.month, dt_utc.day, decimal_hour_utc, 1)
        return time_julian_day

    def _calculate_LST(self, dt, decimal_longitude):
        """Calculate local sidereal time for date, time, location of event.
        :param dt: pendulum.datetime in UTC
        :param decimal_longitude: Float
        :returns: Float"""

        year, month, day = dt.year, dt.month, dt.day
        decimal_hour = self.convert_dms_to_decimal(dt.hour, dt.minute, dt.second)

        # Julian Day number at midnight
        julian_day_0_GMT = self.lib.get_julian_day(year, month, day, 0, 1)

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

    def _calculate_svp(self, julian_day):
        """Calculate the Sidereal Vernal Point for a given Julian Day.
        :param julian_day: Float
        :returns: Float"""

        svp = c_double()  # Destination for the Swiss Ephemeris function to write to
        errorstring = create_string_buffer(126)
        ayanamsa_return = self.lib.get_ayanamsa_UT(julian_day, settings.SIDEREALMODE, svp, errorstring)
        if ayanamsa_return < 0:
            logger.error("Error retrieving ayanamsa: " + str(errorstring))
        return 30 - svp.value

    def _calculate_obliquity(self, julian_day):
        """Calculate the obliquity of the zodiac for a given Julian Day.
        :param julian_day: Float
        :returns: Float"""

        obliquity_array = (c_double * 6)()
        errorstring = create_string_buffer(126)

        # -1 is the special "planetary body" for calculating obliquity
        self.lib.calculate_planets_UT(julian_day, -1, settings.SIDEREALMODE, obliquity_array, errorstring)
        if errorstring.value:
            logger.warning(f'Error encountered in {self._get_planet_array.__name__}: {errorstring.value}')
        return obliquity_array[0]

    def _get_planet_array(self, body_number, dt):
        """Get Swiss Ephemeris output for a given body and datetime. Accepts Julian Day or pendulum.datetime.
        :param body_number: String or Int
        :param dt: Julian Day or pendulum.datetime instance in any timezone
        :returns: Array of 6 c_doubles"""

        if type(body_number) == str:
            body_number = settings.STRING_TO_INT_PLANET_MAP[body_number]
        if type(dt) == float:
            jd = dt
        else:
            dt = dt.in_tz('UTC')
            decimal_hour = self.convert_dms_to_decimal(dt.hour, dt.minute, dt.second)
            jd = self.lib.get_julian_day(dt.year, dt.month, dt.day, decimal_hour, 1)

        ret_array = (c_double * 6)()
        errorstring = create_string_buffer(126)
        self.lib.calculate_planets_UT(jd, body_number, settings.SIDEREALMODE, ret_array, errorstring)
        # if errorstring.value:
        #     print(f'Error encountered in {self._get_planet_array.__name__}: {errorstring.value}')
        return ret_array

    def _initialize_sidereal_framework(self, utc_datetime, local_datetime, geo_longitude, geo_latitude):
        """Initialize an instance of the SiderealFramework class to use in calculations inside a ChartData instance.
        :param utc_datetime: pendulum.datetime
        :param local_datetime: pendulum.datetime
        :param geo_longitude: Float
        :param geo_latitude: Float
        :returns: SiderealFramework instance"""

        julian_day = self._calculate_julian_day(utc_datetime)
        LST = self._calculate_LST(utc_datetime, geo_longitude)
        ramc = LST * 15
        svp = self._calculate_svp(julian_day)
        obliquity = self._calculate_obliquity(julian_day)
        framework = SiderealFramework(geo_longitude, geo_latitude, LST, ramc, svp, obliquity)

        return framework

    def _calculate_prime_vertical_longitude(self, planet_longitude, planet_latitude, ramc, obliquity, svp,
                                            geo_latitude):
        """Calculate a planet's prime vertical longitude.
        :param planet_longitude: Float
        :param planet_latitude: Float
        :param ramc: Float
        :param obliquity: Float
        :param svp: Float
        :param geo_latitude: Float
        :returns: Int Campanus house, Float prime vertical longitude"""

        # Variable names reference the original angularity spreadsheet posted on Solunars.com.
        # Most do not have official names and are intermediary values used elsewhere.
        calc_ax = (cos(radians(planet_longitude
                               + (360 - (330 + svp)))))

        precessed_declination = (degrees(asin
                                         (sin(radians(planet_latitude))
                                          * cos(radians(obliquity))
                                          + cos(radians(planet_latitude))
                                          * sin(radians(obliquity))
                                          * sin(radians(planet_longitude
                                                        + (360 - (330 + svp)))))))

        calc_ay = (sin(radians((planet_longitude
                                + (360 - (330 + svp)))))
                   * cos(radians(obliquity))
                   - tan(radians(planet_latitude))
                   * sin(radians(obliquity)))

        calc_ayx_deg = degrees(atan(calc_ay / calc_ax))

        if calc_ax < 0:
            precessed_right_ascension = calc_ayx_deg + 180
        elif calc_ay < 0:
            precessed_right_ascension = calc_ayx_deg + 360
        else:
            precessed_right_ascension = calc_ayx_deg

        hour_angle_degree = ramc - precessed_right_ascension

        calc_cz = (degrees(atan(1
                                / (cos(radians(geo_latitude))
                                   / tan(radians(hour_angle_degree))
                                   + sin(radians(geo_latitude))
                                   * tan(radians(precessed_declination))
                                   / sin(radians(hour_angle_degree))))))

        calc_cx = (cos(radians(geo_latitude))
                   * cos(radians(hour_angle_degree))
                   + sin(radians(geo_latitude))
                   * tan(radians(precessed_declination)))

        campanus_longitude = 90 - calc_cz if (calc_cx < 0) else 270 - calc_cz

        planet_pvl_house = (int(campanus_longitude / 30) + 1)
        return [planet_pvl_house, campanus_longitude]

    def _calculate_right_ascension(self, planet_latitude, planet_longitude, svp, obliquity):
        """Calculate a planet's right ascension.
        :param planet_latitude: Float
        :param planet_longitude: Float
        :param svp: Float
        :param obliquity: Float
        :returns: Float right ascension"""

        circle_minus_ayanamsa = 360 - (330 + svp)

        precessed_longitude = planet_longitude + circle_minus_ayanamsa
        calcs_ay = (sin(radians(precessed_longitude)) * cos(radians(obliquity))
                    - tan(radians(planet_latitude)) * sin(radians(obliquity)))
        calcs_ax = cos(radians(precessed_longitude))
        calcs_o = degrees(atan(calcs_ay / calcs_ax))

        if calcs_ax < 0:
            precessed_right_ascension = calcs_o + 180
        elif calcs_ay < 0:
            precessed_right_ascension = calcs_o + 360
        else:
            precessed_right_ascension = calcs_o

        return precessed_right_ascension
