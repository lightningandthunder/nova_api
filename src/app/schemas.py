from flask_restplus import fields

radix_query_schema = {
    'local_datetime': fields.Date(),
    'longitude': fields.Float(),
    'latitude': fields.Float(),
    'tz': fields.String(),
}

return_chart_param_schema = {
    'return_planet': fields.String(),
    'return_harmonic': fields.Integer(),
    'return_longitude': fields.Float(),
    'return_latitude': fields.Float(),
    'return_start_date': fields.Date(),
    'tz': fields.String(),
    'return_quantity': fields.Integer(),
}

return_chart_query_schema = {
    'radix': None,
    'return_params': fields.Nested(return_chart_param_schema)
}

relocation_query_schema = {
    'longitude': fields.Float(),
    'latitude': fields.Float(),
    'tz': fields.String(),
    'placeName': fields.String(),
    'radix': None,
    'return_chart': None,
}

# Representing the chart itself, not query parameters
radix_chart_schema = {
    'local_datetime': fields.Date(),
    'utc_datetime': fields.Date(),
    'julian_day': fields.String(),
    'tz': fields.String(),
    'sidereal_framework': None,
    'cusps_longitude': None,
    'angles_longitude': None,
    'planets_ecliptic': None,
    'planets_mundane': None,
    'planets_right_ascension': None
}

return_chart_schema = {

}