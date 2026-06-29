import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yaml

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(value):
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


def load_config():
    config = DEFAULTS.copy()

    # YAML layer
    env = os.getenv("APP_ENV", "development")
    yaml_file = Path(f"config.{env}.yaml")
    if yaml_file.exists():
        with open(yaml_file) as f:
            config.update(yaml.safe_load(f) or {})

    # .env / OS env layer
    mapping = {
        "APP_PORT": "port",
        "NUM_WORKERS": "workers",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, cfg_key in mapping.items():
        if env_key in os.environ:
            config[cfg_key] = coerce(cfg_key, os.environ[env_key])

    return config


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = load_config()

    # CLI overrides
    for item in set:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key in config:
            config[key] = coerce(key, value)

    config["api_key"] = "****"

    return config
