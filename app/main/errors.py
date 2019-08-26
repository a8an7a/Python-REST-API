from . import main
from flask import make_response, jsonify

@main.app_errorhandler(400)
def bad_request( e ):
    return make_response( jsonify({ 'Error 400': 'Bad Request' }), 400 )

@main.app_errorhandler(404)
def not_found( e ):
    return make_response( jsonify({ 'Error 404': 'Not Found' }), 404 )

@main.app_errorhandler(500)
def internal_server_error( e ):
    return make_response( jsonify({ 'Error 500': 'Internal Server Error' }), 500 )