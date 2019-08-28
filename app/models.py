import pickle
from . import db
from sqlalchemy import text
from datetime import datetime

class Import( db.Model ):
    __tablename__ = 'imports'
    id        = db.Column( db.Integer, primary_key = True )
    citizens  = db.relationship('Citizen', backref='citizen', lazy='dynamic')

    def __repr__( self ):
        return '<Import %r>' % self.id

    @staticmethod
    def get_index():
        query = text('SELECT * FROM imports ORDER BY id DESC LIMIT 1')
        result = db.engine.execute(query).fetchone()
        return 1 if result is None else result['id'] + 1 

class Citizen( db.Model ):
    __tablename__ = 'citizens'
    id         = db.Column( db.Integer,     primary_key = True)
    import_id  = db.Column( db.Integer,     db.ForeignKey('imports.id'), nullable = False )
    citizen_id = db.Column( db.Integer,     nullable = False, index = True )

    town       = db.Column( db.String(256), nullable = False ) 
    street     = db.Column( db.String(256), nullable = False ) 
    building   = db.Column( db.String(256), nullable = False ) 
    apartment  = db.Column( db.Integer,     nullable = False ) 
    name       = db.Column( db.String(256), nullable = False ) 
    birth_date = db.Column( db.String(10),  nullable = False )
    gender     = db.Column( db.String(10),  nullable = False )
    relatives  = db.Column( db.PickleType() )

    def __repr__( self ):
        return '<Citizen id %r: import_id: %r, citizen_id: %r, %r, %r, %r, %r, %r, %r, %r, %r>' % (self.id, self.import_id, self.citizen_id, \
                self.town, self.street, self.building, self.apartment, self.name, self.birth_date, self.gender, pickle.loads(self.relatives))

    def get_age( self ):
        today = datetime.today()
        born = datetime.strptime(self.birth_date, '%d.%m.%Y')
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def get_month_birth( self ):
        return str(datetime.strptime(self.birth_date, '%d.%m.%Y').month)

    def to_json( self ):
        json_citizen = {
            'citizen_id': self.citizen_id,
            'town':       self.town,
            'street':     self.street,
            'building':   self.building,
            'apartment':  self.apartment,
            'name':       self.name,
            'birth_date': self.birth_date,
            'gender':     self.gender,
            'relatives':  pickle.loads(self.relatives)
        }
        return json_citizen