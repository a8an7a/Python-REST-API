import time, pickle, numpy as np
from datetime import datetime

from .. import db
from . import main
from flask import jsonify, make_response, request, abort
from ..models import Import, Citizen
from ..validation import cerberus, cerberus_lite, _unique
from ..relatives import set_relatives, new_relatives
from sqlalchemy.orm import load_only

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

    return jsonify({ 'data': citizen.to_json() }), 200

@main.route('/imports/<int:import_id>/citizens/birthdays', methods = ['GET'])
def get_birthdays( import_id ):
    """ Возвращает жителей и количество подарков, которые 
    они будут покупать своим ближайшим родственникам, 
    сгруппированных по месяцам из указанного набора данных
    """
    citizens = Citizen.query.filter_by( import_id = import_id ).all()

    if not citizens:
        abort(404)

    data = dict( (str(i), []) for i in range(1,13) )

    for сitizen in citizens:
        month = сitizen.get_month_birth()
        relatives = pickle.loads(сitizen.relatives)

        if not relatives:
            continue

        for relative in relatives:
            if not data[month]:
                data[month].append({ 'citizen_id': relative,
                                     'present': 1 })
            else:
                for el in data[month]:
                    if el['citizen_id'] == relative:
                        el['present'] += 1
                        break
                else:
                    data[month].append({ 'citizen_id': relative,
                                         'present': 1 })

    return jsonify({'data': data}), 200

@main.route('/imports/<int:import_id>/towns/stat/percentile/age', methods = ['GET'])
def get_percentile( import_id ):
    """ Возвращает статистику по городам для указанного 
    набора данных в разрезе возраста (полных лет) жителей
    """
    towns = db.session.query(Citizen.town).filter(Citizen.import_id == import_id).\
                       group_by(Citizen.town).all()

    if not towns:
        abort(404)

    towns = [ town[0] for town in towns ]

    data = []
    for town in towns:
        citizens = Citizen.query.filter_by( import_id = import_id, town = town ).all()
        age = [ citizen.get_age() for citizen in citizens ]
        data.append({
            'town': town,
            'p50': round( np.percentile(age, 50, interpolation = 'linear'), 2),
            'p75': round( np.percentile(age, 75, interpolation = 'linear'), 2),
            'p99': round( np.percentile(age, 99, interpolation = 'linear'), 2),
        })

    return jsonify({'data': data}), 200
