from numpy import round

"""Test dictionaries based on Solar Fire output, rounded to 1/10000 of a degree, or 0.36 seconds of arc.
Intended accuracy for Astronova is approximately 1/1000 of a degree, or 3.6 seconds."""


def compare_charts(chart, fixture):
    ecliptic = chart.get_ecliptical_coords()
    for body in ecliptic:
        assert round(ecliptic[body], decimals=2) == round(fixture['Ecliptical'][body], decimals=2)

    mundane = chart.get_mundane_coords()
    for body in mundane:
        assert round(mundane[body], decimals=2) == round(fixture['Mundane'][body], decimals=2)

    ra = chart.get_right_ascension_coords()
    for body in ra:
        assert round(ra[body], decimals=2) == round(fixture['Right Ascension'][body], decimals=2)

    cusps = chart.get_cusps_longitude()
    for cusp in cusps:
        assert round(cusps[cusp], decimals=2) == round(fixture['Cusps'][cusp], decimals=2)

    angles = chart.get_angles_longitude()
    for angle in angles:
        assert round(angles[angle], decimals=2) == round(fixture['Angles'][angle], decimals=2)

    assert round(chart.sidereal_framework.LST, decimals=2) == round(fixture['LST'], decimals=2)
    assert round(chart.sidereal_framework.svp, decimals=2) == round(fixture['SVP'], decimals=2)
    assert round(chart.sidereal_framework.obliquity, decimals=2) == round(fixture['Obliquity'], decimals=2)

    return True


# ==================================================================================================================== #
# =================================================   Fixtures   ===================================================== #
# ==================================================================================================================== #


transits_2019_3_18_22_30_15 = {
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
        'Uranus': 4.6030,
        'Neptune': 321.6134,
        'Pluto': 267.8205
    },
    'Mundane': {
        'Sun': 0,
        'Moon': 0,
        'Mercury': 0,
        'Venus': 0,
        'Mars': 20,
        'Jupiter': 0,
        'Saturn': 0,
        'Uranus': 0,
        'Neptune': 0,
        'Pluto': 0,
    },
    'Right Ascension': {
        'Sun': 0,
        'Moon': 0,
        'Mercury': 0,
        'Venus': 0,
        'Mars': 20,
        'Jupiter': 0,
        'Saturn': 0,
        'Uranus': 0,
        'Neptune': 0,
        'Pluto': 0,
    },
    'Cusps': {
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0,
        "6": 0,
        "7": 0,
        "8": 0,
        "9": 0,
        "10": 0,
        "11": 0,
        "12": 0
    },
    'Angles': {
        "Asc": 0,
        "MC": 0,
        "Dsc": 0,
        "IC": 0,
        "Eq Asc": 0,
        "Eq Dsc": 0,
        "EP (Ecliptical)": 0,
        "Zen": 0,
        "WP (Ecliptical)": 0,
        "Ndr": 0
    }
}
