YaPi REST API
==============
> Тестовое задание на поступление в школу бэкэнд-разработки Яндекс

Назначение
----------

Веб-служба, разработанна на **Python** с ипользованием фреймворка **Flask** и 
предназначена для хранения поступающих наборов данных ( выгрузок от поставищиков ) 
с жителями, позволяет их просматривать и редактировать информацию об отдельных жителях.

Реализованные методы
--------------------

> Изменения v2.0:
> *Добавлен 4 метод и обновлены модульные тесты*

1. Принимает на вход набор с данными о жителях в формате `json` и сохраняет его с уникальным идентификатором `import_id`:

        POST | /imports

2. Изменяет информацию о жителе в указанном наборе данных:

        PATCH | /imports/ <int: import_id> /citizens/ <int: citizens_id>

3. Возвращает список всех жителей для указанного набора данных:

        GET | /imports/ <int: import_id> /citizens

4. Возвращает жителей и количество подарков, которые они будут покупать своим ближайшим родственникам (1-го порядка), сгруппированных по месяцам из указанного набора данных:

        GET | /imports/ <int: import_id> /citizens/birthdays

Установка
---------

1. Установите Python 3.
2. Запустите `setup.sh` (Linux, OS X, Cygwin) или `setup.bat` (Windows): в директории будет создано виртуальное окружение и установлены все необходимые раширения для работы приложения. В другом случае, выполните следующие команды:

        $ python -m venv venv                                 (Linux)
        $ source venv/bin/activate
        (venv) $ pip install -r requirements.txt

        python -m venv venv                                 (Windows)
        venv\Scripts\activate 
        (venv) pip install -r requirements.txt

3. Выполните команду `python manage.py db upgrade` для создания и обновления базы данных приложения.

4. (Для Linux) Чтобы запустить локальный сервер, необходимо создать юнит сервисного модуля **systemd** (*deployment/yapi.servece*), который позволит системе инициализации **Ubuntu** автоматически запускать `Gunicorn` и обслуживать приложение при каждой загрузке сервера

        $ sudo nano /etc/systemd/system/appname.service

   */etc/systemd/system/appname.service*
   ```
   [Unit]
   Description=Gunicorn instance to serve appname
   After=network.target
   ```

   В разделе [**Unit**] определяются метаданные и зависимости.

   - `Description` — описание сервиса. **appname** — имя приложения
   - `After` — определяет загрузку пользовательского юнита после запуска **network.target**

   */etc/systemd/system/appname.service*
   ```
   [Service]
   User=username
   Group=www-data
   WorkingDirectory=/home/username/appname
   Environment="PATH=/home/username/appname/venv/bin"
   ExecStart=/home/username/appname/venv/bin/gunicorn -b 0.0.0.0:8080 -w 4 manage:app
   ```

   В разделе [**Service**] указывается имя пользователя *username* и группа *www-data*, под которой будет    заупскаться процесс.
   
   - `WorkingDirectory` — путь к рабочей директории приложения
   - `Environment` — путь к виртуальному окружению *venv*
   - `ExecStart` — путь к исполняемому файлу **gunicorn** и параметры с которыми он запускается: `0.0.0.0:8080`    (ip адрес веб-службы), `-w 4` (количество рабочих процессов), `manage:app` (модуль, содержащий приложение `:`    имя этого приложения)
   
   */etc/systemd/system/appname.service*
   ```
   [Install]
   WantedBy=multi-user.target
   ```

   В разделе [**Install**] находятся параметры, которые указывают **systemd**, когда запускать сервис. В данном случае: когда система запущена и работает.

После создания юнита, его необходимо запустить и включить запуск при загрузке ситсемы:

        $ sudo systemctl start appname.service
        $ sudo systemctl enable appname.service

Проверить статус:

        $ sudo systemctl status appname.service

Зависимости приложения
----------------------
Приложение для работы использует фреймворк `Flask` и следующие расширения:

- `Flask-SQLAlchemy` — фреймворк для работы с реляционными базами данных
- `Flask-Script` — парсер командной строки
- `Flask-Migrate` — фреймворк миграции базы данных
- `Gunicorn` — WSGI-сервер

А так же расширение `Cerebrus` для реализации валидации входящих данных и клиент `HTTPie` для тестирование веб-службы и имтиации запросов.

>Все остальные зависимости описаны в файле `requirements.txt`

Тестирование
------------
Для тестирование веб-службы используется модуль Python **unittest** и  **coverage** — для измерения охвата покрытия тестирования.

Модульное тестирование запускается командой `test`:

        (venv) $ python manage.py test                         (Linux)
        (venv) python manage.py test                         (Windows)

Для того, чтобы произвести модульное тестирование с охватом его покрытия, в файле `manage.py` нужно изменить значение атрибута **coverage** функции *test()* на `True` и выполнить команду `test`:

        @manager.command
        def test( coverage = True ):
            # ...

Структура приложения
--------------------
        yapi
        ├── app
        │   ├── main
        |   |   ├── __init__.py     # создание макета приложения
        |   |   ├── errors.py       # обработчики ошибок
        |   |   └── views.py        # функции представления
        │   ├── __init__.py         # конструктор пакета приложения
        │   ├── models.py           # модели базы данных
        │   ├── relatives.py        # функции для установкии двусторонности родства
        │   └── validation.py       # схема и функции валидации
        |
        ├── deployment
        |    └── systemd.system     # сервис для запуска локального
        |        └── yapi.service   # сервера
        |
        ├── migrations              # файлы миграции базы данных
        |   └── ...
        |
        ├── tests
        |   ├── __init__.py
        |   ├── test_api.py         # набор тестирования веб-службы
        |   ├── test_basics.py      # базовое тестирование
        |   └── ...
        |  
        ├── manage.py               # инициализация приложения
        ├── config.py               # настройки приложения
        └── ...
