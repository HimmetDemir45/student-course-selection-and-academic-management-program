import os

from app import create_app
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig

CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def create_app_from_env():
    env = os.getenv("FLASK_ENV", "development").lower()
    config_class = CONFIG_MAP.get(env, DevelopmentConfig)
    return create_app(config_class=config_class)


app = create_app_from_env()

if __name__ == "__main__":
    # debug değeri seçilen config üzerinden gelir
    app.run() 