import os
import platform
import ctypes as c

import astrosetup


def load_library():
    plat = platform.system()
    file_dir = os.path.dirname(os.path.abspath(__file__))
    lib = None
    try:
        if plat == 'Windows':
            lib = c.windll.LoadLibrary(file_dir + 'swe/swedll64.dll')  # TODO: put DLL + necessary files in there
        elif plat == 'Linux':
            lib = c.CDLL(file_dir + 'swe/libswe.so')
        else:
            raise OSError('OS must be Windows or Linux')
    except OSError as e:
        print(e)

    return lib
