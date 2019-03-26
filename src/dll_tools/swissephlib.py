import ctypes
from ctypes import c_char_p, c_int, c_int32, c_double, POINTER, CDLL
import os
import platform
import struct
import pathlib
import threading

import settings
# from LibThreadManager import LibThreadManager
from logging import getLogger

logger = getLogger(__name__)

"""
Wraps Swiss Ephemeris library functions. Only one instance should exist at a time.
"""

class SwissephLib:
    def __init__(self):
        self.swe_lib = self._load_library()
        # self.thread = LibThreadManager()

        # Wrap Swiss Ephemeris functions and expose as public methods
        self.set_ephemeris_path = self.swe_lib.swe_set_ephe_path
        self.set_ephemeris_path.argtypes = [c_char_p]
        self.set_ephemeris_path.restype = None
        self.set_ephemeris_path.__doc__ = ("""
        Sets the filepath of the ephemerides for the DLL functions.
        :param ephemeris_path: c_char_p
        :returns: None
        """)

        self.set_sidereal_mode = self.swe_lib.swe_set_sid_mode
        self.set_sidereal_mode.argtypes = [c_int32, c_double, c_double]
        self.set_sidereal_mode.restype = None
        self.set_sidereal_mode.__doc__ = ("""
        Sets the sidereal mode of the Swiss Ephemeris library to Fagan/Allen.
        :param sid_mode: c_int32 (should be 0)
        :param t0: c_double (should be 0)
        :param ayan_t0: c_double (should be 0)
        :returns: None
        """)

        self.get_julian_day = self.swe_lib.swe_julday
        self.get_julian_day.argtypes = [c_int, c_int, c_int, c_double, c_int]
        self.get_julian_day.restype = c_double
        self.get_julian_day.__doc__ = ("""
        Calculates julian day number (in UTC) from wall-clock time (in UTC)
        :param year: c_int
        :param month: c_int
        :param day: c_int
        :param fractional_hour: c_double
        :param calendar flag: c_int (should be 1)
        :returns: c_double
        """)

        self.reverse_julian_day = self.swe_lib.swe_revjul
        self.reverse_julian_day.argtypes = [c_double, c_int, POINTER(c_int), POINTER(c_int),
                                            POINTER(c_int), POINTER(c_double)]
        self.reverse_julian_day.restype = None
        self.reverse_julian_day.__doc__ = ("""
        Calculates year, month, day, fractional hour from Julian Day.
        :param julian_day: c_double
        :param calendar_flag: c_int (should be 1)
        :param year: POINTER(c_int)
        :param month: POINTER(c_int)
        :param day: POINTER(c_int)
        :param fractional_hour: POINTER(c_double)
        :returns: None 
        """)

        self.get_sidereal_time_UTC = self.swe_lib.swe_sidtime
        self.get_sidereal_time_UTC.argtypes = [c_double]
        self.get_sidereal_time_UTC.restype = c_double
        self.get_sidereal_time_UTC.__doc__ = ("""
        Calculates sidereal time at the Greenwich Meridian.
        :param julian_day_in_UTC: c_double
        :rtype c_double
        :returns: c_double
        .. note:: Must be converted to local time for use in mundane calculations.
        """)

        self.calculate_planets_UT = self.swe_lib.swe_calc_ut
        self.calculate_planets_UT.argtypes = [c_double, c_int, c_int32,
                                              POINTER(c_double), c_char_p]
        self.calculate_planets_UT.restype = None
        self.calculate_planets_UT.__doc__ = ("""
        Calculates planetary positions.
        :param julian_day_UTC: c_double
        :param body_number: c_int
        :param zodiacal_flag: c_int32
        :param return_array: POINTER(c_double) (Requires array of 6 doubles)
        :param error_string: c_char_p (String to write errors to)
        :returns: None 
        """)

        self.get_ayanamsa_UT = self.swe_lib.swe_get_ayanamsa_ex_ut
        self.get_ayanamsa_UT.argtypes = [c_double, c_int32,
                                         POINTER(c_double), c_char_p]
        self.get_ayanamsa_UT.restype = c_int32
        self.get_ayanamsa_UT.__doc__ = ("""
        Calculates ayanamsa.
        :param julian_day_UTC: c_double
        :param sidereal_flag: c_int32
        :param result_double: POINTER(c_double) (Pointer to a double to write to)
        :param error_string: c_char_p (String to write errors to)
        :returns: Ayanamsa (positive int or -1 for error)
        :rtype: c_int32 
        """)

        self.calculate_houses = self.swe_lib.swe_houses_ex
        self.calculate_houses.argtypes = [c_double, c_int32, c_double, c_double,
                                          c_int, POINTER(c_double), POINTER(c_double)]
        self.calculate_houses.restype = None
        self.calculate_houses.__doc__ = ("""
        Calculates Ascendant, MC, and house cusps.
        :param julian_day_UTC: c_double
        :param ephemeris_flag: c_int32
        :param geographic_latitude: c_double
        :param geographic_longitude: c_double
        :param int_house_system: c_int (should be 'C')
        :param array_cusps: POINTER(c_double) (Array of 12 doubles to write to)
        :param array_asc_mc: POINTER(c_double) (Array of 10 doubles to write to)
        :returns: None 
        """)

        self.close = self.swe_lib.swe_close
        self.close.argtypes = None
        self.close.restype = None
        self.close.__doc__ = ("""
        Closes the connection to the ephemeris.
        :param swe_lib: CDLL or WinDLL
        :returns: None
        """)

        self.ephemeris_path = self._get_ephemeris_path()
        self.set_ephemeris_path(self.ephemeris_path)
        self.set_sidereal_mode(0, 0, 0)



    def _get_library_for_platform(self):
        """
        Get the absolute path of the Swiss Ephemeris library version needed for current system.
        """

        plat = platform.system()
        bit_mode = struct.calcsize("P") * 8  # Yields 32-bit or 64-bit according to OS
        if plat == 'Windows':
            if bit_mode == 32:
                library_name = 'swedll32.dll'
            else:
                library_name = 'swedll64.dll'
        elif plat == 'Linux':
            library_name = 'libswe.so'
        else:
            raise OSError('OS must be Windows or Linux')

        return library_name

    def _load_library(self):
        plat = platform.system()
        library_with_extension = self._get_library_for_platform()
        library_sub_dir = os.path.join('swe/dll', library_with_extension)
        path_to_library = os.path.join(os.path.dirname(__file__), library_sub_dir)
        swe_lib = None
        try:
            if plat == 'Windows':
                swe_lib = ctypes.windll.LoadLibrary(path_to_library)
                logger.info(msg='Loaded Swiss Ephemeris library for Windows.')
            elif plat == 'Linux':
                swe_lib = CDLL(path_to_library)
                logger.info(msg='Loaded Swiss Ephemeris library for Linux.')
            else:
                raise OSError('OS must be Windows or Linux')
        except OSError as e:
            logger.error(e)
        finally:
            if swe_lib is None:
                raise ImportError("Unable to load Swiss Ephemeris Library.")
            else:
                return swe_lib

    def _get_ephemeris_path(self):
        path = os.path.join('../', settings.EPHEMERIS_PATH)
        e_path = path.encode('utf-8')
        e_pointer = c_char_p(e_path)
        return e_pointer
