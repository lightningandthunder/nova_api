from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

# import calcs
# from Chart import Chart

app = Flask(__name__)
CORS(app, support_credentials=True)


@app.route('/query', methods=['POST'])
@cross_origin(origin='*')
def query():
    data = request.get_json(force=True)
    if not data:
        print("Didn't receive data.")
        return jsonify("No data!")
    else:
        location = data['inputLocation']
        location = location.strip()
        location = location.lower()

        birthDate = data['inputDate']
        birthDate = birthDate.strip()
        splitBirthDate = birthDate.split('/')
        month, day, year = (int(x) for x in splitBirthDate)

        birthTime = data['inputTime']
        splitBirthTime = birthTime.split(':')
        hour, minute = (int(x) for x in splitBirthTime)

        radix_chart = Chart(location, month, day, year, hour, minute)

        return jsonify([radix_chart.formatData()])
