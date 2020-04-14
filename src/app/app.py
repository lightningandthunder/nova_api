from flask import Flask
from flask_cors import CORS, cross_origin
from flask_restx import Resource, Api
import logging
import pendulum
import json

from src.dll_tools.chartmanager import ChartManager
from src import settings
from .schemas import radix_query_schema, return_chart_query_schema, relocation_query_schema

app = Flask(__name__)
CORS(app)
api = Api(app)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M')

manager = ChartManager()


# ========================= Routes ======================== #


@cross_origin()
@api.route('/radix')
class Radix(Resource):

    @api.expect(radix_query_schema)
    def post(self):
        try:
            radix_chart = get_radix_chart_from_json(api.payload)
            return json.dumps(radix_chart.jsonify_chart())
        except Exception as ex:
            return json.dumps({"err": str(ex)})


@cross_origin()
@api.route('/returns')
class SolunarReturns(Resource):

    @api.expect(return_chart_query_schema)
    def post(self):
        try:
            radix_chart = get_radix_chart_from_json(api.payload['radix'])
            return_params = get_solunar_return_params_from_json(api.payload['return_params'])

            return_pairs = manager.generate_radix_return_pairs(radix=radix_chart, **return_params)

            result_json = []
            for pair in return_pairs:
                result_json.append({"radix": pair[0].jsonify_chart(), "return_chart": pair[1].jsonify_chart()})

            return json.dumps(result_json)
        except Exception as ex:
            return json.dumps({"err": str(ex)})


@cross_origin()
@api.route('/relocate')
class Relocate(Resource):

    @api.expect(relocation_query_schema)
    def post(self):
        try:
            try:
                longitude = float(api.payload['longitude'])
            except ValueError:
                raise ValueError(f"Cannot parse longitude {api.payload['longitude']} to float")

            try:
                latitude = float(api.payload['latitude'])
            except ValueError:
                raise ValueError(f"Cannot parse latitude {api.payload['latitude']} to float")

            radix_dt = pendulum.parse(api.payload['radix']['local_datetime'])

            tz = api.payload['tz']
            radix_dt_in_tz = radix_dt.in_tz(tz)
            rel_radix = manager.create_chartdata(radix_dt_in_tz, longitude, latitude)

            rel_return = None
            print(api.payload)
            if api.payload['return_chart'] is not None:
                return_dt = pendulum.parse(api.payload['return_chart']['local_datetime'])
                return_dt_in_tz = return_dt.in_tz(tz)
                rel_return = manager.create_chartdata(return_dt_in_tz, longitude, latitude)
                manager.precess_into_sidereal_framework(radix=rel_radix, transit_chart=rel_return)

            if rel_return:
                return json.dumps({"radix": rel_radix.jsonify_chart(), "return_chart": rel_return.jsonify_chart()})
            else:
                return json.dumps(rel_radix.jsonify_chart())

        except Exception as ex:
            return json.dumps({"err": str(ex)})


# @app.route('/relocate', methods=['POST'])
# @cross_origin()
# def relocate_charts():
#     try:
#         longitude = float(request.json.get('longitude'))
#         latitude = float(request.json.get('latitude'))
#         radix_dt = pendulum.parse(request.json.get('radix').get('local_datetime'))
#         tz = request.json.get('tz')
#         radix_dt = radix_dt.in_tz(tz)
#         rel_radix = manager.create_chartdata(radix_dt, longitude, latitude)
#
#         rel_return = None
#         if request.json.get('return_chart') is not None:
#             return_dt = pendulum.parse(request.json.get('return_chart').get('local_datetime'))
#             return_dt = return_dt.in_tz(tz)
#             rel_return = manager.create_chartdata(return_dt, longitude, latitude)
#             manager.precess_into_sidereal_framework(radix=rel_radix, transit_chart=rel_return)
#
#         if rel_return:
#             return json.dumps({"radix": rel_radix.jsonify_chart(), "return_chart": rel_return.jsonify_chart()})
#         else:
#             return json.dumps(rel_radix.jsonify_chart())
#
#     except Exception as ex:
#         return json.dumps({"err": str(ex)})


# =================== Utility functions =================== #

def get_solunar_return_params_from_json(return_params):
    start_date_raw = return_params['return_start_date']
    start_date = pendulum.parse(start_date_raw)
    start_date_in_tz = start_date.in_timezone(return_params['tz'])

    body_name = return_params['return_planet']
    if body_name not in ['Sun', 'Moon']:
        raise ValueError(f"Invalid return planet selected: {return_params['return_planet']}")
    planet = settings.STRING_TO_INT_PLANET_MAP[body_name]

    try:
        longitude = float(return_params['return_longitude'])
    except ValueError:
        raise ValueError(f"Cannot parse longitude {return_params['return_longitude']} to float")

    try:
        latitude = float(return_params['return_latitude'])
    except ValueError:
        raise ValueError(f"Cannot parse latitude {return_params['return_latitude']} to float")

    try:
        harmonic = int(return_params['return_harmonic'])
    except ValueError:
        raise ValueError(f"Cannot parse harmonic {return_params['return_harmonic']} to int")

    try:
        qty_of_returns = int(return_params['return_quantity'])
    except ValueError:
        raise ValueError(f"Cannot parse return quantity {return_params['return_quantity']} to int")

    return {
        "date": start_date_in_tz,
        "body": planet,
        "geo_longitude": longitude,
        "geo_latitude": latitude,
        "harmonic": harmonic,
        "return_quantity": qty_of_returns,
    }


def get_radix_chart_from_json(payload):
    local_dt = pendulum.parse(payload['local_datetime'])
    dt_in_tz = local_dt.in_timezone(payload['tz'])

    try:
        longitude = float(payload['longitude'])
    except ValueError:
        raise ValueError(f"Cannot parse longitude {payload['longitude']} to float")

    try:
        latitude = float(payload['latitude'])
    except ValueError:
        raise ValueError(f"Cannot parse latitude {payload['latitude']} to float")

    radix_chart = manager.create_chartdata(local_datetime=dt_in_tz,
                                           geo_longitude=longitude,
                                           geo_latitude=latitude)

    return radix_chart


if __name__ == '__main__':
    while True:
        try:
            app.run(debug=True, port=5000)
        except KeyboardInterrupt:
            exit(1)
        except Exception as e:
            logger.exception(msg=f'Error: {str(e)}')
