# Quick Start Guide - Schwab Trading Agent Tools

**Status:** ✅ Implementation Complete (100%)
**Ready for Testing:** Yes

---

## ⚠️ Important: Use Virtual Environment

**Before you start, set up a virtual environment!** This keeps your dependencies isolated and clean.

**See [SETUP.md](SETUP.md) for complete virtual environment setup instructions.**

Quick setup:
```bash
cd "c:\Users\Alvee\Desktop\Trading Agent Tools"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**All commands below assume your virtual environment is activated** (you'll see `(venv)` in your prompt).

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies (in virtual environment)

```bash
cd "c:\Users\Alvee\Desktop\Trading Agent Tools"

# Create virtual environment (first time only)
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Credentials

1. Create a `.env` file by copying the example:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your Schwab API credentials:
   ```
   SCHWAB_APP_KEY=your_actual_app_key_here
   SCHWAB_APP_SECRET=your_actual_secret_here
   SCHWAB_REDIRECT_URI=https://localhost:8080
   ```

### Step 3: Run the Weather Agent

```bash
# Classify ES market regime
python Weather_Tools/weather_tools.py --symbol ES

# Classify NQ with pretty output
python Weather_Tools/weather_tools.py --symbol NQ --output pretty

# Debug mode (verbose logging)
python Weather_Tools/weather_tools.py --symbol ES --debug
```

---

## 📋 First Run - What to Expect

### Authentication Flow (First Time Only)

On your first run, the tool will:

1. **Open your browser** to Schwab's authorization page
2. **Ask you to log in** with your Schwab account
3. **Request permission** to access market data (read-only)
4. **Redirect to localhost** (you'll see "Authorization Successful!")
5. **Encrypt and save tokens** using Windows DPAPI

**Subsequent runs will use cached tokens automatically.**

### Expected Output

```json
{
  "instrument": "ES",
  "timestamp": "2025-12-16T20:30:00Z",
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

### Execution Time

- **First run:** ~30-60 seconds (includes OAuth browser flow)
- **Subsequent runs:** ~5-10 seconds

---

## 🎯 What the Tool Does

### Data Collection
1. ✅ Auto-detects front month ES/NQ contract (e.g., `/ESH25`)
2. ✅ Fetches real-time quote
3. ✅ Downloads 1-minute candles (last 10 days)
4. ✅ Downloads 5-minute candles (last 10 days)
5. ✅ Stores data in SQLite database

### Feature Calculation
- VWAP (Volume-Weighted Average Price)
- ATR (Average True Range)
- Realized Volatility (short & long term)
- Bar Overlap Ratio
- Directional Efficiency
- Volume Profile Analysis
- Session Phase Detection

### Regime Classification
Classifies market into one of four primary regimes:
- **Balanced / Rotational** - Mean reversion dominates
- **Trend / Initiative** - Directional movement accepted
- **Transition / Breakout Attempt** - Attempting to leave balance
- **Event-Distorted** - Dominated by news/events

---

## 📁 What Gets Created

After first run, you'll see:

```
Trading Agent Tools/
├── data/
│   ├── .credentials/
│   │   └── schwab_tokens.dat        # Encrypted tokens (DPAPI)
│   └── market_data.db                # SQLite database
└── (all your Python files)
```

**Security:** The `.credentials/` directory and database are automatically gitignored.

---

## 🔧 Command-Line Options

```bash
python Weather_Tools/weather_tools.py [OPTIONS]

Options:
  --symbol {ES,NQ}      Required. Futures product to analyze
  --output {json,pretty} Output format (default: json)
  --debug               Enable verbose logging
  --no-save             Dry run - don't save to database
```

### Examples

```bash
# Basic usage
python Weather_Tools/weather_tools.py --symbol ES

# Pretty-printed output
python Weather_Tools/weather_tools.py --symbol NQ --output pretty

# Debug mode (shows all API calls, calculations)
python Weather_Tools/weather_tools.py --symbol ES --debug

# Dry run (fetch data but don't save to database)
python Weather_Tools/weather_tools.py --symbol ES --no-save

# Redirect logs to file, output to JSON file
python Weather_Tools/weather_tools.py --symbol ES 2>logs.txt >regime.json
```

---

## 🧪 Testing Checklist

Before relying on the tool, test these scenarios:

### ✅ Authentication Test
```bash
# First run - should open browser
python Weather_Tools/weather_tools.py --symbol ES --debug

# Second run - should use cached tokens (no browser)
python Weather_Tools/weather_tools.py --symbol ES --debug
```

### ✅ Data Fetching Test
```bash
# Should fetch quotes and candles successfully
python Weather_Tools/weather_tools.py --symbol ES --debug

# Check logs for:
# - "Trading symbol: /ESH25" (or current front month)
# - "Fetched XXX 1-minute candles"
# - "Fetched XXX 5-minute candles"
# - "Current price: XXXX.XX"
```

### ✅ Database Test
```bash
# Run once
python Weather_Tools/weather_tools.py --symbol ES

# Check database exists
dir data\market_data.db

# Should see regime_snapshots and candles tables
```

### ✅ Both Instruments
```bash
# Test ES
python Weather_Tools/weather_tools.py --symbol ES --output pretty

# Test NQ
python Weather_Tools/weather_tools.py --symbol NQ --output pretty

# Different calibration parameters should be used
```

---

## 🐛 Troubleshooting

### Problem: "Missing required environment variables"
**Solution:** Create `.env` file with your Schwab credentials

### Problem: "pywin32 not available"
**Solution:** Install pywin32:
```bash
pip install pywin32
```

### Problem: "Insufficient 1m data: X candles (need 60+)"
**Solution:** This happens if:
- Market is closed
- You're requesting data outside trading hours
- API returned limited data

Try again during regular trading hours (8:30 AM - 4:00 PM CT).

### Problem: Authentication fails repeatedly
**Solution:**
1. Delete cached tokens:
   ```bash
   del data\.credentials\schwab_tokens.dat
   ```
2. Verify credentials in `.env` are correct
3. Check your Schwab Developer app status at https://developer.schwab.com/

### Problem: "Rate limited" (429 errors)
**Solution:** The tool automatically retries with exponential backoff. Wait a minute and try again.

---

## 📊 Understanding the Output

### Regime Types

| Primary Regime | Meaning | Trading Implication |
|---------------|---------|-------------------|
| **Balanced / Rotational** | Price rotates around value | Mean reversion at extremes |
| **Trend / Initiative** | Directional movement | Follow continuation signals |
| **Transition / Breakout Attempt** | Leaving balance | Wait for acceptance |
| **Event-Distorted** | News-driven | All signals degraded |

### Secondary Tags

**For Balanced:**
- `tight` - Very narrow range, compressing
- `normal` - Standard rotation
- `migrating` - Balance shifting directionally

**For Trend:**
- `clean` - High efficiency, low pullbacks
- `grinding` - Moderate efficiency
- `liquidation` - Extreme efficiency + volatility

### Confidence Score

- **80-100:** High confidence - features strongly agree
- **60-79:** Medium confidence - some agreement
- **40-59:** Low confidence - conflicting signals
- **0-39:** Very low confidence - unclear conditions

### Volatility States

- `compressing` - ATR decreasing, short-term volatility < long-term
- `normal` - Typical ATR range
- `expanding` - ATR increasing, volatility rising
- `extreme` - Range significantly above historical average

### Participation States

- `thin` - Volume below expected (>30% below normal)
- `normal` - Volume as expected
- `heavy` - Volume above expected (>30% above normal)

---

## 💡 Tips for Best Results

1. **Run during regular session hours** (8:30 AM - 4:00 PM CT)
   - Opening range (8:30-9:00) provides valuable context
   - Lunch (11:30-13:00) typically has lower confidence
   - Power hour (15:00-16:00) has increased volatility

2. **Compare ES vs NQ**
   - ES: Cleaner structure, more reliable balance
   - NQ: Higher volatility, more false breakouts

3. **Watch confidence scores**
   - High confidence (>75) = more reliable classification
   - Low confidence (<50) = conflicting signals, exercise caution

4. **Use session phase context**
   - Opening range: Wait for acceptance before acting
   - Lunch: Lower liquidity, noisier signals
   - Power hour: Increased volume and volatility

5. **Store historical snapshots**
   - The database tracks regime changes over time
   - Analyze patterns and regime persistence
   - Validate classification accuracy

---

## 📈 Next Steps

### Analyze Historical Regimes

Query the database to see regime history:

```python
from Weather_Tools.storage.data_store import MarketDataStore

store = MarketDataStore("data/market_data.db")
history = store.get_regime_history('ES', limit=100)

for snapshot in history:
    print(f"{snapshot['timestamp']}: {snapshot['primary_regime']} ({snapshot['confidence']}%)")
```

### Automate Execution

Run every 5 minutes during market hours:

**Windows Task Scheduler:**
```bash
schtasks /create /tn "ES Regime" /tr "python path\to\weather_tools.py --symbol ES" /sc minute /mo 5
```

**Or use a loop:**
```bash
# Every 5 minutes (simple loop)
while true; do
    python Weather_Tools/weather_tools.py --symbol ES >> regime_log.json
    sleep 300
done
```

### Integrate with Other Systems

The JSON output can be:
- Piped to other tools
- Logged to files
- Sent to webhooks
- Stored in time-series databases
- Used for backtesting strategies

---

## 🎓 Learning Resources

- **weather.md** - Full specification of regime detection logic
- **IMPLEMENTATION_STATUS.md** - Technical implementation details
- **README.md** - Comprehensive documentation

---

## ✅ You're Ready!

The tool is fully implemented and ready to use. Start with:

```bash
python Weather_Tools/weather_tools.py --symbol ES --output pretty
```

Good luck with your regime detection! 📊
