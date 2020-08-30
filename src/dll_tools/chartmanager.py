import copy
import pendulum
from logging import getLogger
from typing import Tuple, List, Union
from ctypes import c_double, create_string_buffer
from math import sin, cos, tan, asin, atan, degrees, radians, fabs, ceil

from src.models.chartdata import ChartData
from src.models.sidereal_framework import SiderealFramework
from src.dll_tools.swissephlib import SwissephLib
from src.dll_tools.tests.functionality_tests import run_tests

from src import settings

logger = getLogger(__name__)


class ChartManager:
    """
    Singleton that manages chart data sets. Initialized with an instance of a SwissephLib library wrapper class.
    """

    def __init__(self):
        self.lib = SwissephLib()
        run_tests(self)

    def __del__(self):
        self.lib.close()

    # =============================================================================================================== #
    # =========================================   Public functions   ================================================ #
    # =============================================================================================================== #

    def create_chartdata(self, local_datetime: pendulum.datetime, geo_longitude: float,
                         geo_latitude: float, place_name: str = None) -> ChartData:
        """Create a ChartData instance representing an astrological chart."""

        utc_datetime = local_datetime.in_tz("UTC")
        julian_day = self._calculate_julian_day(utc_datetime)
        chart = ChartData(local_datetime, utc_datetime, julian_day)
        chart.sidereal_framework = self._initialize_sidereal_framework(utc_datetime, geo_longitude, geo_latitude)
        chart.planets_ecliptic = self._populate_ecliptic_values(julian_day)
        chart.planets_mundane = self._populate_mundane_values(chart)
        chart.planets_right_ascension = self._populate_right_ascension_values(chart)
        chart.angles_longitude, chart.cusps_longitude = self._populate_ecliptical_angles_and_cusps(chart)
        chart.place_name = place_name

        return chart

    def relocate(self, radix: ChartData, geo_longitude: float, geo_latitude: float, timezone: str) -> None:
        """Recalculate prime vertical longitude, right ascension, and ecliptical angles and cusps against a new
         sidereal framework. Done on the radix chart in place."""

        radix.sidereal_framework.geo_longitude = geo_longitude
        radix.sidereal_framework.geo_latitude = geo_latitude
        radix.local_datetime = radix.local_datetime.in_tz(timezone)
        radix.planets_mundane = self._populate_mundane_values(radix)
        radix.planets_right_ascension = self._populate_right_ascension_values(radix)
        radix.angles_longitude, radix.cusps_longitude = self._populate_ecliptical_angles_and_cusps(radix)

    def precess(self, radix: ChartData, transit_chart: ChartData) -> None:
        """Recalculate prime vertical longitude, right ascension, and ecliptical angles and cusps against a transiting
        chart's sidereal framework. Done on the radix chart in place."""

        radix.sidereal_framework = transit_chart.sidereal_framework
        radix.local_datetime = radix.local_datetime.in_tz(transit_chart.local_datetime.tz)
        radix.tz = transit_chart.local_datetime.tz
        radix.planets_mundane = self._populate_mundane_values(radix)
        radix.planets_right_ascension = self._populate_right_ascension_values(radix)
        radix.angles_longitude, radix.cusps_longitude = self._populate_ecliptical_angles_and_cusps(radix)

    def get_transit_sensitive_charts(self, radix: ChartData, local_dt: pendulum.datetime, geo_longitude: float,
                                     geo_latitude: float) -> dict:
        # TODO: Test me

        transits = self.create_chartdata(local_dt, geo_longitude, geo_latitude)

        local_natal = copy.deepcopy(radix)
        self.relocate(local_natal, geo_longitude, geo_latitude, local_dt.tz)

        ssr_dt = local_dt
        active_ssr = self._generate_return_list(radix=local_natal, geo_longitude=geo_longitude,
                                                geo_latitude=geo_latitude, date=ssr_dt,
                                                body=0, harmonic=1, return_quantity=1)[0]

        # Re-generate if the SSR identified is in the future
        if active_ssr.local_datetime > local_dt:
            ssr_dt = ssr_dt.subtract(years=1)
            active_ssr = self._generate_return_list(radix=local_natal, geo_longitude=geo_longitude,
                                                    geo_latitude=geo_latitude, date=ssr_dt,
                                                    body=0, harmonic=1, return_quantity=1)[0]

        # Secondary progressions
        sp_radix = self.get_progressions(radix, local_dt, geo_longitude, geo_latitude)
        sp_ssr = self.get_progressions(active_ssr, local_dt, geo_longitude, geo_latitude)

        return {
            "radix": radix,
            "local_natal": local_natal,
            "sp_radix": sp_radix,
            "ssr": active_ssr,
            "sp_ssr": sp_ssr,
            "transits": transits,
        }

    def get_progressions(self, radix: ChartData, local_dt: pendulum.datetime, geo_longitude: float,
                         geo_latitude: float) -> ChartData:
        # TODO: Test me

        progressed_time = (local_dt.in_tz('UTC') - radix.utc_datetime).in_minutes() * settings.Q2
        progressed_dt = radix.utc_datetime.add(minutes=progressed_time)

        # Create chart based on progressed date
        chart = self.create_chartdata(progressed_dt, geo_longitude, geo_latitude)

        # Precess chart into actual date
        chart.local_datetime = local_dt
        chart.utc_datetime = local_dt.in_tz('UTC')
        chart.sidereal_framework = self._initialize_sidereal_framework(local_dt.in_tz('UTC'), geo_longitude,
                                                                       geo_latitude)
        chart.planets_mundane = self._populate_mundane_values(chart)
        chart.planets_right_ascension = self._populate_right_ascension_values(chart)
        return chart

    def generate_radix_return_pairs(self, radix: ChartData, geo_longitude: float,
                                    geo_latitude: float, date: pendulum.datetime,
                                    body: int, harmonic: int,
                                    return_quantity: int, place_name: str = None) -> List[Tuple[ChartData, ChartData]]:

        return_list = self._generate_return_list(radix, geo_longitude, geo_latitude, date, body, harmonic,
                                                 return_quantity)
        pairs = []
        for solunar_return in return_list:
            radix_copy = copy.deepcopy(radix)
            solunar_return.place_name = place_name
            self.precess(radix_copy, solunar_return)
            pairs.append((radix_copy, solunar_return))
        return pairs

    @staticmethod
    def get_sign(longitude: float) -> str:
        """Determine astrological sign from unsigned longitude."""

        zodiac = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
                  "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        key = int(longitude / 30)
        return zodiac[key]

    @staticmethod
    def convert_dms_to_decimal(degree: int, minute: int, second: int) -> float:
        """Convert hour/degree, minute, and second into a decimal hour or decimal degree."""

        return degree + (minute / 60) + (second / 3600)

    @staticmethod
    def convert_decimal_to_dms(decimal: float) -> Tuple[int, int, int]:
        """Convert a decimal hour or degree into degree/hour, minute, second."""

        degree = int(decimal)
        minute = int(fabs((decimal - degree) * 60))
        second = int((fabs((decimal - degree) * 60) - int(fabs((decimal - degree) * 60))) * 60)
        return degree, minute, second

    # =============================================================================================================== #
    # ============================   Functions to populate coordinate data sets   =================================== #
    # =============================================================================================================== #

    def _populate_ecliptic_values(self, julian_day: float) -> dict:
        """Calculate ecliptical longitude for planets."""

        errorstring = create_string_buffer(126)
        returnarray = [(c_double * 6)() for _ in range(10)]

        ecliptic_dict = dict()
        for body_number, body_name in enumerate(settings.INT_TO_STRING_PLANET_MAP):
            self.lib.calculate_planets_UT(julian_day, body_number, settings.SIDEREALMODE,
                                          returnarray[body_number], errorstring)
            ecliptic_dict[body_name] = returnarray[body_number]
            if errorstring.value:
                logger.warning("Error calculating ecliptic values: " + str(errorstring.value))

        return ecliptic_dict

    def _populate_mundane_values(self, chart: ChartData) -> dict:
        """Calculate prime vertical longitude for planets."""

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

    def _populate_right_ascension_values(self, chart: ChartData) -> dict:
        """Calculate right ascension values for planets."""

        right_ascension_dict = dict()
        for body_name in settings.INT_TO_STRING_PLANET_MAP:
            planet_longitude = chart.planets_ecliptic[body_name][0]
            planet_latitude = chart.planets_ecliptic[body_name][1]
            planet_right_ascension = self._calculate_right_ascension(planet_latitude, planet_longitude,
                                                                     chart.sidereal_framework.svp,
                                                                     chart.sidereal_framework.obliquity)

            right_ascension_dict[body_name] = planet_right_ascension
        return right_ascension_dict

    def _populate_ecliptical_angles_and_cusps(self, chart: ChartData) -> Tuple[dict, dict]:
        """Calculate house cusps and ecliptical longitudes of angles in the Campanus system."""

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
            "Eq Asc": house_array[4],
        }

        return angles_longitude, cusps_longitude

    # =============================================================================================================== #
    # =============================   Functions for harmonic return calculation   =================================== #
    # =============================================================================================================== #

    def _is_past(self, transit_longitude: float, natal_longitude: float, harmonic: int) -> bool:
        """Determine if a transit longitude is 'past' a radical one in the context of a harmonic."""

        harmonic_of_natal_pos = self._get_closest_harmonic_pos(natal_longitude, transit_longitude, harmonic)
        half_coordinate_range = (360 / harmonic) / 2
        distance = fabs(transit_longitude - harmonic_of_natal_pos)

        past = True if transit_longitude > harmonic_of_natal_pos else False
        # If the longitudes are in same half of range, expected behavior; otherwise, reverse
        return past if distance <= half_coordinate_range else not past

    def _get_closest_harmonic_pos(self, radix_pos: float, transit_pos: float, harmonic: int) -> float:
        """Calculate the closest valid harmonic position of a radical longitude to a transiting longitude."""

        harmonic_positions = set()
        coordinate_range = 360 / harmonic
        next_harmonic_pos = (radix_pos + coordinate_range) % 360
        while next_harmonic_pos not in harmonic_positions:
            harmonic_positions.add(next_harmonic_pos)
            next_harmonic_pos = (next_harmonic_pos + coordinate_range) % 360

        return min(harmonic_positions, key=lambda x: abs(x - transit_pos))

    def _get_nearest_return(self, body: int, radix_position: float, dt: pendulum.datetime,
                            harmonic: int) -> pendulum.datetime:
        """Get nearest harmonic return date to a given date, to start a list of return dates."""

        delta = ceil(settings.ORBITAL_PERIODS_HOURS[body] / harmonic)
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

    def _find_harmonic_in_date_range(self, harmonic: int, body: int, natal_longitude: float,
                                     start_dt: pendulum.datetime, end_dt: pendulum.datetime,
                                     precision: str) -> pendulum.datetime:
        """Find a harmonic solunar return within a pair of dates, to a specified precision."""

        pendulum_precision_map = {
            'seconds': 'in_seconds',
            'minutes': 'in_minutes',
            'hours': 'in_hours',
            'days': 'in_days',
            'weeks': 'in_weeks',
            'months': 'in_months',
            'years': 'in_years'
        }

        if type(harmonic) != int:
            raise ValueError('Cannot calculate harmonic returns with a non-integer harmonic')
        if precision not in pendulum_precision_map.keys():
            raise ValueError('Precision must be a unit of time as a string: \'hours\', \'seconds\', etc')

        # Ensure there is a valid value in range
        while True:
            end_pos = self._get_planet_longitude(body, end_dt)
            if not self._is_past(end_pos, natal_longitude, harmonic):
                # Need to move forward in time
                start_dt = end_dt
                end_dt = end_dt.add(hours=1)

            else:
                break  # valid

        period = end_dt - start_dt

        # Binary search for a planetary return to a specific precision
        ceiling = getattr(period, pendulum_precision_map[precision])()  # period.in_seconds(), .in_hours(), etc
        floor = 0
        test_dt = None
        while ceiling > floor:
            test_dt = start_dt
            midpoint = ((ceiling - floor) // 2) + floor
            test_dt = test_dt.add(**{precision: midpoint})  # e.g. .add(hours=some_int)
            test_pos = self._get_planet_longitude(body, test_dt)
            if self._is_past(test_pos, natal_longitude, harmonic):
                ceiling = midpoint - 1
            else:
                floor = midpoint + 1

        return test_dt

    def _get_return_time_list(self, body: int, radix_position: float, dt: pendulum.datetime, harmonic: int,
                              return_quantity: float) -> List[pendulum.datetime]:
        """Calculate a list of harmonic return times to second precision."""

        return_time_list_hour_precision = []
        initial_return_hour = self._get_nearest_return(body, radix_position, dt, harmonic)
        return_time_list_hour_precision.append(initial_return_hour)

        delta = (settings.ORBITAL_PERIODS_HOURS[body] // harmonic) - 24  # Approx how far away next return is
        buffer = delta // 2  # Create a window of a few hours on either side of delta
        period_begin = initial_return_hour.add(hours=delta - buffer)
        period_end = initial_return_hour.add(hours=delta + buffer)

        while len(return_time_list_hour_precision) < return_quantity:
            next_return = self._find_harmonic_in_date_range(harmonic, body, radix_position, period_begin, period_end,
                                                            precision='seconds')

            if next_return:
                return_time_list_hour_precision.append(next_return)
            else:
                raise RuntimeError(f'Failed to find a return between {period_begin} and {period_end}')

            period_begin = next_return.add(hours=delta - buffer)
            period_end = next_return.add(hours=delta + buffer)

        return_time_list_second_precision = list()

        for hour in return_time_list_hour_precision:
            period_begin = hour.subtract(hours=6)
            period_end = hour.add(hours=6)
            match = self._find_harmonic_in_date_range(harmonic, body, radix_position, period_begin, period_end,
                                                      precision='seconds')
            return_time_list_second_precision.append(match)

        return return_time_list_second_precision

    def _generate_return_list(self, radix: ChartData, geo_longitude: float, geo_latitude: float,
                              date: pendulum.datetime, body: int, harmonic: int,
                              return_quantity: int) -> List[ChartData]:
        """Generate a list of harmonic return datetimes."""

        body_name = settings.INT_TO_STRING_PLANET_MAP[body]
        radix_position = radix.planets_ecliptic[body_name][0]
        # date = date.in_tz('UTC')

        self.relocate(radix, geo_longitude, geo_latitude, date.tz)
        geo_longitude = radix.sidereal_framework.geo_longitude
        geo_latitude = radix.sidereal_framework.geo_latitude
        return_time_list = self._get_return_time_list(body, radix_position, date, harmonic, return_quantity)

        return_chart_list = []
        for chart_time in return_time_list:
            chart = self.create_chartdata(chart_time, geo_longitude, geo_latitude)
            return_chart_list.append(chart)

        for chart in return_chart_list:
            chart.local_datetime = chart.local_datetime.in_tz(date.tz)
        return return_chart_list

    # =============================================================================================================== #
    # =======================================   Internal calculations   ============================================= #
    # =============================================================================================================== #

    def _calculate_julian_day(self, dt_utc: pendulum.datetime) -> float:
        """Calculate Julian Day for a given UTC datetime."""

        decimal_hour_utc = self.convert_dms_to_decimal(dt_utc.hour, dt_utc.minute, dt_utc.second)
        time_julian_day = self.lib.get_julian_day(dt_utc.year, dt_utc.month, dt_utc.day, decimal_hour_utc, 1)
        return time_julian_day

    def _calculate_LST(self, dt: pendulum.datetime, decimal_longitude: float) -> float:
        """Calculate local sidereal time for date in UTC, time, location of event."""

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

    def _calculate_svp(self, julian_day: float) -> float:
        """Calculate the Sidereal Vernal Point for a given Julian Day."""

        svp = c_double()  # Destination for the Swiss Ephemeris function to write to
        errorstring = create_string_buffer(126)
        ayanamsa_return = self.lib.get_ayanamsa_UT(julian_day, settings.SIDEREALMODE, svp, errorstring)
        if ayanamsa_return < 0:
            logger.error("Error retrieving ayanamsa: " + str(errorstring.value))
        return 30 - svp.value

    def _calculate_obliquity(self, julian_day: float) -> float:
        """Calculate the obliquity of the zodiac for a given Julian Day."""

        obliquity_array = (c_double * 6)()
        errorstring = create_string_buffer(126)

        # -1 is the special "planetary body" for calculating obliquity
        self.lib.calculate_planets_UT(julian_day, -1, settings.SIDEREALMODE, obliquity_array, errorstring)
        if errorstring.value:
            logger.warning("Error calculating obliquity: " + str(errorstring.value))
        return obliquity_array[0]

    def _get_planet_longitude(self, body_number: int, dt: Union[float, pendulum.datetime]) -> float:
        """Get Swiss Ephemeris output for a given body and datetime."""

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
        if errorstring.value:
            logger.warning("Error calculating planet longitude: " + str(errorstring.value))
        return ret_array[0]

    def _initialize_sidereal_framework(self, utc_datetime: pendulum.datetime,
                                       geo_longitude: float, geo_latitude: float) -> SiderealFramework:
        """Initialize an instance of the SiderealFramework class to use in calculations inside a ChartData instance."""

        julian_day = self._calculate_julian_day(utc_datetime)
        LST = self._calculate_LST(utc_datetime, geo_longitude)
        ramc = LST * 15
        svp = self._calculate_svp(julian_day)
        obliquity = self._calculate_obliquity(julian_day)
        framework = SiderealFramework(geo_longitude=geo_longitude, geo_latitude=geo_latitude,
                                      LST=LST, ramc=ramc, svp=svp, obliquity=obliquity)

        return framework

    def _calculate_prime_vertical_longitude(self, planet_longitude: float, planet_latitude: float, ramc: float,
                                            obliquity: float, svp: float, geo_latitude) -> float:
        """Calculate a planet's prime vertical longitude."""

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

    def _calculate_right_ascension(self, planet_latitude: float, planet_longitude: float,
                                   svp: float, obliquity: float) -> float:
        """Calculate a planet's right ascension."""

        # Variable names reference the original angularity spreadsheet posted on Solunars.com.
        # Most do not have official names and are intermediary values used elsewhere.
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
