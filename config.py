"""
Configuration management for Schwab Trading Agent Tools.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Base directory for the project
BASE_DIR = Path(__file__).parent


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # Schwab API credentials
    schwab_app_key: str
    schwab_app_secret: str
    schwab_redirect_uri: str = "https://localhost:8080"

    # Schwab API endpoints
    schwab_api_base_url: str = "https://api.schwabapi.com"
    schwab_auth_url: str = "https://api.schwabapi.com/v1/oauth/authorize"
    schwab_token_url: str = "https://api.schwabapi.com/v1/oauth/token"

    # Data storage paths
    data_dir: Path = BASE_DIR / "data"
    credentials_dir: Path = BASE_DIR / "data" / ".credentials"
    db_path: Path = BASE_DIR / "data" / "market_data.db"

    # Logging
    log_level: str = "INFO"
    log_file: Path = None

    def __post_init__(self):
        """Convert string paths to Path objects if needed."""
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        if isinstance(self.credentials_dir, str):
            self.credentials_dir = Path(self.credentials_dir)
        if isinstance(self.db_path, str):
            self.db_path = Path(self.db_path)
        if isinstance(self.log_file, str):
            self.log_file = Path(self.log_file)

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.credentials_dir.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    """
    Load configuration from environment variables.

    Returns:
        Config: Configuration object with all settings

    Raises:
        ValueError: If required environment variables are missing
    """
    # Required fields
    app_key = os.getenv("SCHWAB_APP_KEY")
    app_secret = os.getenv("SCHWAB_APP_SECRET")

    if not app_key or not app_secret:
        raise ValueError(
            "Missing required environment variables: SCHWAB_APP_KEY and SCHWAB_APP_SECRET. "
            "Please set them in your .env file or environment."
        )

    # Optional fields with defaults
    config = Config(
        schwab_app_key=app_key,
        schwab_app_secret=app_secret,
        schwab_redirect_uri=os.getenv("SCHWAB_REDIRECT_URI", "https://localhost:8080"),
        data_dir=os.getenv("DATA_DIR", str(BASE_DIR / "data")),
        credentials_dir=os.getenv("CREDENTIALS_DIR", str(BASE_DIR / "data" / ".credentials")),
        db_path=os.getenv("DB_PATH", str(BASE_DIR / "data" / "market_data.db")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE")
    )

    # Ensure directories exist
    config.ensure_directories()

    return config


def validate_config(config: Config):
    """
    Validate configuration object.

    Args:
        config: Configuration object to validate

    Raises:
        ValueError: If configuration is invalid
    """
    if not config.schwab_app_key or not config.schwab_app_secret:
        raise ValueError("Schwab API credentials are required")

    if not config.schwab_redirect_uri:
        raise ValueError("Schwab redirect URI is required")
