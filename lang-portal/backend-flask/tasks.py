# from invoke import task
# from lib.db import db

# @task
# def init_db(c):
#   from flask import Flask
#   app = Flask(__name__)
#   db.init(app)
#   print("Database initialized successfully.")

from flask.cli import FlaskGroup
from lib.db import db

def create_app():
    from backend_flask import app
    return app

cli = FlaskGroup(create_app=create_app)

@cli.command('init-db')
def init_db():
    """Initialize the database"""
    with current_app.app_context():
        db.init_db_command()
