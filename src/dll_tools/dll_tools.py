import os
import settings


def get_ephe_path():
    return os.path.relpath(settings.EPHEMERIS_PATH, os.getcwd())

def get_planet_dict():
    return  {
    "Sun": '',
    "Moon": '',
    "Mercury": '',
    "Venus": '',
    "Mars": '',
    "Jupiter": '',
    "Saturn": '',
    "Uranus": '',
    "Neptune": '',
    "Pluto": '',
}