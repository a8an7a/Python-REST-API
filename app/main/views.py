import pickle
import locale
from datetime import datetime

from .. import db
from . import main
from flask import jsonify, make_response, request, abort
from ..models import Import, Citizen
from ..validation import cerberus, cerberus_lite, _unique
from ..relatives import set_relatives, new_relatives

@main.after_request
def apply_caching( e ):
    """ Устанавливает местное время в заголовок ответа Date
    """
    e.headers["Date"] = datetime.today().strftime('%a, %d %b %Y %H:%M:%S GMT')
    return e

@main.route('/imports/<int:import_id>/citizens', methods = ['GET'])
def get_citizens( import_id ):
    """ Возвращает список всех жителей для указанного 
    набора данных
    """
    imports = Import.query.filter_by( id = import_id ).first()
    
    if imports is None:
        abort(404) 

    citizens = imports.citizens.all()
    return jsonify({ 'data': [ citizen.to_json() for citizen in citizens ] }), 200

@main.route('/imports', methods = ['POST'])
def post_citizens():
    """ Принимает на вход набор с данными о жителях в формате json 
    и сохраняет его с уникальным идентификатором import_id
    """
    if not request.json or not 'citizens' in request.json or \
    len(request.json['citizens']) == 0:
        abort(400)

    if not _unique( request.json['citizens'] ):
        abort(400)
    
    import_id = Import.get_index()

    for citizen in request.json['citizens']:
        if not cerberus.validate(citizen):
            abort(400)
        
        citizen['import_id'] = import_id
        citizen['relatives'] = pickle.dumps(citizen['relatives'])

        new_citizen = Citizen( **citizen )
        db.session.add(new_citizen)

    db.session.add( Import() )
    db.session.commit()

    set_relatives( import_id )

    return jsonify({ 'data' : {'import_id': import_id} }), 201

@main.route('/imports/<int:import_id>/citizens/<int:citizen_id>', methods = ['PATCH'])
def patch_citizen( import_id, citizen_id ):
    """ Изменяет информацию о жителе в указанном наборе данных
    """
    if not request.json or 'citizen_id' in request.json or \
    len(request.json) == 0:
        abort(400)

    citizen = Citizen.query.filter_by( import_id = import_id, citizen_id = citizen_id ).first()
    if citizen is None:
        abort(404)

    old_relatives = pickle.loads(citizen.relatives)

    if not cerberus_lite.validate(request.json):
        abort(400)
    
    for k, v in request.json.items():
        if k != 'relatives':
            setattr( citizen, k, v )
        else:
            if citizen_id in v:
                abort(400)
            setattr( citizen, k, pickle.dumps(v) )
            new_relatives( import_id, citizen_id, old_relatives, v )

    db.session.add(citizen)
    db.session.commit()

    return jsonify( citizen.to_json() ), 200