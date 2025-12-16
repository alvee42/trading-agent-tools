"""
Futures contract utilities for ES and NQ.

Provides auto-detection of front month contracts with rollover logic.
"""

import logging
from datetime import datetime, date, timedelta, timezone
from typing import Tuple

logger = logging.getLogger(__name__)

# Futures month codes
FUTURES_MONTH_CODES = {
    1: "F",   # January
    2: "G",   # February
    3: "H",   # March
    4: "J",   # April
    5: "K",   # May
    6: "M",   # June
    7: "N",   # July
    8: "Q",   # August
    9: "U",   # September
    10: "V",  # October
    11: "X",  # November
    12: "Z"   # December
}

# ES and NQ trade quarterly contracts: March, June, September, December
QUARTERLY_MONTHS = [3, 6, 9, 12]

# Rollover days before expiration (3rd Friday of month)
ROLLOVER_DAYS_BEFORE_EXPIRATION = 10


class ContractResolver:
    """Utilities for resolving front month futures contracts."""

    @staticmethod
    def get_front_month_contract(
        product: str,
        as_of_date: Optional[datetime] = None
    ) -> str:
        """
        Get the front month contract symbol for ES or NQ futures.

        ES/NQ futures have quarterly expirations: March (H), June (M), September (U), December (Z).
        Contracts expire on the 3rd Friday of the expiration month.
        Volume typically rolls 10 days before expiration.

        Args:
            product: Futures product ('ES' or 'NQ')
            as_of_date: Date to calculate from (default: now)

        Returns:
            Front month contract symbol (e.g., '/ESH25' for March 2025)

        Examples:
            - Jan 15, 2025 → '/ESH25' (March 2025)
            - March 8, 2025 → '/ESM25' (already rolled to June, since March expiration is March 21)
            - June 25, 2025 → '/ESU25' (September 2025)
        """
        if as_of_date is None:
            as_of_date = datetime.now(timezone.utc)

        # Ensure we have a date object
        if isinstance(as_of_date, datetime):
            current_date = as_of_date.date()
        else:
            current_date = as_of_date

        # Get next quarterly expiration
        exp_month, exp_year = ContractResolver._get_next_quarterly_expiration(current_date)

        # Calculate expiration date (3rd Friday)
        expiration_date = ContractResolver._get_third_friday(exp_year, exp_month)

        # Check if we should roll early (within 10 days of expiration)
        if ContractResolver._should_roll_early(current_date, expiration_date):
            logger.debug(
                f"Within rollover window for {FUTURES_MONTH_CODES[exp_month]}{exp_year % 100}. "
                f"Rolling to next contract."
            )
            # Move to next quarterly month
            exp_month, exp_year = ContractResolver._get_next_quarterly_month(exp_month, exp_year)

        # Format symbol: /{PRODUCT}{MONTH_CODE}{YEAR_2DIGIT}
        month_code = FUTURES_MONTH_CODES[exp_month]
        year_code = str(exp_year)[-2:]
        symbol = f"/{product.upper()}{month_code}{year_code}"

        logger.info(f"Front month contract for {product}: {symbol}")

        return symbol

    @staticmethod
    def _get_next_quarterly_expiration(current_date: date) -> Tuple[int, int]:
        """
        Get the next quarterly expiration month and year.

        Args:
            current_date: Current date

        Returns:
            Tuple of (month, year)
        """
        current_month = current_date.month
        current_year = current_date.year

        # Find next quarterly month from current month
        next_quarterly = None
        for month in QUARTERLY_MONTHS:
            if month >= current_month:
                next_quarterly = month
                break

        if next_quarterly is None:
            # Wrap to next year
            next_quarterly = QUARTERLY_MONTHS[0]
            current_year += 1

        return next_quarterly, current_year

    @staticmethod
    def _get_next_quarterly_month(month: int, year: int) -> Tuple[int, int]:
        """
        Get the next quarterly month after the given month.

        Args:
            month: Current month
            year: Current year

        Returns:
            Tuple of (next_month, next_year)
        """
        try:
            idx = QUARTERLY_MONTHS.index(month)
            if idx == len(QUARTERLY_MONTHS) - 1:
                # December, wrap to March next year
                return QUARTERLY_MONTHS[0], year + 1
            else:
                return QUARTERLY_MONTHS[idx + 1], year
        except ValueError:
            # Month is not quarterly, find next quarterly
            for quarterly_month in QUARTERLY_MONTHS:
                if quarterly_month > month:
                    return quarterly_month, year
            # Wrap to next year
            return QUARTERLY_MONTHS[0], year + 1

    @staticmethod
    def _get_third_friday(year: int, month: int) -> date:
        """
        Calculate the 3rd Friday of a given month/year.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            Date of the 3rd Friday
        """
        # First day of month
        first_day = date(year, month, 1)

        # Find first Friday (Friday is weekday 4)
        days_until_friday = (4 - first_day.weekday()) % 7
        first_friday = first_day + timedelta(days=days_until_friday)

        # Third Friday is 14 days after first Friday
        third_friday = first_friday + timedelta(days=14)

        return third_friday

    @staticmethod
    def _should_roll_early(current_date: date, expiration_date: date) -> bool:
        """
        Determine if we're in the rollover window.

        Most traders roll contracts 8-10 days before expiration to avoid low liquidity.

        Args:
            current_date: Current date
            expiration_date: Contract expiration date (3rd Friday)

        Returns:
            True if within rollover window, False otherwise
        """
        days_until_expiration = (expiration_date - current_date).days

        if days_until_expiration <= ROLLOVER_DAYS_BEFORE_EXPIRATION:
            logger.debug(
                f"{days_until_expiration} days until expiration "
                f"(threshold: {ROLLOVER_DAYS_BEFORE_EXPIRATION})"
            )
            return True

        return False

    @staticmethod
    def get_contract_expiration(symbol: str) -> Optional[date]:
        """
        Parse contract symbol and return expiration date.

        Args:
            symbol: Contract symbol (e.g., '/ESH25')

        Returns:
            Expiration date (3rd Friday of contract month), or None if invalid
        """
        try:
            # Parse symbol: /{PRODUCT}{MONTH_CODE}{YEAR_2DIGIT}
            # Example: /ESH25 → product=ES, month_code=H, year=25

            if not symbol.startswith('/'):
                logger.warning(f"Invalid symbol format: {symbol}")
                return None

            # Remove leading slash
            symbol_no_slash = symbol[1:]

            # Extract month code (last 3 chars: month code + 2-digit year)
            if len(symbol_no_slash) < 3:
                logger.warning(f"Symbol too short: {symbol}")
                return None

            month_code = symbol_no_slash[-3]
            year_2digit = symbol_no_slash[-2:]

            # Find month number from code
            month = None
            for m, code in FUTURES_MONTH_CODES.items():
                if code == month_code:
                    month = m
                    break

            if month is None:
                logger.warning(f"Invalid month code: {month_code}")
                return None

            # Convert 2-digit year to 4-digit (assume 20XX)
            year = 2000 + int(year_2digit)

            # Get 3rd Friday
            expiration = ContractResolver._get_third_friday(year, month)

            return expiration

        except Exception as e:
            logger.error(f"Failed to parse contract symbol {symbol}: {e}")
            return None
