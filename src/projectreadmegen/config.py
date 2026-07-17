# src/projectreadmegen/config.py
#
# Configuration loading and validation.
#
# For backwards compatibility, all constants from constants.py are re-exported
# here so existing ``from projectreadmegen.config import SKIP_DIRS`` continues
# to work.  New code should import from constants.py directly.

import json
import logging
from pathlib import Path

from projectreadmegen.constants import *  # noqa: F401, F403  — re-export
from projectreadmegen.constants import DEFAULT_CONFIG, VALID_CONFIG_KEYS

logger = logging.getLogger(__name__)


def load_config(root_path: str) -> dict:
    """
    Load readmegen.config.json from the project root if it exists,
    otherwise return DEFAULT_CONFIG.

    Parameters:
        root_path (str): Path to the project root.

    Returns:
        dict: Merged configuration (user config overrides defaults).

    Raises:
        ConfigurationError: If the config file exists but is malformed.
    """
    from projectreadmegen.exceptions import ConfigurationError

    config_path = Path(root_path) / "readmegen.config.json"
    config = DEFAULT_CONFIG.copy()

    if config_path.exists():
        logger.debug(f"Loading config from {config_path}")
        try:
            # Verify readable
            if not config_path.is_file():
                logger.warning(f"Config path is not a file: {config_path}")
                return config

            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)

            # Validate config is dict
            if not isinstance(user_config, dict):
                raise ConfigurationError(
                    f"Invalid config format: expected dict, got {type(user_config).__name__}",
                    "Configuration file must be a valid JSON object.",
                )

            # Validate and merge — only known keys are accepted
            for key, value in user_config.items():
                if key in config:
                    config[key] = value
                else:
                    logger.warning(f"Unknown config key in readmegen.config.json: {key}")

            logger.debug(f"Loaded user config: {config}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {config_path}: {e}")
            raise ConfigurationError(
                f"Invalid JSON in {config_path}: {e}",
                "The readmegen.config.json file contains invalid JSON. Please fix the syntax.",
            )
        except (IOError, OSError) as e:
            logger.error(f"Cannot read config file {config_path}: {e}")
            raise ConfigurationError(
                f"Cannot read config file {config_path}: {e}",
                f"Unable to read configuration file: {e}",
            )
        except ConfigurationError:
            raise
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            raise ConfigurationError(
                f"Error loading config from {config_path}: {e}",
                f"An error occurred while loading configuration: {e}",
            )

    return config
