from numpy import round
import pendulum

"""Test dictionaries based on Solar Fire output."""


def compare_return_times(chart_list, expected_date_list, name):
    print(f'Testing return times for {name}...')

    failed = False
    for index, c in enumerate(chart_list):
        if c.local_datetime != expected_date_list[index]:
            print(f'Harmonic return test failed; {c.local_datetime} != expected date: {expected_date_list[index]}')
            failed = True

    if not failed: print('Return dates passed.')


def compare_charts(chart, fixture, name):
    print(f'Testing chart {name}...')

    failed = False
    ecliptic = chart.get_ecliptical_coords()
    for body in ecliptic:
        if not round(ecliptic[body], decimals=2) == round(fixture['Ecliptic'][body], decimals=2):
            print(f"Test failed on {body} ecliptical coords: {ecliptic[body]} != {fixture['Ecliptic'][body]}")
            failed = True

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
        print('LST passed.')

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
    'SVP': 4.991,
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
        'Saturn': 290.637,
        'Uranus': 28.668,
        'Neptune': 348.067,
        'Pluto': 294.686,
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
    'LST': 8.884,
    'SVP': 4.991,
    'Obliquity': 23.436,
    'Ecliptic': {
        'Sun': 332.5745,
        'Moon': 116.1571,
        'Mercury': 325.9758,
        'Venus': 294.9854,
        'Mars': 26.5067,
        'Jupiter': 238.5130,
        'Saturn': 264.0730,
        'Uranus': 5.5716,
        'Neptune': 321.5900,
        'Pluto': 267.8094
    },
    'Mundane': {
        'Sun': 141.727,
        'Moon': 287.887,
        'Mercury': 134.319,
        'Venus': 104.577,
        'Mars': 172.371,
        'Jupiter': 17.920,
        'Saturn': 51.533,
        'Uranus': 161.643,
        'Neptune': 134.392,
        'Pluto': 57.690,
    },
    'Right Ascension': {
        'Sun': 357.778,
        'Moon': 144.301,
        'Mercury': 350.535,
        'Venus': 322.478,
        'Mars': 48.866,
        'Jupiter': 262.977,
        'Saturn': 290.590,
        'Uranus': 28.638,
        'Neptune': 348.046,
        'Pluto': 294.670,
    },
    'Cusps': {
        "1": 217.330,
        "2": 249.704,
        "3": 269.071,
        "4": 285.814,
        "5": 307.338,
        "6": 345.598,
        "7": 37.330,
        "8": 69.704,
        "9": 89.071,
        "10": 105.814,
        "11": 127.338,
        "12": 165.598
    },
    'Angles': {
        "Asc": 217.330,
        "MC": 105.814,
        "Dsc": 37.330,
        "IC": 285.814,
        "Eq Asc": 200.732,
        "Eq Dsc": 20.732,
        "EP (Ecliptical)": 195.810,
        "Zen": 127.324,
        "WP (Ecliptical)": 15.810,
        "Ndr": 307.324
    }
}

transits_2019_3_23_1_30_15_murmansk = {
    'LST': 22.240,
    'SVP': 4.991,
    'Obliquity': 23.436,
    'Ecliptic': {
        'Sun': 337.3951,
        'Moon': 188.4192,
        'Mercury': 322.4498,
        'Venus': 300.8043,
        'Mars': 29.7377,
        'Jupiter': 238.8208,
        'Saturn': 264.3748,
        'Uranus': 5.8193,
        'Neptune': 321.7700,
        'Pluto': 267.8902
    },
    'Mundane': {
        'Sun': 325.360,
        'Moon': 159.949,
        'Mercury': 309.504,
        'Venus': 235.326,
        'Mars': 337.453,
        'Jupiter': 164.068,
        'Saturn': 171.096,
        'Uranus': 334.560,
        'Neptune': 315.542,
        'Pluto': 171.626,
    },
    'Right Ascension': {
        'Sun': 2.206,
        'Moon': 212.906,
        'Mercury': 347.718,
        'Venus': 328.235,
        'Mars': 52.169,
        'Jupiter': 263.306,
        'Saturn': 290.916,
        'Uranus': 28.878,
        'Neptune': 348.209,
        'Pluto': 294.757,
    },
    'Cusps': {
        "1": 99.960,  # This matches Solar Fire. The rest do not. SF's output below:
        "2": 115.411,  # 129.963
        "3": 121.480,  # 159. etc
        "4": 126.582,  # 189
        "5": 134.476,  # 219
        "6": 169.542,  # 249
        "7": 279.960,  # 279
        "8": 295.411,  # 309
        "9": 301.480,  # 9
        "10": 306.582,  # 39
        "11": 314.476,  # 69
        "12": 349.542  # 99
    },
    'Angles': {
        "Asc": 99.960,
        "MC": 306.582,
        "Dsc": 279.960,
        "IC": 126.582,
        "Eq Asc": 40.509,
        "Eq Dsc": 220.509,
        "EP (Ecliptical)": 36.582,
        "Zen": 9.960,
        "WP (Ecliptical)": 216.582,
        "Ndr": 189.960
    }
}

slr_2019_3_19_melbourne = {
    'LST': 12.426,
    'SVP': 4.991,
    'Obliquity': 23.436,
    'Ecliptic': {
        'Sun': 333.9193,
        'Moon': 118.3506,
        'Mercury': 319.1094,
        'Venus': 329.6520,
        'Mars': 40.1497,
        'Jupiter': 36.6407,
        'Saturn': 258.3559,
        'Uranus': 250.5477,
        'Neptune': 257.6079,
        'Pluto': 200.3281
    },
    'Mundane': {
        'Sun': 80.626,
        'Moon': 214.236,
        'Mercury': 62.135,
        'Venus': 75.859,
        'Mars': 140.466,
        'Jupiter': 139.082,
        'Saturn': 352.044,
        'Uranus': 344.779,
        'Neptune': 351.534,
        'Pluto': 317.405,
    },
    'Right Ascension': {
        'Sun': 359.016,
        'Moon': 146.055,
        'Mercury': 346.240,
        'Venus': 355.666,
        'Mars': 62.968,
        'Jupiter': 59.666,
        'Saturn': 284.440,
        'Uranus': 276.058,
        'Neptune': 283.617,
        'Pluto': 227.530,
    },
    'Cusps': {'1': 60.46534287447976, '2': 101.02797414566278, '3': 142.37746406430412, '4': 170.81882375428106,
              '5': 191.94365638621713, '6': 212.83312536164476, '7': 240.46534287447977, '8': 281.02797414566277,
              '9': 322.3774640643041, '10': 350.8188237542811, '11': 11.943656386217109, '12': 32.83312536164474},
    'Angles': {
        'Asc': 60.46534287447976, 'MC': 350.8188237542811, 'Dsc': 240.46534287447975, 'IC': 170.81882375428108,
        'Eq Asc': 78.47068148253182, 'Eq Dsc': 258.4706814825318, 'EP (Ecliptical)': (80.81882375428108,),
        'Zen': 330.46534287447975, 'WP (Ecliptical)': 260.8188237542811, 'Ndr': 150.46534287447975
    }
}

quarti_lunar_dates_from_2019_3_18_22_30_15_Hackensack = [
    pendulum.parse('2019-03-25T03:01:07-04:00'),
    pendulum.parse('2019-04-01T11:50:14-04:00'),
    pendulum.parse('2019-04-08T18:11:26-04:00'),
    pendulum.parse('2019-04-15T07:04:27-04:00'),
    pendulum.parse('2019-04-21T12:53:17-04:00'),
    pendulum.parse('2019-04-28T19:13:39-04:00'),
    pendulum.parse('2019-05-06T00:35:28-04:00'),
    pendulum.parse('2019-05-12T13:13:43-04:00'),
    pendulum.parse('2019-05-18T22:15:22-04:00'),
    pendulum.parse('2019-05-26T03:09:47-04:00'),
    pendulum.parse('2019-06-02T08:42:47-04:00'),
    pendulum.parse('2019-06-08T18:36:47-04:00'),
    pendulum.parse('2019-06-15T05:58:26-04:00'),
    pendulum.parse('2019-06-22T11:03:43-04:00'),
    pendulum.parse('2019-06-29T18:04:11-04:00'),
    pendulum.parse('2019-07-06T01:15:46-04:00'),
    pendulum.parse('2019-07-12T12:01:25-04:00'),
    pendulum.parse('2019-07-19T18:21:24-04:00'),
    pendulum.parse('2019-07-27T03:25:30-04:00'),
    pendulum.parse('2019-08-02T10:09:37-04:00')
]
quarti_ennead_dates_from_2019_3_18_22_30_15_Melbourne = [
    pendulum.parse("2019-09-21T06:34:06+10:00"),
    pendulum.parse("2019-10-01T11:25:58+10:00"),
    pendulum.parse("2019-10-11T15:56:29+11:00"),
    pendulum.parse("2019-10-21T18:06:19+11:00"),
    pendulum.parse("2019-10-31T18:46:25+11:00"),
    pendulum.parse("2019-11-10T18:15:12+11:00"),
    pendulum.parse("2019-11-20T16:38:38+11:00"),
    pendulum.parse("2019-11-30T13:55:09+11:00"),
    pendulum.parse("2019-12-10T10:28:46+11:00"),
    pendulum.parse("2019-12-20T06:30:00+11:00"),
    pendulum.parse("2019-12-30T02:01:28+11:00"),
    pendulum.parse("2020-01-08T21:29:25+11:00"),
    pendulum.parse("2020-01-18T17:06:45+11:00"),
    pendulum.parse("2020-01-28T12:56:27+11:00"),
    pendulum.parse("2020-02-07T09:23:52+11:00"),
    pendulum.parse("2020-02-17T06:41:04+11:00"),
    pendulum.parse("2020-02-27T04:47:53+11:00"),
    pendulum.parse("2020-03-08T04:06:16+11:00"),
    pendulum.parse("2020-03-18T04:43:11+11:00"),
    pendulum.parse("2020-03-28T06:33:06+11:00")
]
