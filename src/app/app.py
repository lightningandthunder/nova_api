from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import logging
import pendulum
from chartmanager import ChartManager
from src.dll_tools.tests.functionality_tests import run_tests
import settings
import json

from pendulum.tz.zoneinfo.exceptions import InvalidTimezone

app = Flask(__name__)
CORS(app)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M')

manager = ChartManager()


@app.route('/radix', methods=['POST'])
@cross_origin()
def radix():
    try:
        radix_chart = get_radix_from_json(request.json)
        return json.dumps(radix_chart.jsonify_chart())
    except Exception as ex:
        return str(ex)


@app.route('/returns', methods=['POST'])
@cross_origin()
def returns():
    # TODO: Add validation
    radix_data = request.json.get('radix')
    return_params = request.json.get('return_params')
    print(radix_data)
    print(return_params)

    return_planet = return_params.get("return_planet")
    return_harmonic = int(return_params.get("return_harmonic"))
    return_longitude = float(return_params.get("return_longitude"))
    return_latitude = float(return_params.get("return_latitude"))
    return_start_date_raw = return_params.get("return_start_date")
    return_quantity = int(return_params.get("return_quantity"))

    return_start_date = pendulum.parse(return_start_date_raw)
    tz = return_params.get('tz')
    return_start_date = return_start_date.in_timezone(tz)

    print(return_start_date)

    return_body = settings.STRING_TO_INT_PLANET_MAP[return_planet]

    radix = get_radix_from_json(radix_data)
    return_pairs = manager.generate_radix_return_pairs(radix=radix,
                                                       geo_longitude=return_longitude,
                                                       geo_latitude=return_latitude,
                                                       date=return_start_date,
                                                       body=return_body,
                                                       harmonic=return_harmonic,
                                                       return_quantity=return_quantity)

    return_json = list()

    for pair in return_pairs:
        return_json.append({"radix": pair[0].jsonify_chart(), "return_chart": pair[1].jsonify_chart()})

    return json.dumps(return_json)


def get_radix_from_json(json):
    local_datetime = json.get('local_datetime')
    tz = json.get('tz')

    if not local_datetime:
        raise RuntimeError('No datetime provided')

    pendulum_dt = pendulum.parse(local_datetime)

    if tz:
        try:
            pendulum_dt = pendulum_dt.in_timezone(tz)
            print(pendulum_dt)
        except InvalidTimezone as ex:
            logger.error(f"Bad timezone: {str(ex)}")
            raise ex

    longitude = json.get('longitude')
    latitude = json.get('latitude')

    radix_chart = manager.create_chartdata(local_datetime=pendulum_dt,
                                           geo_longitude=float(longitude),
                                           geo_latitude=float(latitude))

    return radix_chart


if __name__ == '__main__':
    while True:
        try:
            run_tests(manager)
            app.run(debug=True, port=5000)
        except KeyboardInterrupt:
            exit(1)
        except Exception as e:
            logger.exception(msg=f'Error: {str(e)}')
