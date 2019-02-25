import os
import settings


def get_ephe_path():
    return os.path.relpath(settings.EPHEMERIS_PATH, os.getcwd())
