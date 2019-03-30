import ctypes
from ctypes import c_char_p, c_int, c_int32, c_double, POINTER, CDLL
import os
import platform
import struct
import pathlib
import threading

import settings
from logging import getLogger

logger = getLogger(__name__)

"""
Wraps Swiss Ephemeris library functions. Only one instance should exist at a time.
"""


class SwissephLibV2:
    class ThreadWithReturn(threading.Thread):
        def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
            threading.Thread.__init__(self, group, target, name, args, kwargs, daemon=daemon)
            self._return = None

        def run(self):
            if self._target is not None:
                self._return = self._target(*self._args, **self._kwargs)

        def join(self, **kwargs):
            threading.Thread.join(self, **kwargs)
            return self._return

    def __init__(self):
        self.lock = threading.Lock()
        self.swe_lib = self._load_library()

        self._base_func_calc_planets = self._wrap_function(self.swe_lib.swe_calc_ut, [c_double, c_int, c_int32,
                                                                                      POINTER(c_double), c_char_p],
                                                           None, """
        Calculates planetary positions.
        :param julian_day_UTC: c_double
        :param body_number: c_int
        :param zodiacal_flag: c_int32
        :param return_array: POINTER(c_double) (Requires array of 6 doubles)
        :param error_string: c_char_p (String to write errors to)
        :returns: None 
        """)
        self._base_func_calc_ayanamsa = self._wrap_function(self.swe_lib.swe_get_ayanamsa_ex_ut, [c_double, c_int32,
                                                                                                  POINTER(c_double),
                                                                                                  c_char_p], c_int32,
        """
        Calculates ayanamsa.
        :param julian_day_UTC: c_double
        :param sidereal_flag: c_int32
        :param result_double: POINTER(c_double) (Pointer to a double to write to)
        :param error_string: c_char_p (String to write errors to)
        :returns: Ayanamsa (positive int or -1 for error)
        :rtype: c_int32 
        """)

        self._base_func_calc_julday = self._wrap_function(self.swe_lib.swe_julday,
                                                          [c_int, c_int, c_int, c_double, c_int], restype=c_double,
                                                          doc="""
        Calculates julian day number (in UTC) from wall-clock time (in UTC)
        :param year: c_int
        :param month: c_int
        :param day: c_int
        :param fractional_hour: c_double
        :param calendar flag: c_int (should be 1)
        :returns: c_double
        """)

        self._base_func_set_ephemeris_path = self._wrap_function(self.swe_lib.swe_set_ephe_path, [c_char_p], None, """
        Sets the filepath of the ephemerides for the DLL functions.
        :param ephemeris_path: c_char_p
        :returns: None
        """)
        self._base_func_set_sidereal_mode = self._wrap_function(self.swe_lib.swe_set_sid_mode,
                                                                [c_int32, c_double, c_double], None, """
        Sets the sidereal mode of the Swiss Ephemeris library to Fagan/Allen.
        :param sid_mode: c_int32 (should be 0)
        :param t0: c_double (should be 0)
        :param ayan_t0: c_double (should be 0)
        :returns: None
        """)
        self._base_func_reverse_julian_day = self._wrap_function(self.swe_lib.swe_revjul,
                                                                 [c_double, c_int, POINTER(c_int), POINTER(c_int),
                                                                  POINTER(c_int), POINTER(c_double)], None, """
        Calculates year, month, day, fractional hour from Julian Day.
        :param julian_day: c_double
        :param calendar_flag: c_int (should be 1)
        :param year: POINTER(c_int)
        :param month: POINTER(c_int)
        :param day: POINTER(c_int)
        :param fractional_hour: POINTER(c_double)
        :returns: None 
        """)
        self._base_func_get_sidereal_time_utc = self._wrap_function(self.swe_lib.swe_sidtime, [c_double], c_double, """
        Calculates sidereal time at the Greenwich Meridian.
        :param julian_day_in_UTC: c_double
        :rtype c_double
        :returns: c_double
        .. note:: Must be converted to local time for use in mundane calculations.
        """)
        self._base_func_calculate_houses = self._wrap_function(self.swe_lib.swe_houses_ex,
                                                               [c_double, c_int32, c_double, c_double,
                                                                c_int, POINTER(c_double), POINTER(c_double)], None, """
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
        self._base_func_close = self._wrap_function(self.swe_lib.swe_close, None, None, """
        Closes the connection to the ephemeris.
        :param swe_lib: CDLL or WinDLL
        :returns: None
        """)

        self.ephemeris_path = self._get_ephemeris_path()
        self.set_ephemeris_path(self.ephemeris_path)
        self.set_sidereal_mode(0, 0, 0)


    # === Public functions

    def calculate_planets_UT(self, *args):
        return self._run_thread(self._base_func_calc_planets, args)

    def get_ayanamsa_UT(self, *args):
        return self._run_thread(self._base_func_calc_ayanamsa, args)

    def get_julian_day(self, *args):
        return self._run_thread(self._base_func_calc_julday, args)

    def set_ephemeris_path(self, *args):
        return self._run_thread(self._base_func_set_ephemeris_path, args)

    def set_sidereal_mode(self, *args):
        return self._run_thread(self._base_func_set_sidereal_mode, args)

    def reverse_julian_day(self, *args):
        return self._run_thread(self._base_func_reverse_julian_day, args)

    def get_sidereal_time_utc(self, *args):
        return self._run_thread(self._base_func_get_sidereal_time_utc, args)

    def calculate_houses(self, *args):
        return self._run_thread(self._base_func_calculate_houses, args)

    def close(self, *args):
        return self._run_thread(self._base_func_close, args)

    # === Internal functions

    def _wrap_function(self, base, argtypes, restype, doc):
        def _wrap_signature(base):
            func = base
            func.argtypes = argtypes
            func.restype = restype
            func.__doc__ = doc
            return func

        return _wrap_signature(base)

    def _run_thread(self, func, args):
        thread = self.ThreadWithReturn(target=self._call_thread_safe, args=(func, *args), kwargs={'seconds': 2})
        thread.start()
        results = thread.join()
        return results

    def _call_thread_safe(self, f, *args, **kwargs):
        with self.lock:
            res = f(*args)
        return res

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


# ======================================

#
# class LibThreadManager:
#     def __init__(self):
#         self.lock = threading.Lock()
#         self.lib = SwissephLib()
#         self._base_func_calc_planets = self._wrap_function(self.lib.swe_lib.swe_calc_ut, [c_double, c_int, c_int32,
#                                                                                           POINTER(c_double), c_char_p],
#                                                            None, '')
#         self._base_func_calc_ayanamsa = self._wrap_function(self.lib.swe_lib.swe_get_ayanamsa_ex_ut, [c_double, c_int32,
#                                                                                                       POINTER(c_double),
#                                                                                                       c_char_p],
#                                                             c_int32, '')
#
#         self._base_func_calc_julday = self._wrap_function(self.lib.swe_lib.swe_julday,
#                                                           [c_int, c_int, c_int, c_double, c_int], restype=c_double,
#                                                           doc='')
#
#     def calculate_planets(self, *args):
#         return self._run_thread(self._base_func_calc_planets, args)
#
#     def get_ayanamsa(self, *args):
#         return self._run_thread(self._base_func_calc_ayanamsa, args)
#
#     def get_julian_day(self, *args):
#         return self._run_thread(self._base_func_calc_julday, args)
#
#     def _wrap_function(self, base, argtypes, restype, doc):
#         def _wrap_signature(base):
#             func = base
#             func.argtypes = argtypes
#             func.restype = restype
#             func.__doc__ = doc
#             return func
#
#         return _wrap_signature(base)
#
#     def _run_thread(self, func, args):
#         thread = ThreadWithReturn(target=self._call_thread_safe, args=(func, *args), kwargs={'seconds': 10})
#         thread.start()
#         results = thread.join()
#         return results
#
#     def _call_thread_safe(self, f, *args, **kwargs):
#         with self.lock:
#             res = f(*args)
#         return res
#
#
# l = LibThreadManager()
# arr = (c_double * 6)()
# s = create_string_buffer(126)
#
# aya = c_double()
# s2 = create_string_buffer(126)
#
# for x in range(10000):
#     l.calculate_planets(2458570.5 + x, 0, 64 * 1024, arr, s)
#     r = l.get_ayanamsa(2458570.5 + x, 64 * 1024, aya, s2)
#     julian = l.get_julian_day(2019, 3, 28, 0, 1)
#     if x % 1000 == 0:
#         print(julian)
#         print(arr[0])
#         print(aya)
