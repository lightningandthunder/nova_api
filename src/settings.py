from ctypes import c_int, c_int32
import os

VERSION_NUMBER = "0.3a"

ENVIRONMENT = os.environ.get('ENVIRONMENT', None)

if ENVIRONMENT == 'Production':
    pass
else:  # Development
    pass

# DLL parameters
SIDEREALMODE = c_int32(64 * 1024)
CAMPANUS = c_int(67)
EPHEMERIS_PATH = 'swe/ephemeris/'
SWISSEPH_LIB_PATH = 'astronova_api/src/dll_tools/swe/dll'

# Progressions
Q2 = 0.002737909  # MikeStar lists this as 0.0027378030919862
TERTIARY_RATE = 0.0366009950851544

# Planets
INT_TO_STRING_PLANET_MAP = [
    'Sun',
    'Moon',
    'Mercury',
    'Venus',
    'Mars',
    'Jupiter',
    'Saturn',
    'Uranus',
    'Neptune',
    'Pluto'
]

STRING_TO_INT_PLANET_MAP = {
    'Sun': 0,
    'Moon': 1,
    'Mercury': 2,
    'Venus': 3,
    'Mars': 4,
    'Jupiter': 5,
    'Saturn': 6,
    'Uranus': 7,
    'Neptune': 8,
    'Pluto': 9
}

ORBITAL_PERIODS_HOURS = [8784, 672]  # Sun, Moon

PLANETLIST = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto"
]

ANGLES = [
    "Asc",
    "MC",
    "Dsc",
    "IC",
    "Eq Asc",
    "Eq Dsc",
    "EP (Ecliptical)",
    "Zen",
    "WP (Ecliptical)",
    "Ndr"
]
