"""
Weather/Market Regime Agent - Main CLI Entry Point

Single-shot execution mode for classifying ES/NQ futures market regimes.

Usage:
    python weather_tools.py --symbol ES
    python weather_tools.py --symbol NQ --output pretty
    python weather_tools.py --symbol ES --debug
"""

import argparse
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config, validate_config
from Weather_Tools.storage.token_store import TokenStore
from Weather_Tools.storage.data_store import MarketDataStore
from Weather_Tools.schwab.auth import SchwabAuthManager
from Weather_Tools.schwab.client import SchwabAPIClient
from Weather_Tools.schwab.contracts import ContractResolver
from Weather_Tools.regime.calibration import get_calibration
from Weather_Tools.regime.calculator import FeatureCalculator
from Weather_Tools.regime.classifier import RegimeClassifier
from Weather_Tools.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Weather/Market Regime Agent - Classify ES/NQ futures market regimes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python weather_tools.py --symbol ES
  python weather_tools.py --symbol NQ --output pretty
  python weather_tools.py --symbol ES --debug

Output:
  Regime classification is printed to stdout as JSON.
  Logs are printed to stderr (can be redirected separately).
        """
    )

    parser.add_argument(
        '--symbol',
        choices=['ES', 'NQ'],
        required=True,
        help='Futures product to analyze (ES or NQ)'
    )

    parser.add_argument(
        '--output',
        choices=['json', 'pretty'],
        default='json',
        help='Output format (default: json)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save data to database (dry run)'
    )

    return parser.parse_args()


def main():
    """
    Main execution flow (single-shot mode).

    Steps:
    1. Load configuration
    2. Initialize components (auth, API client, database)
    3. Resolve front month contract
    4. Fetch market data (quotes + historical candles)
    5. Persist data to SQLite
    6. Calculate features
    7. Classify regime
    8. Save regime snapshot
    9. Output JSON to stdout
    """
    args = parse_arguments()

    # Setup logging
    setup_logging(debug=args.debug)

    logger.info("="*70)
    logger.info("Weather/Market Regime Agent - Starting")
    logger.info("="*70)

    try:
        # Step 1: Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        validate_config(config)
        logger.debug(f"Data directory: {config.data_dir}")

        # Step 2: Initialize components
        logger.info("Initializing components...")

        # Token store
        token_store = TokenStore(config.credentials_dir)

        # Auth manager
        auth_manager = SchwabAuthManager(
            app_key=config.schwab_app_key,
            app_secret=config.schwab_app_secret,
            redirect_uri=config.schwab_redirect_uri,
            token_store=token_store,
            auth_url=config.schwab_auth_url,
            token_url=config.schwab_token_url
        )

        # API client
        client = SchwabAPIClient(
            auth_manager=auth_manager,
            base_url=f"{config.schwab_api_base_url}/marketdata/v1"
        )

        # Database (only if not dry run)
        if not args.no_save:
            data_store = MarketDataStore(config.db_path)
        else:
            logger.info("Dry run mode: database operations disabled")
            data_store = None

        # Step 3: Resolve front month contract
        logger.info(f"Resolving front month contract for {args.symbol}...")
        symbol = ContractResolver.get_front_month_contract(args.symbol)
        logger.info(f"Trading symbol: {symbol}")

        # Step 4: Fetch market data
        logger.info("Fetching market data from Schwab API...")

        # Get current quote
        logger.debug(f"Fetching quote for {symbol}")
        quote_data = client.get_quote(symbol, fields='quote')
        quote = quote_data.get('quote', {})
        logger.info(f"Current price: {quote.get('lastPrice', 'N/A')}")

        # Get 1-minute candles (last 10 days)
        logger.debug("Fetching 1-minute candles...")
        history_1m = client.get_intraday_candles(symbol, frequency_minutes=1, days_back=10)
        candles_1m = history_1m.get('candles', [])
        logger.info(f"Fetched {len(candles_1m)} 1-minute candles")

        # Get 5-minute candles (last 10 days)
        logger.debug("Fetching 5-minute candles...")
        history_5m = client.get_intraday_candles(symbol, frequency_minutes=5, days_back=10)
        candles_5m = history_5m.get('candles', [])
        logger.info(f"Fetched {len(candles_5m)} 5-minute candles")

        # Validate we have enough data
        if len(candles_1m) < 60:
            raise ValueError(f"Insufficient 1m data: {len(candles_1m)} candles (need 60+)")
        if len(candles_5m) < 20:
            raise ValueError(f"Insufficient 5m data: {len(candles_5m)} candles (need 20+)")

        # Step 5: Persist data to database
        if data_store:
            logger.info("Saving candle data to database...")
            data_store.insert_candles(symbol, candles_1m)
            data_store.insert_candles(symbol, candles_5m)
            logger.debug("Data persisted successfully")

        # Step 6: Calculate features
        logger.info(f"Calculating market features for {args.symbol}...")
        calibration = get_calibration(args.symbol)
        calculator = FeatureCalculator(args.symbol, calibration)

        features = calculator.calculate_features(
            candles_1m=candles_1m,
            candles_5m=candles_5m,
            current_quote=quote
        )

        logger.info(
            f"Features: VWAP={features.vwap:.2f}, ATR={features.atr_14:.2f}, "
            f"Efficiency={features.directional_efficiency:.3f}, "
            f"Overlap={features.bar_overlap_ratio:.3f}"
        )

        # Step 7: Classify regime
        logger.info("Classifying market regime...")
        classifier = RegimeClassifier(args.symbol, calibration)
        regime = classifier.classify(features)

        logger.info(
            f"Regime: {regime.primary_regime} ({regime.secondary_tag or 'N/A'}) "
            f"- Confidence: {regime.confidence}%"
        )

        # Step 8: Save regime snapshot
        if data_store:
            logger.info("Saving regime snapshot to database...")
            regime_data = regime.to_dict()
            regime_data['raw_features'] = features.to_json()  # Store features for analysis
            data_store.insert_regime_snapshot(regime_data)

        # Step 9: Output JSON to stdout
        if args.output == 'pretty':
            print(regime.to_json(pretty=True))
        else:
            print(regime.to_json(pretty=False))

        logger.info("="*70)
        logger.info("Execution completed successfully")
        logger.info("="*70)

        return 0

    except KeyboardInterrupt:
        logger.warning("Execution interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
