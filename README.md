# Schwab Trading Agent Tools

A Python module for real-time market regime classification of ES/NQ futures using the Charles Schwab API.

## Overview

The **Weather/Market Regime Agent** is a non-executing analytical tool that classifies current market conditions and communicates what type of behavior is statistically likely. It does NOT place trades, suggest entries/exits, or output directional bias.

### Features

- OAuth 2.0 authentication with Schwab API
- Auto-detection of front month ES/NQ futures contracts
- Real-time quote fetching
- Historical 1-minute and 5-minute candle data
- Market regime classification:
  - Balanced / Rotational
  - Trend / Initiative
  - Transition / Breakout Attempt
  - Event-Distorted
- Secure token storage using Windows DPAPI
- SQLite persistence for historical data
- Single-shot execution mode

## Installation

### Prerequisites

- Python 3.11 or higher
- Windows OS (for DPAPI token encryption)
- Schwab Developer Account with API credentials

### Setup

1. **Clone or download this repository**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Add your Schwab API credentials:
     ```
     SCHWAB_APP_KEY=your_app_key_here
     SCHWAB_APP_SECRET=your_app_secret_here
     ```

4. **Get Schwab API Credentials:**
   - Go to https://developer.schwab.com/
   - Create a new application
   - Copy your App Key and Secret to `.env`

## Usage

### Basic Usage

```bash
# Classify current ES market regime
python Weather_Tools/weather_tools.py --symbol ES

# Classify NQ market regime
python Weather_Tools/weather_tools.py --symbol NQ

# Pretty-printed output
python Weather_Tools/weather_tools.py --symbol ES --output pretty

# Debug mode
python Weather_Tools/weather_tools.py --symbol ES --debug
```

### First Run (Authentication)

On the first run, the tool will:
1. Open your browser to Schwab's authorization page
2. Ask you to approve the application
3. Redirect you to localhost (the auth code will be captured)
4. Exchange the code for access and refresh tokens
5. Encrypt and store tokens locally

Subsequent runs will use the cached tokens automatically.

### Output Format

The tool outputs JSON matching the regime classification spec:

```json
{
  "instrument": "ES",
  "timestamp": "2025-12-16T14:30:00Z",
  "primary_regime": "Trend / Initiative",
  "secondary_tag": "clean",
  "confidence": 84,
  "volatility_state": "expanding",
  "participation_state": "heavy",
  "balance_state": "imbalanced",
  "trend_quality": "clean",
  "noise_level": "low",
  "session_phase": "mid_afternoon",
  "order_flow_reliability_note": "Continuation signals favored; fading less reliable."
}
```

## Architecture

```
Weather_Tools/
├── schwab/          # Schwab API integration
│   ├── auth.py         # OAuth 2.0 authentication
│   ├── client.py       # API client (quotes, price history)
│   └── contracts.py    # Front month contract detection
├── storage/         # Data persistence
│   ├── token_store.py  # Encrypted token storage (DPAPI)
│   └── data_store.py   # SQLite database operations
├── regime/          # Regime classification logic
│   ├── calculator.py   # Feature calculations (VWAP, ATR, etc.)
│   ├── classifier.py   # Regime classification
│   ├── calibration.py  # ES/NQ-specific parameters
│   └── models.py       # Data models
└── utils/           # Utilities
    ├── session.py      # Session phase detection
    └── logging_config.py  # Logging setup
```

## Security

- **Tokens are encrypted** using Windows DPAPI (Data Protection API)
- Tokens can only be decrypted by the same Windows user on the same machine
- Credentials never stored in plain text
- `.credentials/` directory is git-ignored

## Configuration

All configuration is managed through environment variables in `.env`:

- `SCHWAB_APP_KEY`: Your Schwab API App Key
- `SCHWAB_APP_SECRET`: Your Schwab API Secret
- `SCHWAB_REDIRECT_URI`: OAuth redirect URI (default: https://localhost:8080)
- `DATA_DIR`: Data storage directory (optional)
- `LOG_LEVEL`: Logging level (default: INFO)

## Market Regime Types

### 1. Balanced / Rotational
Price rotates around value; mean reversion dominates
- High bar overlap
- VWAP acts as gravity
- Breakouts frequently fail

### 2. Trend / Initiative
One side consistently initiates and price accepts movement
- Low overlap
- Directional efficiency
- VWAP slope meaningful

### 3. Transition / Breakout Attempt
Market attempts to leave balance; acceptance not confirmed
- High risk classification
- Range expansion
- Increased volatility

### 4. Event-Distorted
Behavior dominated by scheduled/unscheduled events
- CPI, FOMC, NFP releases
- Overrides other regime classifications

## ES vs NQ Calibration

The tool uses different thresholds for ES and NQ:

- **ES**: Cleaner balance behavior, more reliable structure
- **NQ**: Higher baseline volatility, more false breakouts, stricter trend confirmation required

## Development

### Running Tests

```bash
pytest tests/
```

### Project Structure

See [weather.md](weather.md) for the complete specification of the Market Regime Agent.

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:
1. Delete `data/.credentials/schwab_tokens.dat`
2. Re-run the tool to initiate a fresh OAuth flow

### Missing Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### API Rate Limiting

The Schwab API has rate limits. If you encounter 429 errors, the client will automatically retry with exponential backoff.

## License

This project is for personal/educational use with the Schwab API.

## Contributing

This is a personal project. Feel free to fork and modify for your own use.

## Support

For Schwab API questions: https://developer.schwab.com/
For issues with this tool: Check the logs in `data/weather.log`
