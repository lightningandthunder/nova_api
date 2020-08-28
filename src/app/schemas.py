from flask_restx import fields

radix_query_schema = {
    'local_datetime': fields.Date(),
    'location': fields.String(),
}

solunar_param_schema = {
    'return_planet': fields.String(),
    'return_harmonic': fields.Integer(),
    'return_start_date': fields.Date(),
    'return_location': fields.String(),
    'return_quantity': fields.Integer(),
}

return_chart_query_schema = {
    'radix': fields.Nested(radix_query_schema),
    'return_params': fields.Nested(solunar_param_schema),
}

relocation_query_schema = {
    'location': fields.String(),
    'local_datetime': fields.Date(),
    'radix': fields.Nested(radix_query_schema),
    'solunar': fields.Nested(solunar_param_schema),
}
