from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import logging
import pendulum
from chartmanager import ChartManager
from src.dll_tools.tests.functionality_tests import run_tests


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
    local_datetime = request.json.get('local_datetime')
    tz = request.json.get('tz')
    if not local_datetime:
        return('No datetime provided')

    pendulum_dt = pendulum.parse(local_datetime)

    if tz:
        try:
            pendulum_dt = pendulum_dt.in_timezone(tz)
            print(pendulum_dt)
        except InvalidTimezone as ex:
            logger.error(f"Bad timezone: {str(ex)}")
            return str(ex)

    longitude = request.json.get('longitude')
    latitude = request.json.get('latitude')

    radix_chart = manager.create_chartdata(local_datetime=pendulum_dt,
                                           geo_longitude=float(longitude),
                                           geo_latitude=float(latitude))

    return radix_chart.jsonify_chart()


if __name__ == '__main__':
    while True:
        try:
            run_tests(manager)
            app.run(debug=True, port=5000)
        except KeyboardInterrupt:
            exit(1)
        except Exception as e:
            logger.exception(msg=f'Error: {str(e)}')
