from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import logging
import pendulum

from chartmanager import ChartManager
from swissephlib import SwissephLib
from src.dll_tools.tests.functionality_tests import run_tests

app = Flask(__name__)
api = Api(app)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M')

swiss_lib = SwissephLib()
manager = ChartManager(swiss_lib)


# CORS(app, support_credentials=True, expose_headers='Authorization')

class TestMe(Resource):
    def get(self):
        return {'works?': 'works.'}

    def put(self, route):
        try:
            data = request.get_json()
            if not data:
                logger.info(msg="Didn't receive data.")
                return jsonify({'error_string': 'Did not receive JSON.'})

            logger.info(f'Received data: {data}')
            local_datetime = data.get('local_datetime')
            longitude = data.get('longitude')
            latitude = data.get('latitude')

            local_datetime_pendulum = pendulum.datetime(year=int(local_datetime.get('year')),
                                                        month=int(local_datetime.get('month')),
                                                        day=int(local_datetime.get('day')),
                                                        hour=int(local_datetime.get('hour')),
                                                        minute=int(local_datetime.get('minute')),
                                                        second=int(local_datetime.get('second')) or 0,
                                                        tz='America/New_York')
            # tz=local_datetime.get('tz'))

            radix_chart = manager.create_chartdata(local_datetime=local_datetime_pendulum,
                                                   geo_longitude=float(longitude),
                                                   geo_latitude=float(latitude))

            return radix_chart.jsonify_chart()

        except Exception as e:
            logger.exception(msg=str(e))


api.add_resource(TestMe, '/<string:route>')

# @app.route('/radix', methods=['POST'])
# @cross_origin(origin='*')
# def radix():
#     pass


if __name__ == '__main__':
    while True:
        try:
            run_tests()
            app.run(debug=True)
        except KeyboardInterrupt:
            exit(1)
        except Exception as e:
            logger.exception(msg='Error:')
