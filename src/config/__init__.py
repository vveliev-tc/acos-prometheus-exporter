from .config import DevelopmentConfig, ProductionConfig, load_configuration, load_auth_config

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}
