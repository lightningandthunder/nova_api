from ctypes import c_char_p, c_int, c_int32, c_double, POINTER, windll, CDLL, WinError
import os
import platform
import struct
import settings

from logging import getLogger

logger = getLogger(__name__)

"""
Wraps Swiss Ephemeris library functions.
"""


class SwissephLib:
    def __init__(self):
        self.ephemeris_path = self._get_ephemeris_path()
        self.swe_lib = self._load_library()

        # Wrap Swiss Ephemeris functions and expose as public methods
        self.set_ephemeris_path = self._wrap_set_ephemeris_path(self.swe_lib)
        self.set_sidereal_mode = self._wrap_set_sidereal_mode(self.swe_lib)
        self.get_julian_day = self._wrap_get_julian_day(self.swe_lib)
        self.reverse_julian_day = self._wrap_reverse_julian_day(self.swe_lib)
        self.get_sidereal_time_UT = self._wrap_get_sidereal_time_UT(self.swe_lib)
        self.calculate_planets_UT = self._wrap_calculate_planets_UT(self.swe_lib)
        self.get_ayanamsa_UT = self._wrap_get_ayanamsa_UT(self.swe_lib)
        self.calculate_houses = self._wrap_calculate_houses(self.swe_lib)
        self.close = self._wrap_close(self.swe_lib)

    def __enter__(self):
        self.set_ephemeris_path(self.ephemeris_path)
        self.set_sidereal_mode(0, 0, 0)
        return self

    def __exit__(self, _type, value, traceback):
        self.close()

    def _get_library_relpath(self, library_dir):
        """
        Get the absolute path of the Swiss Ephemeris library version needed for current system.
        """

        plat = platform.system()
        bit_mode = struct.calcsize("P") * 8  # Yields 32-bit or 64-bit according to OS
        if plat == 'Windows':
            if bit_mode == 32:
                library_relpath = os.path.join(library_dir, 'swedll32.dll')
            else:
                library_relpath = os.path.join(library_dir, 'swedll64.dll')
        elif plat == 'Linux':
            library_relpath = os.path.join(library_dir, 'libswe.so')
        else:
            raise OSError('OS must be Windows or Linux')
        # library_relpath = os.path.relpath(os.path.abspath(library_relpath))
        return library_relpath

    def _load_library(self):
        plat = platform.system()
        library_relpath = self._get_library_relpath(settings.SWISSEPH_LIB_PATH)
        swe_lib = None
        try:
            if plat == 'Windows':
                swe_lib = windll.LoadLibrary(library_relpath)
                logger.info(msg='Loaded Swiss Ephemeris library for Windows.')
            elif plat == 'Linux':
                swe_lib = CDLL(library_relpath)
                logger.info(msg='Loaded Swiss Ephemeris library for Linux.')
            else:
                raise OSError('OS must be Windows or Linux')
        except OSError as e:
            logger.error(e)
        except WinError as e:
            logger.error(e)
        finally:
            if swe_lib is None:
                raise ImportError("Unable to load Swiss Ephemeris Library.")
            else:
                return swe_lib

    def _get_ephemeris_path(self):
        # path = os.path.abspath(settings.EPHEMERIS_PATH)
        path = settings.EPHEMERIS_PATH
        e_path = path.encode('utf-8')
        e_pointer = c_char_p(e_path)
        return e_pointer

    #                                           #
    #     Wrapped Swiss Ephemeris functions     #
    #                                           #
    def _wrap_set_ephemeris_path(self, swe_lib):
        set_ephemeris_path = swe_lib.swe_set_ephe_path
        set_ephemeris_path.argtypes = [c_char_p]
        set_ephemeris_path.restype = None
        set_ephemeris_path.__doc__ = ("""
        Sets the filepath of the ephemerides for the DLL functions.
        :param ephemeris_path: c_char_p
        :returns: None
        """)

        return set_ephemeris_path

    def _wrap_set_sidereal_mode(self, swe_lib):

        set_sidereal_mode = swe_lib.swe_set_sid_mode
        set_sidereal_mode.argtypes = [c_int32, c_double, c_double]
        set_sidereal_mode.restype = None
        set_sidereal_mode.__doc__ = ("""
        Sets the sidereal mode of the Swiss Ephemeris library to Fagan/Allen.
        :param sid_mode: c_int32 (should be 0)
        :param t0: c_double (should be 0)
        :param ayan_t0: c_double (should be 0)
        :returns: None
        """)

        return set_sidereal_mode

    def _wrap_local_time_to_UTC(self, swe_lib):
        local_time_to_UTC = swe_lib.swe_utc_time_zone
        local_time_to_UTC.argtypes = [c_int32, c_int32, c_int32, c_int32,
                                      c_int32, c_double, c_double,
                                      POINTER(c_int32), POINTER(c_int32),
                                      POINTER(c_int32), POINTER(c_int32),
                                      POINTER(c_int32), POINTER(c_double)]
        local_time_to_UTC.restype = None
        local_time_to_UTC.__doc__ = ("""Converts local time, with timezone, to UTC
        :param in-year: c_int32
        :param in-month: c_int32
        :param in-day: c_int32
        :param in-hour: c_int32
        :param in-min: c_int32
        :param in-sec: c_double
        :param in-timezone: c_double
        :param out_year: POINTER(c_int32)
        :param out-month: POINTER(c_int32)
        :param out-day: POINTER(c_int32)
        :param out-hour: POINTER(c_int32)
        :param out-min: POINTER(c_int32)
        :param out-sec: POINTER(c_double)
        :returns: None
        """)

        return local_time_to_UTC

    def _wrap_get_julian_day(self, swe_lib):
        get_julian_day = swe_lib.swe_julday
        get_julian_day.argtypes = [c_int, c_int, c_int, c_double, c_int]
        get_julian_day.restype = c_double
        get_julian_day.__doc__ = ("""
        Calculates julian day number (in UTC) from wall-clock time (in UTC)
        :param year: c_int
        :param month: c_int
        :param day: c_int
        :param fractional_hour: c_double
        :param calendar flag: c_int (should be 1)
        :returns: c_double
        """)

        return get_julian_day

    def _wrap_reverse_julian_day(self, swe_lib):
        reverse_julian_day = swe_lib.swe_revjul
        reverse_julian_day.argtypes = [c_double, c_int, POINTER(c_int), POINTER(c_int),
                                       POINTER(c_int), POINTER(c_double)]
        reverse_julian_day.restype = None
        reverse_julian_day.__doc__ = ("""
        Calculates year, month, day, fractional hour from Julian Day.
        :param julian_day: c_double
        :param calendar_flag: c_int (should be 1)
        :param year: POINTER(c_int)
        :param month: POINTER(c_int)
        :param day: POINTER(c_int)
        :param fractional_hour: POINTER(c_double)
        :returns: None 
        """)

        return reverse_julian_day

    def _wrap_get_sidereal_time_UT(self, swe_lib):
        get_sidereal_time_UTC = swe_lib.swe_sidtime
        get_sidereal_time_UTC.argtypes = [c_double]
        get_sidereal_time_UTC.restype = c_double
        get_sidereal_time_UTC.__doc__ = ("""
        Calculates sidereal time at the Greenwich Meridian.
        :param julian_day_in_UTC: c_double
        :rtype c_double
        :returns: c_double
        .. note:: Must be converted to local time for use in mundane calculations.
        """)

        return get_sidereal_time_UTC

    def _wrap_calculate_planets_UT(self, swe_lib):
        calculate_planets_UT = swe_lib.swe_calc_ut
        calculate_planets_UT.argtypes = [c_double, c_int, c_int32,
                                         POINTER(c_double), c_char_p]
        calculate_planets_UT.restype = None
        calculate_planets_UT.__doc__ = ("""
        Calculates planetary positions.
        :param julian_day_UTC: c_double
        :param body_number: c_int
        :param zodiacal_flag: c_int32
        :param return_array: POINTER(c_double) (Requires array of 6 doubles)
        :param error_string: c_char_p (String to write errors to)
        :returns: None 
        """)

        return calculate_planets_UT

    def _wrap_get_ayanamsa_UT(self, swe_lib):
        get_ayanamsa_UT = swe_lib.swe_get_ayanamsa_ex_ut
        get_ayanamsa_UT.argtypes = [c_double, c_int32,
                                    POINTER(c_double), c_char_p]
        get_ayanamsa_UT.restype = c_int32
        get_ayanamsa_UT.__doc__ = ("""
        Calculates ayanamsa.
        :param julian_day_UTC: c_double
        :param sidereal_flag: c_int32
        :param result_double: POINTER(c_double) (Pointer to a double to write to)
        :param error_string: c_char_p (String to write errors to)
        :returns: Ayanamsa (positive int or -1 for error)
        :rtype: c_int32 
        """)

        return get_ayanamsa_UT

    def _wrap_calculate_houses(self, swe_lib):
        calculate_houses = swe_lib.swe_houses_ex
        calculate_houses.argtypes = [c_double, c_int32, c_double, c_double,
                                     c_int, POINTER(c_double), POINTER(c_double)]
        calculate_houses.restype = None
        calculate_houses.__doc__ = ("""
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

        return calculate_houses

    def _wrap_close(self, swe_lib):
        close = swe_lib.swe_close
        close.argtypes = None
        close.restype = None
        close.__doc__ = ("""
        Closes the connection to the ephemeris.
        :param swe_lib: CDLL or WinDLL
        :returns: None
        """)

        return close
