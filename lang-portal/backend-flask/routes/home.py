from flask import jsonify

def load(app):
    @app.route("/")
    def index():
        return jsonify({
            "status": "operational",
            "version": "1.0.0",
            "endpoints": [
                "/words",
                "/groups",
                "/study-sessions",
                "/dashboard"
            ]
        })
