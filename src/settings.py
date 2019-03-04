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
VERSION_NUMBER = "0.2a"
EPHEMERIS_PATH = 'swe/ephemeris'
SWISSEPH_LIB_PATH = 'swe/dll'

Q2 = 0.002737909

SWISSEPH_BODY_NUMBER_MAP = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune',
                            'Pluto']
