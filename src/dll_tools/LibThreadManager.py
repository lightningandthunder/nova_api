import threading
from functools import wraps
from ctypes import *

from swissephlib import SwissephLib


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


class LibThreadManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.lib = SwissephLib()
        self._base_func_calc_planets = self._wrap_function(self.lib.swe_lib.swe_calc_ut, [c_double, c_int, c_int32,
                                                                                          POINTER(c_double), c_char_p], None, '')
        self._base_func_calc_ayanamsa = self._wrap_function(self.lib.swe_lib.swe_get_ayanamsa_ex_ut, [c_double, c_int32,
                                                                                                      POINTER(c_double), c_char_p], c_int32, '')

        self._base_func_calc_julday = self._wrap_function(self.lib.swe_lib.swe_julday, [c_int, c_int, c_int, c_double, c_int], restype=c_double, doc='')

    def calculate_planets(self, *args):
        return self._run_thread(self._base_func_calc_planets, args)

    def get_ayanamsa(self, *args):
        return self._run_thread(self._base_func_calc_ayanamsa, args)

    def get_julian_day(self, *args):
        return self._run_thread(self._base_func_calc_julday, args)

    def _wrap_function(self, base, argtypes, restype, doc):
        def _wrap_signature(base):
            func = base
            func.argtypes = argtypes
            func.restype = restype
            func.__doc__ = doc
            return func

        return _wrap_signature(base)

    def _run_thread(self, func, args):
        thread = ThreadWithReturn(target=self._call_thread_safe, args=(func, *args), kwargs={'seconds': 10})
        thread.start()
        results = thread.join()
        return results

    def _call_thread_safe(self, f, *args, **kwargs):
        with self.lock:
            res = f(*args)
        return res

l = LibThreadManager()
arr = (c_double * 6)()
s = create_string_buffer(126)

aya = c_double()
s2 = create_string_buffer(126)

for x in range(10000):
    l.calculate_planets(2458570.5 + x, 0, 64 * 1024, arr, s)
    r = l.get_ayanamsa(2458570.5 + x, 64 * 1024, aya, s2)
    julian = l.get_julian_day(2019, 3, 28, 0, 1)
    if x % 1000 == 0:
        print(julian)
        print(arr[0])
        print(aya)