from flask import Flask
from flask_cors import CORS, cross_origin
from flask_restx import Resource, Api
import logging
import pendulum
import json
import requests
from timezonefinder import TimezoneFinder

from src.dll_tools.chartmanager import ChartManager
from src.models.chartdata import ChartData
from src import settings
from src.app.schemas import radix_query_schema, return_chart_query_schema, relocation_query_schema

app = Flask(__name__)
CORS(app)
api = Api(app)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M')

manager = ChartManager()
tf = TimezoneFinder()


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
            logger.exception("Error while calculating radix:")
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
                result_json.append({"radix": pair[0].jsonify_chart(), "solunar": pair[1].jsonify_chart()})

            return json.dumps(result_json)
        except Exception as ex:
            logger.exception("Error while calculating solunar:")
            return json.dumps({"err": str(ex)})


@cross_origin()
@api.route('/relocate')
class Relocate(Resource):
    @api.expect(relocation_query_schema)
    def post(self):
        try:
            geo_results = geocode(api.payload['location'])

            radix_dt = pendulum.parse(api.payload['radix']['local_datetime'])

            tz = geo_results['tz']
            radix_dt_in_tz = radix_dt.in_tz(tz)
            chartdata = manager.create_chartdata(
                radix_dt_in_tz,
                geo_results['longitude'],
                geo_results['latitude'],
                place_name=geo_results['place_name']
            )
            radix = chartdata

            solunar = api.payload.get('solunar', None)
            if solunar:
                return_dt = pendulum.parse(api.payload['solunar']['local_datetime'])
                return_dt_in_tz = return_dt.in_tz(tz)
                solunar = manager.create_chartdata(
                    return_dt_in_tz,
                    geo_results['longitude'],
                    geo_results['latitude'],
                    geo_results['place_name']
                )
                manager.precess(radix=radix, transit_chart=solunar)

            if solunar:
                return json.dumps({"radix": radix.jsonify_chart(), "solunar": solunar.jsonify_chart()})
            else:
                return json.dumps(radix.jsonify_chart())

        except Exception as ex:
            logger.exception("Error while relocating:")
            return json.dumps({"err": str(ex)})


# =================== Utility functions =================== #

def get_solunar_return_params_from_json(return_params: dict) -> dict:
    geo_results = geocode(return_params['return_location'])

    start_date_raw = return_params['return_start_date']
    start_date = pendulum.parse(start_date_raw)
    start_date_in_tz = start_date.in_timezone(geo_results['tz'])

    body_name = return_params['return_planet']
    planet = settings.STRING_TO_INT_PLANET_MAP[body_name]
    longitude = float(geo_results['longitude'])
    latitude = float(geo_results['latitude'])
    harmonic = int(return_params['return_harmonic'])
    qty_of_returns = int(return_params['return_quantity'])

    return {
        "date": start_date_in_tz,
        "body": planet,
        "geo_longitude": longitude,
        "geo_latitude": latitude,
        "harmonic": harmonic,
        "return_quantity": qty_of_returns,
        "place_name": geo_results['place_name'],
    }


def get_radix_chart_from_json(payload: dict) -> ChartData:
    geo_results = geocode(payload['location'])

    local_dt = pendulum.parse(payload['local_datetime'])
    dt_in_tz = local_dt.in_timezone(geo_results['tz'])

    radix_chart = manager.create_chartdata(local_datetime=dt_in_tz,
                                           geo_longitude=geo_results['longitude'],
                                           geo_latitude=geo_results['latitude'],
                                           place_name=geo_results['place_name'])
    return radix_chart


def geocode(location: str) -> dict:
    res = requests.get(settings.MAPQUEST_ENDPOINT, params={
        'key': settings.MAPQUEST_KEY,
        'location': location,
    })
    res.raise_for_status()

    results = res.json()['results'][0]['locations'][0]
    longitude = float(results['latLng']['lng'])
    latitude = float(results['latLng']['lat'])
    tz = tf.timezone_at(lng=longitude, lat=latitude)
    place_name = f"{results['adminArea5']}, {results['adminArea3']}, {results['adminArea1']}"
    return {
        'longitude': longitude,
        'latitude': latitude,
        'tz': tz,
        'place_name': place_name,
    }


if __name__ == '__main__':
    while True:
        try:
            app.run(debug=True, port=5000)
        except KeyboardInterrupt:
            exit(1)
        except Exception as e:
            logger.exception(msg=f'Error: {str(e)}')
