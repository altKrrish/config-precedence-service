import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default configuration
DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(value):
    return str(value).strip().lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


def load_config():
    config = DEFAULTS.copy()

    # 1. YAML layer
    env = os.getenv("APP_ENV", "development")
    yaml_file = Path(f"config.{env}.yaml")
    if yaml_file.exists():
        with open(yaml_file, "r") as f:
            yaml_data = yaml.safe_load(f) or {}
            for k, v in yaml_data.items():
                config[k] = coerce(k, v)

    # 2. .env layer
    dotenv = dotenv_values(".env")

    env_mapping = {
        "APP_PORT": "port",
        "NUM_WORKERS": "workers",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, cfg_key in env_mapping.items():
        if env_key in dotenv and dotenv[env_key] is not None:
            config[cfg_key] = coerce(cfg_key, dotenv[env_key])

    # 3. OS environment layer (highest before CLI)
    for env_key, cfg_key in env_mapping.items():
        if env_key in os.environ:
            config[cfg_key] = coerce(cfg_key, os.environ[env_key])

    return config


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = load_config()

    # 4. CLI/query overrides (highest precedence)
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key in config:
            config[key] = coerce(key, value)

    # Always mask the secret
    config["api_key"] = "****"

    return config
