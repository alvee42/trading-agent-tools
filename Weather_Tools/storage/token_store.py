"""
Secure token storage using Windows DPAPI (Data Protection API).

Tokens are encrypted using the current Windows user's credentials,
ensuring they can only be decrypted by the same user on the same machine.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta

try:
    import win32crypt
    DPAPI_AVAILABLE = True
except ImportError:
    DPAPI_AVAILABLE = False
    logging.warning("pywin32 not available. Token encryption will be disabled.")


logger = logging.getLogger(__name__)


class TokenStore:
    """Secure token storage using Windows DPAPI encryption."""

    def __init__(self, credentials_dir: Path):
        """
        Initialize token store.

        Args:
            credentials_dir: Directory to store encrypted token file

        Raises:
            RuntimeError: If DPAPI is not available (Windows required)
        """
        if not DPAPI_AVAILABLE:
            raise RuntimeError(
                "Windows DPAPI is required for secure token storage. "
                "Please install pywin32: pip install pywin32"
            )

        self.credentials_dir = Path(credentials_dir)
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self.token_file = self.credentials_dir / "schwab_tokens.dat"

        logger.debug(f"TokenStore initialized with path: {self.token_file}")

    def save_tokens(self, token_data: Dict[str, any]):
        """
        Encrypt and save tokens to disk using Windows DPAPI.

        Args:
            token_data: Dictionary containing token information
                Expected keys: access_token, refresh_token, expires_in, token_type, scope

        The tokens will include an 'expires_at' timestamp calculated from 'expires_in'.
        """
        # Add expiration timestamp if not present
        if 'expires_at' not in token_data and 'expires_in' in token_data:
            expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
            token_data['expires_at'] = expires_at.isoformat()

        # Convert to JSON
        json_data = json.dumps(token_data, indent=2).encode('utf-8')

        try:
            # Encrypt using DPAPI
            encrypted_data = win32crypt.CryptProtectData(
                json_data,
                "Schwab API Tokens",  # Description
                None,  # Optional entropy (None for user-based encryption)
                None,  # Reserved
                None,  # Prompt struct
                0      # Flags
            )

            # Write encrypted data to file
            self.token_file.write_bytes(encrypted_data)
            logger.info(f"Tokens encrypted and saved to {self.token_file}")

        except Exception as e:
            logger.error(f"Failed to encrypt and save tokens: {e}")
            raise

    def load_tokens(self) -> Optional[Dict[str, any]]:
        """
        Load and decrypt tokens from disk using Windows DPAPI.

        Returns:
            Dictionary containing token data, or None if no tokens exist or decryption fails

        The returned dictionary includes:
            - access_token: OAuth access token
            - refresh_token: OAuth refresh token
            - expires_in: Seconds until expiration
            - token_type: Token type (usually "Bearer")
            - scope: OAuth scopes
            - expires_at: ISO 8601 timestamp of expiration
        """
        if not self.token_file.exists():
            logger.debug("No token file found")
            return None

        try:
            # Read encrypted data
            encrypted_data = self.token_file.read_bytes()

            # Decrypt using DPAPI
            decrypted_data = win32crypt.CryptUnprotectData(
                encrypted_data,
                None,  # Optional entropy
                None,  # Reserved
                None,  # Prompt struct
                0      # Flags
            )

            # Parse JSON (decrypted_data is a tuple: (description, data))
            json_str = decrypted_data[1].decode('utf-8')
            token_data = json.loads(json_str)

            logger.debug("Tokens successfully decrypted and loaded")
            return token_data

        except Exception as e:
            logger.error(f"Failed to decrypt tokens: {e}")
            logger.warning("Tokens may be corrupted or from a different user/machine")
            return None

    def delete_tokens(self):
        """
        Securely delete token file.

        This removes the encrypted token file from disk.
        """
        if self.token_file.exists():
            try:
                self.token_file.unlink()
                logger.info(f"Token file deleted: {self.token_file}")
            except Exception as e:
                logger.error(f"Failed to delete token file: {e}")
                raise
        else:
            logger.debug("No token file to delete")

    def is_token_valid(self, token_data: Optional[Dict[str, any]] = None) -> bool:
        """
        Check if the stored token is still valid (not expired).

        Args:
            token_data: Token data dictionary. If None, will load from disk.

        Returns:
            True if token exists and is not expired, False otherwise
        """
        if token_data is None:
            token_data = self.load_tokens()

        if not token_data:
            return False

        # Check if expires_at exists
        if 'expires_at' not in token_data:
            logger.warning("Token data missing 'expires_at' field")
            return False

        try:
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            # Add 60 second buffer to avoid using token right at expiration
            is_valid = datetime.now() < (expires_at - timedelta(seconds=60))

            if is_valid:
                logger.debug(f"Token is valid until {expires_at}")
            else:
                logger.debug(f"Token expired at {expires_at}")

            return is_valid

        except Exception as e:
            logger.error(f"Failed to parse token expiration: {e}")
            return False

    def get_valid_token(self) -> Optional[Dict[str, any]]:
        """
        Load tokens and verify they are still valid.

        Returns:
            Token data if valid, None otherwise
        """
        token_data = self.load_tokens()

        if token_data and self.is_token_valid(token_data):
            return token_data

        return None
