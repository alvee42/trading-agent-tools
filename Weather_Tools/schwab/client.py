"""
Schwab API client for market data (quotes and price history).

Provides methods to fetch real-time quotes and historical candle data.
"""

import logging
import time
from typing import Dict, List, Optional
import requests

from Weather_Tools.schwab.auth import SchwabAuthManager

logger = logging.getLogger(__name__)


class SchwabAPIClient:
    """Client for Schwab market data API endpoints."""

    def __init__(
        self,
        auth_manager: SchwabAuthManager,
        base_url: str = "https://api.schwabapi.com/marketdata/v1"
    ):
        """
        Initialize Schwab API client.

        Args:
            auth_manager: SchwabAuthManager instance for authentication
            base_url: Base URL for Schwab market data API
        """
        self.auth_manager = auth_manager
        self.base_url = base_url
        self.session = requests.Session()

        logger.debug(f"SchwabAPIClient initialized with base_url: {base_url}")

    def get_quote(self, symbol: str, fields: Optional[str] = None) -> Dict:
        """
        Get quote for a single symbol.

        Args:
            symbol: Symbol to look up (e.g., '/ESH25', 'AAPL')
            fields: Comma-separated list of fields to return (quote, reference, fundamental, extended, regular)
                   Default: all fields

        Returns:
            Dictionary containing quote data for the symbol

        Example response:
            {
              "/ESH25": {
                "assetMainType": "FUTURE",
                "symbol": "/ESH25",
                "quote": {
                  "bidPrice": 4500.25,
                  "askPrice": 4500.50,
                  "lastPrice": 4500.25,
                  "highPrice": 4510.00,
                  "lowPrice": 4490.00,
                  ...
                },
                ...
              }
            }
        """
        endpoint = f"/quotes/{symbol}"
        params = {}

        if fields:
            params['fields'] = fields

        logger.debug(f"Fetching quote for {symbol}")

        response_data = self._make_request('GET', endpoint, params=params)

        # Extract the symbol's data from response
        if symbol in response_data:
            return response_data[symbol]
        else:
            logger.warning(f"Symbol {symbol} not found in response")
            return response_data

    def get_quotes(self, symbols: List[str], fields: Optional[str] = None) -> Dict:
        """
        Get quotes for multiple symbols.

        Args:
            symbols: List of symbols to look up
            fields: Comma-separated list of fields to return

        Returns:
            Dictionary mapping symbols to their quote data
        """
        endpoint = "/quotes"
        params = {
            'symbols': ','.join(symbols)
        }

        if fields:
            params['fields'] = fields

        logger.debug(f"Fetching quotes for {len(symbols)} symbols")

        return self._make_request('GET', endpoint, params=params)

    def get_price_history(
        self,
        symbol: str,
        period_type: str = "day",
        period: int = 10,
        frequency_type: str = "minute",
        frequency: int = 5,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None,
        extended_hours: bool = True,
        need_previous_close: bool = False
    ) -> Dict:
        """
        Get historical price data (candles) for a symbol.

        Args:
            symbol: Symbol to get history for
            period_type: Chart period type (day, month, year, ytd)
            period: Number of periods
                - day: 1, 2, 3, 4, 5, 10
                - month: 1, 2, 3, 6
                - year: 1, 2, 3, 5, 10, 15, 20
                - ytd: 1
            frequency_type: Time frequency type (minute, daily, weekly, monthly)
            frequency: Frequency duration
                - minute: 1, 5, 10, 15, 30
                - daily: 1
                - weekly: 1
                - monthly: 1
            start_date: Start date in EPOCH milliseconds
            end_date: End date in EPOCH milliseconds
            extended_hours: Include extended hours data
            need_previous_close: Include previous close price/date

        Returns:
            Dictionary containing candles and metadata
            {
              "symbol": "/ESH25",
              "empty": false,
              "previousClose": 4500.00,
              "previousCloseDate": 1640000000000,
              "candles": [
                {
                  "open": 4500.25,
                  "high": 4501.00,
                  "low": 4499.50,
                  "close": 4500.75,
                  "volume": 1000,
                  "datetime": 1640001600000
                },
                ...
              ]
            }
        """
        endpoint = "/pricehistory"
        params = {
            'symbol': symbol,
            'periodType': period_type,
            'period': period,
            'frequencyType': frequency_type,
            'frequency': frequency,
            'needExtendedHoursData': str(extended_hours).lower(),
            'needPreviousClose': str(need_previous_close).lower()
        }

        if start_date:
            params['startDate'] = start_date

        if end_date:
            params['endDate'] = end_date

        logger.debug(
            f"Fetching price history for {symbol}: "
            f"{period_type}/{period}, {frequency_type}/{frequency}"
        )

        return self._make_request('GET', endpoint, params=params)

    def get_intraday_candles(
        self,
        symbol: str,
        frequency_minutes: int = 5,
        days_back: int = 10
    ) -> Dict:
        """
        Helper method to get recent intraday candles.

        Args:
            symbol: Symbol to get candles for
            frequency_minutes: Candle frequency in minutes (1, 5, 10, 15, 30)
            days_back: Number of days to fetch (max 10 for intraday)

        Returns:
            Dictionary containing candles data
        """
        return self.get_price_history(
            symbol=symbol,
            period_type="day",
            period=min(days_back, 10),  # Schwab API limits intraday data
            frequency_type="minute",
            frequency=frequency_minutes,
            extended_hours=True,
            need_previous_close=True
        )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Dict:
        """
        Make HTTP request to Schwab API with authentication and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/quotes')
            params: Query parameters
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed JSON response

        Raises:
            RuntimeError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(max_retries):
            try:
                # Get valid access token
                access_token = self.auth_manager.get_access_token()

                # Prepare headers
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Accept': 'application/json'
                }

                # Make request
                logger.debug(f"{method} {url} (attempt {attempt + 1}/{max_retries})")

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    timeout=30
                )

                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                # Handle unauthorized (401) - token may have expired
                if response.status_code == 401:
                    logger.warning("Received 401 Unauthorized. Token may have expired.")
                    # Force token refresh on next call
                    self.auth_manager.token_store.delete_tokens()
                    if attempt < max_retries - 1:
                        continue
                    else:
                        response.raise_for_status()

                # Raise for other HTTP errors
                response.raise_for_status()

                # Parse and return JSON
                return response.json()

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                if hasattr(e, 'response') and hasattr(e.response, 'text'):
                    logger.error(f"Response: {e.response.text}")

                if attempt == max_retries - 1:
                    raise RuntimeError(f"API request failed after {max_retries} attempts: {e}")

                # Exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")

                if attempt == max_retries - 1:
                    raise RuntimeError(f"API request failed: {e}")

                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

        raise RuntimeError(f"API request failed after {max_retries} attempts")
