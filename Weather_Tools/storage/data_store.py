"""
SQLite database for persistent storage of market data and regime snapshots.

Stores:
- Historical candle data (OHLCV)
- Regime classification snapshots
- Optional event calendar
"""

import sqlite3
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketDataStore:
    """SQLite persistence for market data and regime classifications."""

    def __init__(self, db_path: Path):
        """
        Initialize market data store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema
        self._init_schema()

        logger.info(f"MarketDataStore initialized at {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.Connection(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn

    def _init_schema(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Candles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    datetime INTEGER NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, datetime)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_candles_symbol_datetime
                ON candles(symbol, datetime DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_candles_created
                ON candles(symbol, created_at DESC)
            """)

            # Regime snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regime_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    primary_regime TEXT NOT NULL,
                    secondary_tag TEXT,
                    confidence INTEGER NOT NULL,
                    volatility_state TEXT NOT NULL,
                    participation_state TEXT NOT NULL,
                    balance_state TEXT NOT NULL,
                    trend_quality TEXT NOT NULL,
                    noise_level TEXT NOT NULL,
                    session_phase TEXT NOT NULL,
                    order_flow_reliability_note TEXT,
                    raw_features TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_regime_instrument_timestamp
                ON regime_snapshots(instrument, timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_regime_created
                ON regime_snapshots(created_at DESC)
            """)

            # Optional: Event calendar table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_date TEXT NOT NULL,
                    event_time TEXT,
                    event_name TEXT NOT NULL,
                    impact_level TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_date
                ON scheduled_events(event_date)
            """)

            conn.commit()

            logger.debug("Database schema initialized")

    def insert_candles(self, symbol: str, candles: List[Dict]):
        """
        Batch insert candles into database.

        Uses INSERT OR IGNORE to prevent duplicate entries.

        Args:
            symbol: Symbol for the candles
            candles: List of candle dictionaries with keys:
                     open, high, low, close, volume, datetime (EPOCH ms)
        """
        if not candles:
            logger.debug(f"No candles to insert for {symbol}")
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Prepare data for batch insert
            candle_data = [
                (
                    symbol,
                    candle['datetime'],
                    candle['open'],
                    candle['high'],
                    candle['low'],
                    candle['close'],
                    candle['volume']
                )
                for candle in candles
            ]

            # Insert or ignore (prevents duplicates)
            cursor.executemany("""
                INSERT OR IGNORE INTO candles
                (symbol, datetime, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, candle_data)

            conn.commit()

            logger.info(f"Inserted {cursor.rowcount} candles for {symbol}")

    def get_recent_candles(
        self,
        symbol: str,
        lookback_minutes: int = 1440,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch recent candles for a symbol.

        Args:
            symbol: Symbol to fetch
            lookback_minutes: How far back to look (in minutes from now)
            limit: Maximum number of candles to return

        Returns:
            List of candle dictionaries, sorted by datetime ascending
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Calculate lookback timestamp (EPOCH milliseconds)
            lookback_ms = int(datetime.now().timestamp() * 1000) - (lookback_minutes * 60 * 1000)

            query = """
                SELECT datetime, open, high, low, close, volume
                FROM candles
                WHERE symbol = ? AND datetime >= ?
                ORDER BY datetime ASC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (symbol, lookback_ms))

            rows = cursor.fetchall()

            # Convert to list of dictionaries
            candles = [
                {
                    'datetime': row['datetime'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                }
                for row in rows
            ]

            logger.debug(f"Fetched {len(candles)} candles for {symbol}")

            return candles

    def insert_regime_snapshot(self, regime_data: Dict):
        """
        Store a regime classification snapshot.

        Args:
            regime_data: Dictionary containing regime output fields:
                - instrument: 'ES' or 'NQ'
                - timestamp: ISO 8601 timestamp
                - primary_regime: Regime classification
                - secondary_tag: Optional subtype
                - confidence: 0-100
                - volatility_state: Volatility classification
                - participation_state: Participation classification
                - balance_state: Balance classification
                - trend_quality: Trend quality
                - noise_level: Noise level
                - session_phase: Session phase
                - order_flow_reliability_note: Human-readable note
                - raw_features: (Optional) JSON string of calculated features
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Convert raw_features to JSON string if it's a dict
            raw_features = regime_data.get('raw_features')
            if raw_features and isinstance(raw_features, dict):
                raw_features = json.dumps(raw_features)

            cursor.execute("""
                INSERT INTO regime_snapshots (
                    instrument, timestamp, primary_regime, secondary_tag,
                    confidence, volatility_state, participation_state,
                    balance_state, trend_quality, noise_level,
                    session_phase, order_flow_reliability_note, raw_features
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                regime_data['instrument'],
                regime_data['timestamp'],
                regime_data['primary_regime'],
                regime_data.get('secondary_tag'),
                regime_data['confidence'],
                regime_data['volatility_state'],
                regime_data['participation_state'],
                regime_data['balance_state'],
                regime_data['trend_quality'],
                regime_data['noise_level'],
                regime_data['session_phase'],
                regime_data['order_flow_reliability_note'],
                raw_features
            ))

            conn.commit()

            logger.info(
                f"Saved regime snapshot: {regime_data['instrument']} - "
                f"{regime_data['primary_regime']} (confidence: {regime_data['confidence']})"
            )

    def get_regime_history(
        self,
        instrument: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query historical regime classifications.

        Args:
            instrument: 'ES' or 'NQ'
            start_time: ISO 8601 timestamp (inclusive)
            end_time: ISO 8601 timestamp (inclusive)
            limit: Maximum number of records to return

        Returns:
            List of regime snapshot dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT *
                FROM regime_snapshots
                WHERE instrument = ?
            """
            params = [instrument]

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            rows = cursor.fetchall()

            # Convert to list of dictionaries
            snapshots = [dict(row) for row in rows]

            logger.debug(f"Fetched {len(snapshots)} regime snapshots for {instrument}")

            return snapshots

    def cleanup_old_data(self, days_to_keep: int = 30):
        """
        Delete old candle data to manage database size.

        Args:
            days_to_keep: Number of days of data to retain
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cutoff_date = datetime.now().isoformat()

            # Delete old candles
            cursor.execute("""
                DELETE FROM candles
                WHERE created_at < datetime('now', ?)
            """, (f'-{days_to_keep} days',))

            candles_deleted = cursor.rowcount

            # Delete old regime snapshots (keep longer)
            cursor.execute("""
                DELETE FROM regime_snapshots
                WHERE created_at < datetime('now', ?)
            """, (f'-{days_to_keep * 3} days',))

            snapshots_deleted = cursor.rowcount

            conn.commit()

            logger.info(
                f"Cleanup complete: deleted {candles_deleted} candles, "
                f"{snapshots_deleted} regime snapshots"
            )

    def get_database_stats(self) -> Dict:
        """
        Get database statistics.

        Returns:
            Dictionary with row counts and size information
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Count candles
            cursor.execute("SELECT COUNT(*) as count FROM candles")
            stats['candles_count'] = cursor.fetchone()['count']

            # Count regime snapshots
            cursor.execute("SELECT COUNT(*) as count FROM regime_snapshots")
            stats['regime_snapshots_count'] = cursor.fetchone()['count']

            # Database file size
            stats['db_size_bytes'] = self.db_path.stat().st_size if self.db_path.exists() else 0
            stats['db_size_mb'] = round(stats['db_size_bytes'] / (1024 * 1024), 2)

            return stats
