from flask_restx import fields

radix_query_schema = {
    'local_datetime': fields.Date(),
    'longitude': fields.Float(),
    'latitude': fields.Float(),
    'tz': fields.String(),
}

solunar_param_schema = {
    'return_planet': fields.String(),
    'return_harmonic': fields.Integer(),
    'return_longitude': fields.Float(),
    'return_latitude': fields.Float(),
    'return_start_date': fields.Date(),
    'tz': fields.String(),
    'return_quantity': fields.Integer(),
}

return_chart_query_schema = {
    'radix': fields.Nested(radix_query_schema),
    'return_params': fields.Nested(solunar_param_schema),
}

relocation_query_schema = {
    'longitude': fields.Float(),
    'latitude': fields.Float(),
    'local_datetime': fields.Date(),
    'tz': fields.String(),
    'radix': fields.Nested(radix_query_schema),
    'solunar': fields.Nested(solunar_param_schema),
}
