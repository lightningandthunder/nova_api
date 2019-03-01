from BaseChartData import BaseChartData
import pendulum
from numpy import round


def test_nj_area():
    name = 'Mike'
    ldt = pendulum.datetime(2019, 2, 27, 20, 31, 0, tz='America/New_York')
    udt = pendulum.datetime(2019, 2, 28, 1, 31, 0)
    lat = 40.9958
    long = -74.0435

    ecliptic = {
        'Sun': 314.1574473222989,
        'Moon': 242.31248223042022,
        'Mercury': 332.1508530228922,
        'Venus': 273.06218323415544,
        'Mars': 14.171693744541951,
        'Jupiter': 236.75788601387848,
        'Saturn': 262.6542778677117,
        'Uranus': 4.727366440577683,
        'Neptune': 320.8933177569314,
        'Pluto': 267.41143149288126
    }

    mundane = {
        'Sun': 146.79742300562305,
        'Moon': 71.18931301348978,
        'Mercury': 165.26423810383073,
        'Venus': 103.7315401411139,
        'Mars': 205.09812899050644,
        'Jupiter': 65.96392174555527,
        'Saturn': 92.73263103766716,
        'Uranus': 195.80956452315695,
        'Neptune': 153.37642091894648,
        'Pluto': 97.80109986083579
    }

    RA = {
        'Sun': 340.75288686821625,
        'Moon': 267.1340741579414,
        'Mercury': 356.7020075425924,
        'Venus': 299.9761777212315,
        'Mars': 36.57476357194008,
        'Jupiter': 261.0789262548151,
        'Saturn': 289.0786951081564,
        'Uranus': 27.8386495448017,
        'Neptune': 347.398339836326,
        'Pluto': 294.2457769761652
    }

    chart = BaseChartData(name, ldt, udt, long, lat)

    e = chart.get_ecliptical_coords()
    assert e == ecliptic

    m = chart.get_mundane_coords()
    assert m == mundane

    r = chart.get_right_ascension_coords()
    assert r == RA

    assert round(chart.LST - 7.0863, 2) == 0
    assert round(chart.ramc - 106.296, 2) == 0

    cusps = {'1': 167.88191373470818, '2': 199.5851626176927, '3': 230.6383525226713, '4': 260.0082620127005,
             '5': 288.3863500663652, '6': 317.3157694471956, '7': 347.8819137347082, '8': 19.585162617692678,
             '9': 50.63835252267132, '10': 80.00826201270056, '11': 108.3863500663652, '12': 137.3157694471956}

    angles = {'Asc': 167.88191373470818, 'MC': 80.00826201270056, 'Dsc': 347.8819137347082, 'IC': 260.0082620127006,
              'Eq Asc': 172.66636153568209, 'Eq Dsc': 352.6663615356821, 'EP (Ecliptical)': (170.00826201270056,),
              'Zen': 77.88191373470818, 'WP (Ecliptical)': 350.0082620127006, 'Ndr': 257.8819137347082}

    for key, value in chart.cusps_longitude.items():
        assert value == cusps[key]

    for key, value in chart.angles_longitude.items():
        assert value == angles[key]


test_nj_area()
