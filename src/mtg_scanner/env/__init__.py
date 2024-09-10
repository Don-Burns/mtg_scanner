"""
Some small utils for handling environment variables
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger("env")


def export_dot_env(dot_env_path: Path = Path("./.env")) -> None:
    """
    Export the .env file to the environment variables
    """
    logger.info("Exporting .env file to environment variables")
    with open(dot_env_path, "r", encoding="utf-8") as file:
        for line in file:
            # max split in case the value contains an equals sign
            # e.g. KEY=VALUE=VALUE
            key, value = line.strip().split("=", maxsplit=1)
            os.environ[key] = value


def get_db_url() -> str:
    """
    Get the database URL from the environment
    """
    return os.environ["DB_URL"]
