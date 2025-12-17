"""
Session phase detection for ES/NQ futures trading hours.

ES/NQ trade nearly 24 hours, but different session phases have different characteristics.
"""

import logging
from datetime import datetime, time
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Central Time (Chicago) - ES/NQ primary trading location
CENTRAL = ZoneInfo("America/Chicago")

# Session phases for ES/NQ (Central Time)
SESSION_PHASES = {
    "pre_open": (time(5, 0), time(8, 30)),
    "opening_range": (time(8, 30), time(9, 0)),
    "mid_morning": (time(9, 0), time(11, 30)),
    "lunch": (time(11, 30), time(13, 0)),
    "mid_afternoon": (time(13, 0), time(15, 0)),
    "power_hour": (time(15, 0), time(16, 0)),
    "close": (time(16, 0), time(17, 0)),
    # extended: all other times (overnight session)
}


def get_session_phase(dt: Optional[datetime] = None) -> str:
    """
    Get the current session phase for ES/NQ futures.

    Args:
        dt: Datetime to check (default: now). Assumed to be timezone-aware.
            If timezone-naive, assumed to be UTC.

    Returns:
        Session phase name:
        - pre_open: 05:00 - 08:30 CT
        - opening_range: 08:30 - 09:00 CT (first 30 minutes)
        - mid_morning: 09:00 - 11:30 CT
        - lunch: 11:30 - 13:00 CT
        - mid_afternoon: 13:00 - 15:00 CT
        - power_hour: 15:00 - 16:00 CT (last hour of regular session)
        - close: 16:00 - 17:00 CT
        - extended: All other times (overnight session)
    """
    if dt is None:
        dt = datetime.now(CENTRAL)
    else:
        # Convert to Central Time
        if dt.tzinfo is None:
            # Assume UTC if no timezone
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        dt = dt.astimezone(CENTRAL)

    current_time = dt.time()

    # Check each session phase
    for phase, (start, end) in SESSION_PHASES.items():
        if start <= current_time < end:
            logger.debug(f"Session phase: {phase} (CT time: {current_time})")
            return phase

    # Outside regular session = extended hours
    logger.debug(f"Session phase: extended (CT time: {current_time})")
    return "extended"


def minutes_since_session_open(dt: Optional[datetime] = None) -> int:
    """
    Calculate minutes since regular session open (08:30 CT).

    Args:
        dt: Datetime to check (default: now)

    Returns:
        Minutes since 08:30 CT. Returns 0 if before session open.
    """
    if dt is None:
        dt = datetime.now(CENTRAL)
    else:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        dt = dt.astimezone(CENTRAL)

    # Session opens at 08:30 CT
    open_time = dt.replace(hour=8, minute=30, second=0, microsecond=0)

    if dt < open_time:
        return 0

    minutes = int((dt - open_time).total_seconds() / 60)

    return minutes


def is_regular_session(dt: Optional[datetime] = None) -> bool:
    """
    Check if the given time is during regular trading hours (08:30 - 17:00 CT).

    Args:
        dt: Datetime to check (default: now)

    Returns:
        True if during regular session, False if extended hours
    """
    phase = get_session_phase(dt)
    return phase != "extended"


def get_session_open_time(dt: Optional[datetime] = None) -> datetime:
    """
    Get the session open datetime for the given date.

    Args:
        dt: Date to get session open for (default: today)

    Returns:
        Datetime of session open (08:30 CT)
    """
    if dt is None:
        dt = datetime.now(CENTRAL)
    else:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        dt = dt.astimezone(CENTRAL)

    return dt.replace(hour=8, minute=30, second=0, microsecond=0)


def get_session_close_time(dt: Optional[datetime] = None) -> datetime:
    """
    Get the session close datetime for the given date.

    Args:
        dt: Date to get session close for (default: today)

    Returns:
        Datetime of session close (17:00 CT)
    """
    if dt is None:
        dt = datetime.now(CENTRAL)
    else:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        dt = dt.astimezone(CENTRAL)

    return dt.replace(hour=17, minute=0, second=0, microsecond=0)
