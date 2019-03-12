from ctypes import c_int, c_int32

ENVIRONMENT = 'Development'

if ENVIRONMENT == 'Development':
    pass

elif ENVIRONMENT == 'Production':
    pass

SIDEREALMODE = c_int32(64 * 1024)
PLANETLIST = ["Sun", "Moon", "Mercury", "Venus", "Mars",
              "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]

ANGLES = ["Asc", "MC", "Dsc", "IC", "Eq Asc", "Eq Dsc", "EP (Ecliptical)",
          "Zen", "WP (Ecliptical)", "Ndr"]

CAMPANUS = c_int(67)
VERSION_NUMBER = "0.3a"
EPHEMERIS_PATH = 'swe/ephemeris'
SWISSEPH_LIB_PATH = 'swe/dll'

Q2 = 0.002737909

INT_TO_STRING_PLANET_MAP = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune',
                            'Pluto']

STRING_TO_INT_PLANET_MAP = {
    'Sun' : 0,
    'Moon' : 1,
    'Mercury' : 2,
    'Venus' : 3,
    'Mars' : 4,
    'Jupiter' : 5,
    'Saturn' : 6,
    'Uranus' : 7,
    'Neptune' : 8,
    'Pluto' : 9
}

ORBITAL_PERIODS_HOURS = [8760, 648]  # Sun, Moon