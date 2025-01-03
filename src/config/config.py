import os
import yaml
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
from flask.logging import default_handler
import logging
import sys

LOG_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

class Config:
    DEBUG = False
    TESTING = False
    API_TIMEOUT = 5
    LOG_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    CONFIG_FILE = os.getenv('CONFIG_FILE', 'config.yml')
    APIS_FILE = os.getenv('APIS_FILE', 'default_api_endpoints.txt')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    METRIC_PREFIX = os.getenv('METRIC_PREFIX', 'acos')

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    LOG_LEVEL = 'INFO'

def load_configuration(app, config_file, log_level_override=None):
    try:
        with open(config_file) as f:
            log_data = yaml.safe_load(f).get("log", {})
            log_output = log_data.get("log_output", "STDOUT")
            log_level = log_level_override if log_level_override else log_data.get("log_level", "INFO")
            log_filename = log_data.get("log_filename", None)
            logger = set_logger(log_output, log_level, log_filename)
            app.logger.removeHandler(default_handler)
            app.logger.addHandler(logger.handlers[0])
            logger.info("Starting exporter")
            return logger
    except Exception as e:
        print(f"Error loading configuration: {e}")
        raise

def set_logger(log_output="STDOUT", log_level="INFO", log_filename=None):

    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARN': logging.WARN,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }

    if log_level.upper() not in log_levels:
        print(f"{log_level.upper()} is an invalid log level, setting 'INFO' as default.")
        log_level = "INFO"

    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

    if log_output.upper() == "STDOUT":
        log_handler = StreamHandler(sys.stdout)
    elif log_output.upper() == "JOURNALD":
        try:
            from systemd.journal import JournalHandler
            log_handler = JournalHandler()
        except ImportError:
            print("systemd.journal not available, falling back to STDOUT")
            log_handler = StreamHandler(sys.stdout)
    elif log_output.upper() == "FILE":
        if not log_filename:
            log_filename = "app.log"
        log_handler = RotatingFileHandler(log_filename, maxBytes=LOG_FILE_SIZE, backupCount=2, encoding=None, delay=True)
    else:
        print(f"{log_output} is an invalid log output, setting 'STDOUT' as default.")
        log_handler = StreamHandler(sys.stdout)

    log_handler.setFormatter(log_formatter)
    log_handler.setLevel(log_levels[log_level.upper()])

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger('a10_prometheus_exporter_logger')
    logger.setLevel(log_levels[log_level.upper()])

    if not logger.handlers:
        print("INFO: Adding logger handler")
        logger.addHandler(log_handler)
    else:
        print("Logger handler already exists")

    return logger

def load_auth_config(config_file):
    with open(config_file) as f:
        return yaml.safe_load(f)["hosts"]
