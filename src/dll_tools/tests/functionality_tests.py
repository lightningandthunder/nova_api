import pendulum
import logging

from chartmanager import ChartManager
from swissephlib import SwissephLib
from tests import fixtures

swiss_lib = SwissephLib()
manager = ChartManager(swiss_lib)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M')


def run_tests():

    #  Plain charts

    # 2019/3/18 22:30:15 Hackensack - Positive latitude, negative longitude
    ldt = pendulum.datetime(2019, 3, 18, 22, 30, 15, tz='America/New_York')
    lat = 40.9792
    long = -74.1169
    chart = manager.create_chartdata(ldt, long, lat)
    fixtures.compare_charts(chart, fixtures.transits_2019_3_18_22_30_15_Hackensack, "2019-3-18 22:30:15 Hackensack")

    # 2019/3/10 3:30:15am Melbourne - Negative latitude, positive longitude
    ldt = pendulum.datetime(2019, 3, 18, 22, 30, 15, tz='Australia/Melbourne')
    lat = -37.8166
    long = 144.9666
    chart = manager.create_chartdata(ldt, long, lat)
    fixtures.compare_charts(chart, fixtures.transits_2019_3_10_1_30_15_Melbourne, "2019-3-18 22:30:15 Melbourne, AUS")

    # 2010/3/23 10:59:59am Murmansk - Latitude above arctic circle
    ldt = pendulum.datetime(2019, 3, 23, 10, 59, 59, tz='Europe/Moscow')
    lat = 68.9666
    long = 33.0833
    chart = manager.create_chartdata(ldt, long, lat)
    fixtures.compare_charts(chart, fixtures.transits_2019_3_23_1_30_15_murmansk, "2019-3-23 10:59:59 Murmansk, RUS")

    # Test return chart dates

    # 2019/3/18 22:30:15 Hackensack
    ldt = pendulum.datetime(2019, 3, 18, 22, 30, 15, tz='America/New_York')
    lat = 40.9792
    long = -74.1169
    chart = manager.create_chartdata(ldt, long, lat)
    return_date = pendulum.datetime(2019, 3, 24, 10, tz='America/New_York')
    chart_list = manager._generate_return_list(chart, long, lat, return_date, 1, 4, 20)  # Next 20 quarti-lunars

    fixtures.compare_return_times(chart_list, fixtures.quarti_lunar_dates_from_2019_3_18_22_30_15_Hackensack,
                                  '2019/3/18 22:30:15 Hackensack')

    # 2019/3/10 3:30:15am Melbourne
    ldt = pendulum.datetime(2019, 3, 18, 22, 30, 15, tz='Australia/Melbourne')
    lat = -37.8166
    long = 144.9666
    chart = manager.create_chartdata(ldt, long, lat)
    return_date = pendulum.datetime(2019, 9, 24, 10, tz='Australia/Melbourne')
    chart_list = manager._generate_return_list(chart, long, lat, return_date, 0, 36, 20)

    # Note that Solar Fire doesn't seem to pay attention to Australian AEDT for this; most of its times are an hour behind.
    # However, its calculations are based on UTC, so it appears as though the charts themselves are identical;
    # All that differs is the wall clock time it returns.
    fixtures.compare_return_times(chart_list, fixtures.quarti_ennead_dates_from_2019_3_18_22_30_15_Melbourne,
                                  '2019/3/18 22:30:15 Melbourne')


    # 1989/3/18 22:30:15 Hackensack - precessing into an SLR on the other side of the world
    ldt = pendulum.datetime(1989, 3, 18, 22, 30, 15, tz='America/New_York')
    lat = 40.9792
    long = -74.1169
    radix = manager.create_chartdata(ldt, long, lat)

    return_date = pendulum.datetime(2019, 3, 24, 10, tz='Australia/Melbourne')
    lunar_return = manager._generate_return_list(radix, 144.9666, -37.8166, return_date, 1, 1, 1)[0]
    manager.precess_into_sidereal_framework(radix=radix, transit_chart=lunar_return)

    fixtures.compare_charts(radix, fixtures.slr_2019_3_19_melbourne,
                            "1989-3-18 22:30:15 Hack NJ SLR 2019-3-19 Melbourne AUS")

    # Testing that precession is being accounted for in lists of solunar returns
    ldt = pendulum.datetime(1989, 3, 18, 22, 30, 15, tz='America/New_York')
    lat = 40.9792
    long = -74.1169
    radix = manager.create_chartdata(ldt, long, lat)
    return_date = pendulum.datetime(2019, 3, 24, 10, tz='Australia/Melbourne')
    pairs = manager.generate_radix_return_pairs(radix, 144.9666, -37.8166, return_date, 1, 4, 10)

    failed = False
    errors = list()
    for pair in pairs:
        if not pair[0].sidereal_framework.LST == pair[1].sidereal_framework.LST:
            failed = True
            errors.append(f"Radix LST: {pair[0].sidereal_framework.LST}; Return LST: {pair[1].sidereal_framework.LST}")
    if not failed:
        logger.info('Precessing radix into consecutive returns passed.')
    else:
        logger.warning(f'Failed: precessing radix into consecutive returns: {errors}')


    # These still need tests

    ldt = pendulum.datetime(1989, 12, 20, 22, 20, 0, tz='America/New_York')
    lat = 40.9792
    long = -74.1169
    radix = manager.create_chartdata(ldt, long, lat)
    local_dt = pendulum.datetime(2019, 3, 31, 15, tz='America/New_York')

    sp = manager.get_progressions(radix, local_dt, long, lat)

    ldt = pendulum.datetime(1989, 12, 20, 22, 30, tz='America/New_York')
    lat = 40.9792
    long = -74.1169
    natal = manager.create_chartdata(ldt, long, lat)

    ldt = pendulum.datetime(2019, 4, 2, 22, 32, tz='America/New_York')

    radix, local_natal, sp_radix, active_ssr, sp_ssr, transits = manager.get_transit_sensitive_charts(radix, ldt, long, lat)


if __name__ == '__main__':
    run_tests()
