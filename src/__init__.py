from flask import Flask
from config import config, load_configuration
import os

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])  # Load configuration settings

    # Override configuration with environment variables if set
    app.config['LOG_LEVEL'] = os.getenv('LOG_LEVEL', app.config['LOG_LEVEL'])
    app.config['CONFIG_FILE'] = os.getenv('CONFIG_FILE', app.config['CONFIG_FILE'])
    app.config['METRIC_PREFIX'] = os.getenv('METRIC_PREFIX', "")

    with app.app_context():
        from .views.metrics import metrics_bp
        app.register_blueprint(metrics_bp)

        # Load configuration using the CONFIG_FILE environment variable
        logger = load_configuration(app, app.config['CONFIG_FILE'], app.config['LOG_LEVEL'])
        app.logger = logger

    return app
