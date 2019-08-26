import pickle
from flask import abort
from .models import Citizen

def set_relatives( import_id ):
    """ Устанавливаем родство среди граждан выгрузки import_id,
    если оно не указано.

    view function -> ('/imports', methods = ['POST'])
    """
    import_citizens = Citizen.query.filter_by( import_id = import_id ).all()
    
    for citizen in import_citizens:
        for rel_id in pickle.loads(citizen.relatives):
            
            relative = Citizen.query.filter_by( citizen_id = rel_id, import_id = import_id ).first()
            if relative is None:
                abort(400)

            relatives = pickle.loads(relative.relatives)
            
            if not citizen.citizen_id in relatives:
                relatives.append(citizen.citizen_id)
                relative.relatives = pickle.dumps(relatives)

def new_relatives( import_id, citizen_id, old_rel, new_rel ):
    """ Устанваливаем новое родство горожанину citizen_id при обновлении 
    данных выгрузки import_id, если потребуется.

    view function -> ('/imports/<int:import_id>/citizens', methods = ['PATCH']) 
    """
    if old_rel == new_rel:
        return

    del_rel = set(old_rel) & set(new_rel)

    for el in del_rel:
        old_rel.pop( old_rel.index(el) )
        new_rel.pop( new_rel.index(el) )

    for rel_id in old_rel:
        relative = Citizen.query.filter_by( citizen_id = rel_id, import_id = import_id ).first()
        relatives = pickle.loads(relative.relatives)

        if citizen_id in relatives:
            relatives.pop( relatives.index(citizen_id) )
            relative.relatives = pickle.dumps(relatives)

    for rel_id in new_rel:
        relative = Citizen.query.filter_by( citizen_id = rel_id, import_id = import_id ).first()
        if relative is None: abort(400)
        relatives = pickle.loads(relative.relatives)

        if not citizen_id in relatives:
            relatives.append(citizen_id)
            relative.relatives = pickle.dumps(relatives)