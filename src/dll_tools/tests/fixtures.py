from numpy import round

"""Test dictionaries based on Solar Fire output."""


def compare_charts(chart, fixture, name):
    print(f'Testing chart {name}...')

    failed = False
    ecliptic = chart.get_ecliptical_coords()
    for body in ecliptic:
        if not round(ecliptic[body], decimals=2) == round(fixture['Ecliptic'][body], decimals=2):
            print(f"Test failed on {body} ecliptical coords: {ecliptic[body]} != {fixture['Ecliptic'][body]}")

    if not failed: print('Ecliptical coordinates passed.')

    failed = False
    mundane = chart.get_mundane_coords()
    for body in mundane:
        if not round(mundane[body], decimals=0) == round(fixture['Mundane'][body], decimals=0):
            print(f"Test failed on {body} mundane coords: {mundane[body]} != {fixture['Mundane'][body]}")
            failed = True

    if not failed: print('Mundane coordinates passed.')

    failed = False
    ra = chart.get_right_ascension_coords()
    for body in ra:
        if not round(ra[body], decimals=2) == round(fixture['Right Ascension'][body], decimals=2):
            print(f"Test failed on {body} RA coords: {ra[body]} != {fixture['Right Ascension'][body]}")
            failed = True

    if not failed: print('RA coordinates passed. ')

    failed = False
    cusps = chart.get_cusps_longitude()
    for cusp in cusps:
        if not round(cusps[cusp], decimals=0) == round(fixture['Cusps'][cusp], decimals=0):
            print(f"Test failed on cusp {cusp}: {cusps[cusp]} != {fixture['Cusps'][cusp]}")
            failed = True

    if not failed: print('Cusps coordinates passed.')

    failed = False
    angles = chart.get_angles_longitude()
    for angle in angles:
        if not round(angles[angle], decimals=0) == round(fixture['Angles'][angle], decimals=0):
            print(f"Test failed on angle {angle}: {angles[angle]} != {fixture['Angles'][angle]}")
            failed = True

    if not failed: print('Angle coordinates passed.')

    if not round(chart.sidereal_framework.LST, decimals=2) == round(fixture['LST'], decimals=2):
        print(f"Test failed on LST: {chart.sidereal_framework.LST} != {fixture['LST']}")
    else:
        print ('LST passed.')

    if not round(chart.sidereal_framework.svp, decimals=2) == round(fixture['SVP'], decimals=2):
        print(f"Test failed on SVP: {chart.sidereal_framework.svp} != {fixture['SVP']}")
    else:
        print('SVP passed.')

    if not round(chart.sidereal_framework.obliquity, decimals=2) == round(fixture['Obliquity'], decimals=2):
        print(f"Test failed on obliquity: {chart.sidereal_framework.obliquity} != {fixture['Obliquity']}")
    else:
        print('Obliquity passed.')


# ==================================================================================================================== #
# =================================================   Fixtures   ===================================================== #
# ==================================================================================================================== #


transits_2019_3_18_22_30_15_Hackensack = {
    'LST': 9.325,
    'SVP': 4.995,
    'Obliquity': 23.436,
    'Ecliptic': {
        'Sun': 333.1960,
        'Moon': 125.5073,
        'Mercury': 325.4267,
        'Venus': 295.7339,
        'Mars': 26.9233,
        'Jupiter': 238.5565,
        'Saturn': 264.1137,
        'Uranus': 5.6030,
        'Neptune': 321.6134,
        'Pluto': 267.8205
    },
    'Mundane': {
        'Sun': 136.032,
        'Moon': 284.850,
        'Mercury': 127.041,
        'Venus': 93.594,
        'Mars': 192.304,
        'Jupiter': 39.346,
        'Saturn': 62.019,
        'Uranus': 171.238,
        'Neptune': 122.649,
        'Pluto': 65.746,
    },
    'Right Ascension': {
        'Sun': 358.349,
        'Moon': 153.658,
        'Mercury': 350.075,
        'Venus': 323.221,
        'Mars': 49.286,
        'Jupiter': 263.020,
        'Saturn': 290.633,
        'Uranus': 28.668,
        'Neptune': 348.063,
        'Pluto': 294.681,
    },
    'Cusps': {
        "1": 194.254,
        "2": 227.347,
        "3": 261.680,
        "4": 292.426,
        "5": 319.359,
        "6": 345.489,
        "7": 14.253,
        "8": 47.347,
        "9": 81.680,
        "10": 112.426,
        "11": 139.359,
        "12": 165.489
    },
    'Angles': {
        "Asc": 194.254,
        "MC": 112.426,
        "Dsc": 14.254,
        "IC": 292.426,
        "Eq Asc": 207.283,
        "Eq Dsc": 27.283,
        "EP (Ecliptical)": 202.349,
        "Zen": 104.160,
        "WP (Ecliptical)": 22.349,
        "Ndr": 284.160
    }
}

transits_2019_3_10_1_30_15_Melbourne = {
    'LST': 9.325,
    'SVP': 4.995,
    'Obliquity': 23.436,
    'Ecliptic': {
        'Sun': 333.1960,
        'Moon': 125.5073,
        'Mercury': 325.4267,
        'Venus': 295.7339,
        'Mars': 26.9233,
        'Jupiter': 238.5565,
        'Saturn': 264.1137,
        'Uranus': 5.6030,
        'Neptune': 321.6134,
        'Pluto': 267.8205
    },
    'Mundane': {
        'Sun': 136.032,
        'Moon': 284.850,
        'Mercury': 127.041,
        'Venus': 93.594,
        'Mars': 192.304,
        'Jupiter': 39.346,
        'Saturn': 62.019,
        'Uranus': 171.238,
        'Neptune': 122.649,
        'Pluto': 65.746,
    },
    'Right Ascension': {
        'Sun': 358.349,
        'Moon': 153.658,
        'Mercury': 350.075,
        'Venus': 323.221,
        'Mars': 49.286,
        'Jupiter': 263.020,
        'Saturn': 290.633,
        'Uranus': 28.668,
        'Neptune': 348.063,
        'Pluto': 294.681,
    },
    'Cusps': {
        "1": 194.254,
        "2": 227.347,
        "3": 261.680,
        "4": 292.426,
        "5": 319.359,
        "6": 345.489,
        "7": 14.253,
        "8": 47.347,
        "9": 81.680,
        "10": 112.426,
        "11": 139.359,
        "12": 165.489
    },
    'Angles': {
        "Asc": 194.254,
        "MC": 112.426,
        "Dsc": 14.254,
        "IC": 292.426,
        "Eq Asc": 207.283,
        "Eq Dsc": 27.283,
        "EP (Ecliptical)": 202.349,
        "Zen": 104.160,
        "WP (Ecliptical)": 22.349,
        "Ndr": 284.160
    }
}