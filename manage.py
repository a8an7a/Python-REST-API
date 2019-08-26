#!/usr/bin/env python
import os

COV = None
if os.environ.get('COVERAGE'):
    import coverage
    COV = coverage.coverage( branch = True, include = 'app/*' )
    COV.start()

import sys
import click
from app import create_app, db
from app.models import Import, Citizen
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

""" Инициализация приложения 
"""
app = create_app('default')
manager = Manager(app)
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict( app = app, db = db, Import = Import, Citizen = Citizen )

manager.add_command( 'shell', Shell(make_context = make_shell_context) )
manager.add_command( 'db', MigrateCommand )

@manager.command
def test( coverage = False ):
    """ Модульное тестирование 

    coverage = True -> Выполнить измерение охвата
    """
    if coverage and not os.environ.get('COVERAGE'):
        import subprocess
        os.environ['COVERAGE'] = '1'
        os.execvp( sys.executable, [sys.executable] + sys.argv )

    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner( verbosity = 2 ).run( tests )

    if COV:
        COV.stop()
        COV.save()
        print('Суммарное покрытие:')
        COV.report()
        basedir = os.path.abspath( os.path.dirname(__name__) )
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report( directory = covdir )
        print('HTML версия: file://%s/index.html' % covdir)
        COV.erase()

if __name__ == '__main__':
    manager.run()