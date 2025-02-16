from flask import Flask, g
from flask_cors import CORS
from lib.db import db
import routes.words
import routes.groups
import routes.study_sessions
import routes.dashboard
import routes.study_activities

def get_allowed_origins():
    """Get CORS origins from database using proper app context"""
    with db.get() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT url FROM study_activities')
            urls = cursor.fetchall()
            origins = set()
            for url in urls:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url['url'])
                    origins.add(f"{parsed.scheme}://{parsed.netloc}")
                except:
                    continue
            return list(origins) if origins else ["*"]
        except:
            return ["*"]

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=app.instance_path / 'flaskr.sqlite',
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.cli.add_command(db.init_db_command)

    # Configure CORS with context-aware origins
    @app.before_request
    def configure_cors():
        allowed_origins = get_allowed_origins()
        if app.debug:
            allowed_origins.extend(["http://localhost:8080", "http://127.0.0.1:8080"])
        
        CORS(app, resources={
            r"/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })

    # Register routes
    routes.words.load(app)
    routes.groups.load(app)
    routes.study_sessions.load(app)
    routes.dashboard.load(app)
    routes.study_activities.load(app)

    return app

# Application instance is created when this file is run directly
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
