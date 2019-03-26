import threading
from functools import wraps
from ctypes import *

from swissephlib import SwissephLib


class Thread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._return = None

        def run(self):
            if self._target:
                self._return = self._target(*self._args, **self._kwargs)

        def join(self, *args, **kwargs):
            super().join(*args, **kwargs)
            return self._return


class LibThreadManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.lib = SwissephLib()
        self.c = self.wrap_function(self.lib.calculate_planets_UT,[c_double, c_int, c_int32,
                                              POINTER(c_double), c_char_p], None, '')



    def wrap_function(self, base, argtypes, restype, doc):
        def _wrap_signature(base):
            func = base
            func.argtypes = argtypes
            func.restype = restype
            func.__doc__ = doc
            return func

        return _wrap_signature(base)

    def _call(self, f, *args, **kwargs):
        with self.lock:
            res = f(*args)
        return res


    def start(self, *args):
        thread = Thread(target=self._call, args=(self.c, *args), kwargs={'seconds': 5})
        thread.start()
        results = thread.join()
        return results


l = LibThreadManager()
arr = (c_double * 6)()
s = create_string_buffer(126)

r = l.start(2458568, 0, 64 * 1024, arr, s)
if s.value: print(s.value)