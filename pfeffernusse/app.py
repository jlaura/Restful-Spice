from flask import Flask

from pfeffernusse.config import Config
from pfeffernusse.models import db
from pfeffernusse.utils import CustomJSONEncoder
from pfeffernusse.views import api


def create_app():
    # Create the app
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register the blueprint URLs
    app.register_blueprint(api, url_prefix='/api')

    # Initialize the app
    db.init_app(app)

    # Patch in the standard response and custom reponse encoder
    app.response_failure = {'success':False, 'error_msg':""}
    app.json_encoder = CustomJSONEncoder
    return app
