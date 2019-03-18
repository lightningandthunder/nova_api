from math import fabs
from logging import getLogger

logger = getLogger(__name__)
"""
A class created by the ChartManager singleton representing chart data for a given date, time, and location.
"""

class ChartData:
    def __init__(self, local_datetime, utc_datetime, julian_day):
        self.local_datetime = local_datetime
        self.utc_datetime = utc_datetime
        self.julian_day = julian_day
        self.sidereal_framework = None
        self.cusps_longitude = None
        self.angles_longitude = None

        # Ecliptical longitude, celestial latitude, distance, speed in long, speed in lat, speed in dist
        self.planets_ecliptic = None

        # House placement, decimal longitude (out of 360*)
        self.planets_mundane = None

        # Decimal longitude (out of 360*)
        self.planets_right_ascension = None

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

    def get_angles_longitude(self):
        return self.angles_longitude

    def get_cusps_longitude(self):
        return self.cusps_longitude


