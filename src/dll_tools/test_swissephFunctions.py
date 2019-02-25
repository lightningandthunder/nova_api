from unittest import TestCase
import ctypes as c

from dll_tools import SwissephFunctions

class TestSwissephFunctions(TestCase):

    def setUp(self):
        super()
        self.ephemeris_path = 'swe/ephemeris'
        self.lib = SwissephFunctions(self.ephemeris_path)

    def tearDown(self):
        self.lib.close()

    def test_init(self):
        assert self.lib
        assert self.lib.ephemeris_path == self.ephemeris_path

    def test__format_ephemeris_path(self):
        pass

    def test__load_library(self):
        pass

    def test__wrap_set_ephemeris_path(self):
        pass

    def test__wrap_set_sidereal_mode(self):
        pass

    def test__wrap_local_time_to_UTC(self):
        pass

    def test__wrap_get_julian_day(self):
        pass

    def test__wrap_reverse_julian_day(self):
        pass

    def test__wrap_get_sidereal_time_UT(self):
        pass

    def test__wrap_calculate_planets_UT(self):
        pass

    def test__wrap_get_ayanamsa_UT(self):
        pass

    def test__wrap_calculate_houses(self):
        pass

    def test__wrap_close(self):
        pass
