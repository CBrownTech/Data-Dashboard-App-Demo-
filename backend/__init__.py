# Application factory — creates and configures the Flask app.
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    CORS(app, origins="*", supports_credentials=False)

    from nonprofit_routes import bp, nonprofit_bp
    app.register_blueprint(bp, url_prefix="/api")
    app.register_blueprint(nonprofit_bp, url_prefix="/api")

    return app
