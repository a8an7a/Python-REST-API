import numpy as np
from datetime import datetime
from cerberus import Validator

def _unique( data ):
    try: citizen_id = [ el['citizen_id'] for el in data ]
    except KeyError: return False
    return np.unique(citizen_id).size == len(citizen_id)

class MyValidator(Validator):
    def _validate_borndate(self, date, field, value):
        """ Проверка даты рождения на корректность.

        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        if date:
            try: 
                born = datetime.strptime(value, '%d.%m.%Y')
                if born > datetime.today():
                    self._error(field, 'Must be less than current date')
            except ValueError: 
                self._error(field, 'Must be in DD.MM.YYYY format')

schema = {
    'citizen_id': { 'type': 'integer', 'min': 0 },
    'town':       { 'type': 'string',  'empty': False, 'maxlength': 256 },
    'street':     { 'type': 'string',  'empty': False, 'maxlength': 256 },
    'building':   { 'type': 'string',  'empty': False, 'maxlength': 256 },
    'apartment':  { 'type': 'integer', 'min': 0 },
    'name':       { 'type': 'string',  'empty': False, 'maxlength': 256 },
    'birth_date': { 'type': 'string',  'borndate': True },
    'gender':     { 'type': 'string',  'allowed': ['male', 'female'] },
    'relatives':  { 'type': 'list',    'schema': {'type': 'integer'} }
}

cerberus_lite = MyValidator(schema)        

# Строгая схема, где все поля должны быть заолнены
cerberus = MyValidator(schema, require_all=True) 