from flask import Flask, request
from flask_cors import CORS, cross_origin
import logging
import pendulum
import json
from pendulum.tz.zoneinfo.exceptions import InvalidTimezone

from src.dll_tools.chartmanager import ChartManager
from src.dll_tools.tests.functionality_tests import run_tests
from src import settings

app = Flask(__name__)
CORS(app)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M')

manager = ChartManager()


# ========================= Routes ======================== #


@app.route('/radix', methods=['POST'])
@cross_origin()
def radix():
    try:
        radix_chart = get_radix_from_json(request.json)
        return json.dumps(radix_chart.jsonify_chart())
    except Exception as ex:
        return json.dumps({"err": str(ex)})


@app.route('/returns', methods=['POST'])
@cross_origin()
def returns():
    try:
        radix_chart = get_radix_from_json(request.json.get('radix'))
        return_params = get_return_params_from_json(request.json.get('return_params'))

        return_pairs = manager.generate_radix_return_pairs(radix=radix_chart, **return_params)

        result_json = list()
        for pair in return_pairs:
            result_json.append({"radix": pair[0].jsonify_chart(), "return_chart": pair[1].jsonify_chart()})

        return json.dumps(result_json)
    except Exception as ex:
        return json.dumps({"err": str(ex)})



@app.route('/relocate', methods=['POST'])
@cross_origin()
def relocate_charts():
    try:
        radix_chart = get_radix_from_json(request.json.get('radix'))
        longitude = request.json.get('longitude')
        latitude = request.json.get('latitude')
        tz = request.json.get('tz')

        return_chart = None  # TODO

        manager.relocate(radix=radix_chart, geo_longitude=longitude, geo_latitude=latitude, timezone=tz)

        return json.dumps(radix_chart.jsonify_chart())

    except Exception as ex:
        return json.dumps({"err": str(ex)})

# =============== Extraction and validation =============== #


def get_return_params_from_json(return_params):
    if not return_params:
        raise RuntimeError("Missing return_params")

    planet = return_params.get("return_planet")
    if not (planet in ["Sun", "Moon"]):
        raise RuntimeError(f"Invalid return planet: {planet}")

    harmonic = int(return_params.get("return_harmonic"))
    if harmonic < 1 or harmonic > 36:
        raise RuntimeError(f"Invalid harmonic: {harmonic}")

    try:
        longitude = float(return_params.get("return_longitude"))
    except ValueError as ex:
        logger.error(f"Longitude cannot be parsed to float: {return_params.get('return_longitude')}")
        raise ex

    try:
        latitude = float(return_params.get("return_latitude"))
    except ValueError as ex:
        logger.error(f"Longitude cannot be parsed to float: {return_params.get('return_latitude')}")
        raise ex

    start_date_raw = return_params.get("return_start_date")
    if not start_date_raw:
        raise RuntimeError("Missing parameter return_start_date")

    try:
        qty_of_returns = int(return_params.get("return_quantity"))
    except ValueError as ex:
        logger.error(f"Return qty cannot be parsed to int: {return_params.get('return_quantity')}")
        raise ex

    tz = return_params.get('tz')
    if not tz:
        raise RuntimeError("Missing timezone")

    start_date = pendulum.parse(start_date_raw)
    start_date = start_date.in_timezone(tz)
    return_body = settings.STRING_TO_INT_PLANET_MAP[planet]

    return {
        "geo_longitude": longitude,
        "geo_latitude": latitude,
        "date": start_date,
        "body": return_body,
        "harmonic": harmonic,
        "return_quantity": qty_of_returns
    }


def get_radix_from_json(json):
    local_datetime = json.get('local_datetime')
    tz = json.get('tz')

    if not local_datetime:
        raise RuntimeError('No datetime provided')
    if not tz:
        raise RuntimeError('Missing timezone')

    try:
        pendulum_dt = pendulum.parse(local_datetime)
        pendulum_dt = pendulum_dt.in_timezone(tz)
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
