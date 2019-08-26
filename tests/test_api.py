import unittest, json, pickle, numpy as np
from datetime import datetime
from app import create_app, db
from app.models import Import, Citizen
from app.validation import _unique

class APITestCase( unittest.TestCase ):
    def setUp( self ):
        """ Инициализация экземпляра приложения
        """
        self.app = create_app('testing')
        self.app_contex = self.app.app_context()
        self.app_contex.push()
        db.create_all()
        self.client = self.app.test_client( use_cookies = False )

    def tearDown( self ):
        """ Удаление данных
        """
        db.session.remove()
        db.drop_all()
        self.app_contex.pop()

    def get_api_headers( self ):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Date': datetime.today().strftime('%a, %d %b %Y %H:%M:%S GMT')
        }

    def test_post_201( self ):
        """ Отправка корректного POST-запроса
        """ 
        # Запрос на создание 
        import_id = Import.get_index()
        response = self.client.post(
            '/imports',
            headers = self.get_api_headers(),
            data = json.dumps({
                "citizens" : [
                    {
                        "citizen_id": 1, "town": "Москва", "street": "Льва Толстого",
                        "building": "16к7стр5", "apartment": 7, "name": "Иванов Иван Иванович",
                        "birth_date": "26.12.1986", "gender": "male", "relatives": [2, 3]
                    },
                    {
                        "citizen_id": 2, "town": "Москва", "street": "Льва Толстого",
                        "building": "16к7стр5", "apartment": 7, "name": "Иванов Сергей Иванович",
                        "birth_date": "01.04.1997", "gender": "male", "relatives": [1, 3]
                    },
                    {
                        "citizen_id": 3, "town": "Керчь", "street": "Иосифа Бродского",
                        "building": "2", "apartment": 11, "name": "Романова Мария Леонидовна",
                        "birth_date": "23.11.1986", "gender": "female", "relatives": []
                    }
                ]
            })
        )
        # Проверка кода ответа
        self.assertEqual( response.status_code, 201 )
        # Проверка тела ответа
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response['data'], {'import_id': import_id} )

        # Проверка родословной добавленных пользователей
        # на корректность 
        result = True
        import_citizens = Citizen.query.filter_by( import_id = import_id ).all()
        for citizen in import_citizens:
            for rel_id in pickle.loads(citizen.relatives):
                relative = Citizen.query.filter_by( citizen_id = rel_id, import_id = import_id ).first()
                relatives = pickle.loads(relative.relatives)
                if not citizen.citizen_id in relatives:
                    result = False
        
        self.assertTrue( result )

    def test_post_400( self ):
        """ Тестирование валидации веб-службы (некорректные POST-запросы)
        """
        # Имитируем создание горожанина
        citizen = {
            "citizen_id": 1, "town": "Москва", "street": "Льва Толстого",
            "building": "16к7стр5", "apartment": 7, "name": "Иванов Иван Иванович",
            "birth_date": "26.12.1986", "gender": "male", "relatives": []
        }

        # Валидация: Отрицательный идентификатор горожанина
        citizen['citizen_id'] = -1
        response = self.client.post(
            '/imports',
            headers = self.get_api_headers(),
            data = json.dumps({ "citizens" : [ citizen ] })
        )
        self.assertEqual( response.status_code, 400 )
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response['Error 400'], 'Bad Request' )

        # Валидация: Пустое поле
        citizen['town'] = ''
        response = self.client.post(
            '/imports',
            headers = self.get_api_headers(),
            data = json.dumps({ "citizens" : [ citizen ] })
        )
        self.assertEqual( response.status_code, 400 )
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response['Error 400'], 'Bad Request' )

        # Валидация: Некорректная дата
        citizen['birth_date'] = '31.02.1999'
        response = self.client.post(
            '/imports',
            headers = self.get_api_headers(),
            data = json.dumps({ "citizens" : [ citizen ] })
        )
        self.assertEqual( response.status_code, 400 )
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response['Error 400'], 'Bad Request' )

        # Валидация: Некорректный пол
        citizen['gender'] = 'gay'
        response = self.client.post(
            '/imports',
            headers = self.get_api_headers(),
            data = json.dumps({ "citizens" : [ citizen ] })
        )
        self.assertEqual( response.status_code, 400 )
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response['Error 400'], 'Bad Request' )

        # Валидация: Лишнее поле
        citizen['state'] = 'good'
        response = self.client.post(
            '/imports',
            headers = self.get_api_headers(),
            data = json.dumps({ "citizens" : [ citizen ] })
        )
        self.assertEqual( response.status_code, 400 )
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response['Error 400'], 'Bad Request' )

        # Валидация: Неописанное поле
        citizen.pop('citizen_id')
        response = self.client.post(
            '/imports',
            headers = self.get_api_headers(),
            data = json.dumps({ "citizens" : [ citizen ] })
        )
        self.assertEqual( response.status_code, 400 )
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response['Error 400'], 'Bad Request' )

    def test_post_unique( self ):
        """ Проверка на уникальность идентификаторов горожан
        """
        # Запрос на создание
        import_id = Import.get_index()
        response =self.client.post(
            '/imports',
            headers = self.get_api_headers(),
            data = json.dumps({
                "citizens" : [
                    {
                        "citizen_id": 1, "town": "Москва", "street": "Льва Толстого",
                        "building": "16к7стр5", "apartment": 7, "name": "Иванов Иван Иванович",
                        "birth_date": "26.12.1986", "gender": "male", "relatives": [2, 3]
                    },
                    {
                        "citizen_id": 2, "town": "Москва", "street": "Льва Толстого",
                        "building": "16к7стр5", "apartment": 7, "name": "Иванов Сергей Иванович",
                        "birth_date": "01.04.1997", "gender": "male", "relatives": [1, 3]
                    },
                    {
                        "citizen_id": 3, "town": "Керчь", "street": "Иосифа Бродского",
                        "building": "2", "apartment": 11, "name": "Романова Мария Леонидовна",
                        "birth_date": "23.11.1986", "gender": "female", "relatives": [1, 2]
                    }
                ]
            })
        )
        self.assertEqual( response.status_code, 201 )
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response['data'], {'import_id': import_id} )

        # Проверка на уникальность идентификаторов
        citizens = Citizen.query.filter_by( import_id = import_id ).all()
        citizens_id = [ citizen.id for citizen in citizens ]

        self.assertTrue( len(citizens_id) == np.unique(citizens_id).size )

    def test_patch_404( self ):
        """ Изменение данных несуществующего горожанина
        """
        response = self.client.patch(
            '/imports/1/citizens/1',
            headers = self.get_api_headers(),
            data = json.dumps({
                "town": "Москва", "street": "Ленина", "building": "16к7стр5",
                "apartment": 7, "name": "Иванов Иван Иванович", 
                "birth_date": "26.12.1986", "gender": "male", "relatives": [2, 3]
            })
        )
        self.assertEqual( response.status_code, 404 )
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response['Error 404'], 'Not Found' )

    def test_patch_200( self ):
        """ Корректное изменение данных горожанина
        """
        citizen = [
            {
                "citizen_id": 1, "town": "Москва", "street": "Льва Толстого",
                "building": "16к7стр5", "apartment": 7, "name": "Иванов Иван Иванович",
                "birth_date": "26.12.1986", "gender": "male", "relatives": [2, 3]
            },
            {
                "citizen_id": 2, "town": "Москва", "street": "Льва Толстого",
                "building": "16к7стр5", "apartment": 7, "name": "Иванов Сергей Иванович",
                "birth_date": "01.04.1997", "gender": "male", "relatives": [1, 3]
            },
            {
                "citizen_id": 3, "town": "Керчь", "street": "Иосифа Бродского",
                "building": "2", "apartment": 11, "name": "Романова Мария Леонидовна",
                "birth_date": "23.11.1986", "gender": "female", "relatives": []
            }
        ]

        old_relatives = citizen[2]['relatives'] #  для проверки родственных связей

        # Запрос на создание
        import_id = Import.get_index()
        self.client.post(
            '/imports',
            headers = self.get_api_headers(),
            data = json.dumps({ "citizens" : citizen })
        )

        # Запрос на изменение данных
        new_relatives = [2]
        citizen[2]['relatives'] = new_relatives

        response = self.client.patch(
            '/imports/1/citizens/3',
            headers = self.get_api_headers(),
            data = json.dumps({ "relatives": new_relatives })
        )

        self.assertEqual( response.status_code, 200 )
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response, citizen[2] )

        # Проверка: корректна ли двусторонность родства
        # после изменения родственников
        result = True
        for rel_id in old_relatives:
            relative = Citizen.query.filter_by( import_id = import_id, citizen_id = rel_id ).first()
            relatives = pickle.loads(relative.relatives)
            if 3 in relatives:
                result = False

        for rel_id in new_relatives:
            relative = Citizen.query.filter_by( import_id = import_id, citizen_id = rel_id ).first()
            relatives = pickle.loads(relative.relatives)
            if not 3 in relatives:
                result = False

        self.assertTrue( result )

    def test_patch_400( self ):
        """ Некорректное изменение данных горожанина
        """
        # Запрос на создание горожанина
        self.client.post(
            '/imports',
            headers = self.get_api_headers(),
            data = json.dumps({ "citizens" : [
                {
                    "citizen_id": 1, "town": "Москва", "street": "Льва Толстого",
                    "building": "16к7стр5", "apartment": 7, "name": "Иванов Иван Иванович",
                    "birth_date": "26.12.1986", "gender": "male", "relatives": []
                }   
            ]})
        )

        # Некорректный запрос на изменение 
        # данных горожанина
        response = self.client.patch(
            '/imports/1/citizens/1',
            headers = self.get_api_headers(),
            data = json.dumps({ "relatives": [3] })
        )

        self.assertEqual( response.status_code, 400 )
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response['Error 400'], 'Bad Request' )

    def test_get_404( self ):
        """ Тестирование GET-запроса для выгрузки данных
        """
        # Запрос несуществующих данных
        response = self.client.get(
            '/imports/1/citizens',
            headers = self.get_api_headers()
        )

        self.assertEqual( response.status_code, 404 )
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response['Error 404'], 'Not Found' )

    def test_get_200( self ):
        """ Тестирование GET-запроса для выгрузки данных
        """
        # Запрос данных
        citizen = [
            {
                "citizen_id": 1, "town": "Москва", "street": "Льва Толстого",
                "building": "16к7стр5", "apartment": 7, "name": "Иванов Иван Иванович",
                "birth_date": "26.12.1986", "gender": "male", "relatives": [2, 3]
            },
            {
                "citizen_id": 2, "town": "Москва", "street": "Льва Толстого",
                "building": "16к7стр5", "apartment": 7, "name": "Иванов Сергей Иванович",
                "birth_date": "01.04.1997", "gender": "male", "relatives": [1, 3]
            },
            {
                "citizen_id": 3, "town": "Керчь", "street": "Иосифа Бродского",
                "building": "2", "apartment": 11, "name": "Романова Мария Леонидовна",
                "birth_date": "23.11.1986", "gender": "female", "relatives": [1, 2]
            }
        ]

        # Запрос на создание
        self.client.post(
            '/imports',
            headers = self.get_api_headers(),
            data = json.dumps({ "citizens" : citizen })
        )

        # Запрос выгрузки данных
        response = self.client.get(
            '/imports/1/citizens',
            headers = self.get_api_headers()
        )

        self.assertEqual( response.status_code, 200 )
        json_response = json.loads( response.get_data( as_text = True ) )
        self.assertEqual( json_response['data'], citizen )