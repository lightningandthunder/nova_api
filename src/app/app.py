from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import logging
import pendulum

from ChartData import ChartData
from ChartManager import ChartManager
from swissephlib import SwissephLib

app = Flask(__name__)
# CORS(app, support_credentials=True, expose_headers='Authorization')

logger = logging.getLogger(__name__)
logging.basicConfig()

# swiss_lib = SwissephLib()
# manager = ChartManager(swiss_lib)

@app.route('/')
# @cross_origin(origin='*')
def index():
    return "Something works at least"

# @app.route('/radix', methods=['POST'])
# # @cross_origin(origin='*')
# def radix():
#     data = request.get_json(force=True)
#     if not data:
#         logger.info(msg="Didn't receive data.")
#         return jsonify({'error_string': 'Did not receive JSON.'})
#
#     else:
#         try:
#             local_datetime = data.get('local_datetime')
#             longitude = data.get('longitude')
#             latitude = data.get('latitude')
#
#             local_datetime_pendulum = pendulum.datetime(year=local_datetime.get('year'),
#                                                         month=local_datetime.get('month'),
#                                                         day=local_datetime.get('day'),
#                                                         hour=local_datetime.get('hour'),
#                                                         minute=local_datetime.get('minute'),
#                                                         second=local_datetime.get('second') or 0,
#                                                         tz=local_datetime.get('tz'))
#
#             radix_chart = manager.create_chartdata(local_datetime=local_datetime_pendulum,
#                                                    geo_longitude=longitude,
#                                                    geo_latitude=latitude)
#
#             return radix_chart.jsonify_chart()
#         except Exception as e:
#             logger.error(msg=str(e), exc_info=True)


if __name__ == '__main__':
    app.run(debug=False)
