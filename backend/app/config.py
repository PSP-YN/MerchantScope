"""Central place for future environment-backed configuration."""
from os import environ

APP_ENV = environ.get("APP_ENV", "development")
