"""
OAuth 2.0 authentication for Schwab API.

Implements the authorization code flow with automatic token refresh.
"""

import logging
import webbrowser
import urllib.parse
from typing import Dict, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
from pathlib import Path

from Weather_Tools.storage.token_store import TokenStore

logger = logging.getLogger(__name__)


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler to capture OAuth callback."""

    auth_code = None

    def do_GET(self):
        """Handle GET request from OAuth redirect."""
        # Parse query parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if 'code' in params:
            CallbackHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorization Failed</h1></body></html>")

    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass


class SchwabAuthManager:
    """Manages OAuth 2.0 authentication with Schwab API."""

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        redirect_uri: str,
        token_store: TokenStore,
        auth_url: str = "https://api.schwabapi.com/v1/oauth/authorize",
        token_url: str = "https://api.schwabapi.com/v1/oauth/token"
    ):
        """
        Initialize Schwab Auth Manager.

        Args:
            app_key: Schwab API App Key (Client ID)
            app_secret: Schwab API App Secret
            redirect_uri: OAuth redirect URI (e.g., https://localhost:8080)
            token_store: TokenStore instance for secure token storage
            auth_url: Schwab authorization endpoint
            token_url: Schwab token endpoint
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.token_store = token_store
        self.auth_url = auth_url
        self.token_url = token_url

        logger.debug(f"SchwabAuthManager initialized with redirect_uri: {redirect_uri}")

    def get_access_token(self) -> str:
        """
        Get a valid access token.

        Returns cached token if valid, refreshes if expired, or initiates OAuth flow if no tokens exist.

        Returns:
            Valid access token string

        Raises:
            RuntimeError: If authentication fails
        """
        # Check for cached valid token
        token_data = self.token_store.get_valid_token()

        if token_data:
            logger.debug("Using cached access token")
            return token_data['access_token']

        # Try to refresh token if available
        token_data = self.token_store.load_tokens()
        if token_data and 'refresh_token' in token_data:
            logger.info("Access token expired, attempting refresh")
            try:
                new_tokens = self.refresh_access_token(token_data['refresh_token'])
                return new_tokens['access_token']
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
                # Fall through to OAuth flow

        # No valid tokens, initiate OAuth flow
        logger.info("No valid tokens found, initiating OAuth flow")
        return self.initiate_oauth_flow()

    def initiate_oauth_flow(self) -> str:
        """
        Initiate interactive OAuth 2.0 authorization code flow.

        This method:
        1. Generates the authorization URL
        2. Opens the user's browser
        3. Starts a local HTTP server to capture the callback
        4. Exchanges the authorization code for tokens
        5. Saves tokens securely

        Returns:
            Access token string

        Raises:
            RuntimeError: If OAuth flow fails
        """
        # Generate authorization URL
        auth_params = {
            'response_type': 'code',
            'client_id': self.app_key,
            'redirect_uri': self.redirect_uri,
            'scope': 'readonly'  # Schwab API scope for market data
        }

        auth_url_full = f"{self.auth_url}?{urllib.parse.urlencode(auth_params)}"

        logger.info("Opening browser for authorization...")
        print("\n" + "="*70)
        print("SCHWAB API AUTHORIZATION REQUIRED")
        print("="*70)
        print(f"\nOpening browser to: {auth_url_full}")
        print("\nIf the browser doesn't open automatically, copy and paste the URL above.")
        print("After authorizing, you'll be redirected to localhost (this is expected).")
        print("="*70 + "\n")

        # Open browser
        webbrowser.open(auth_url_full)

        # Start local HTTP server to capture callback
        server = None
        try:
            # Parse redirect URI to get port
            parsed_uri = urllib.parse.urlparse(self.redirect_uri)
            port = parsed_uri.port or 8080

            server = HTTPServer(('localhost', port), CallbackHandler)
            logger.info(f"Waiting for OAuth callback on port {port}...")

            # Handle one request (the callback)
            server.handle_request()

            if not CallbackHandler.auth_code:
                raise RuntimeError("Failed to capture authorization code from callback")

            logger.info("Authorization code received")

            # Exchange code for tokens
            tokens = self.exchange_code_for_token(CallbackHandler.auth_code)

            # Save tokens securely
            self.token_store.save_tokens(tokens)

            print("\n" + "="*70)
            print("AUTHORIZATION SUCCESSFUL!")
            print("="*70)
            print("Tokens have been encrypted and saved securely.")
            print("You won't need to authorize again unless tokens are revoked.")
            print("="*70 + "\n")

            return tokens['access_token']

        except Exception as e:
            logger.error(f"OAuth flow failed: {e}")
            raise RuntimeError(f"OAuth authentication failed: {e}")

        finally:
            if server:
                server.server_close()

    def exchange_code_for_token(self, auth_code: str) -> Dict[str, any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            auth_code: Authorization code from OAuth callback

        Returns:
            Dictionary containing tokens and metadata

        Raises:
            RuntimeError: If token exchange fails
        """
        token_params = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.redirect_uri
        }

        try:
            logger.debug("Exchanging authorization code for tokens")

            response = requests.post(
                self.token_url,
                data=token_params,
                auth=(self.app_key, self.app_secret),
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            response.raise_for_status()

            token_data = response.json()

            logger.info("Successfully obtained access and refresh tokens")

            return token_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Token exchange failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise RuntimeError(f"Failed to exchange authorization code: {e}")

    def refresh_access_token(self, refresh_token: str) -> Dict[str, any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token from previous authentication

        Returns:
            Dictionary containing new tokens

        Raises:
            RuntimeError: If token refresh fails
        """
        refresh_params = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }

        try:
            logger.debug("Refreshing access token")

            response = requests.post(
                self.token_url,
                data=refresh_params,
                auth=(self.app_key, self.app_secret),
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            response.raise_for_status()

            token_data = response.json()

            # Save new tokens
            self.token_store.save_tokens(token_data)

            logger.info("Successfully refreshed access token")

            return token_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Token refresh failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise RuntimeError(f"Failed to refresh token: {e}")
