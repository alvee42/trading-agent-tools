"""
Installation and Configuration Test Script

Run this to verify your setup before using the Weather Agent.
"""

import sys
from pathlib import Path

print("="*70)
print("Schwab Trading Agent Tools - Installation Test")
print("="*70)
print()

# Test 1: Python version
print("Test 1: Python Version")
print(f"  Python: {sys.version}")
if sys.version_info >= (3, 11):
    print("  ✅ Python 3.11+ detected")
else:
    print("  ❌ Python 3.11+ required")
    print(f"  Current version: {sys.version_info.major}.{sys.version_info.minor}")
print()

# Test 2: Required packages
print("Test 2: Required Packages")
required_packages = [
    'requests',
    'pandas',
    'numpy',
    'dotenv',
    'win32crypt',
    'authlib'
]

all_installed = True
for package in required_packages:
    try:
        if package == 'dotenv':
            import dotenv
        elif package == 'win32crypt':
            import win32crypt
        elif package == 'authlib':
            import authlib
        else:
            __import__(package)
        print(f"  ✅ {package}")
    except ImportError:
        print(f"  ❌ {package} - NOT INSTALLED")
        all_installed = False

if not all_installed:
    print()
    print("  Fix: pip install -r requirements.txt")
print()

# Test 3: .env file
print("Test 3: Configuration File")
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    print(f"  ✅ .env file exists")

    # Check if it has the required keys
    with open(env_file) as f:
        content = f.read()
        has_key = "SCHWAB_APP_KEY" in content and "your_app_key_here" not in content
        has_secret = "SCHWAB_APP_SECRET" in content and "your_app_secret_here" not in content

        if has_key:
            print("  ✅ SCHWAB_APP_KEY configured")
        else:
            print("  ❌ SCHWAB_APP_KEY missing or not configured")

        if has_secret:
            print("  ✅ SCHWAB_APP_SECRET configured")
        else:
            print("  ❌ SCHWAB_APP_SECRET missing or not configured")
else:
    print(f"  ❌ .env file not found")
    print(f"  Fix: copy .env.example to .env and add your credentials")
print()

# Test 4: Module imports
print("Test 4: Module Imports")
try:
    from config import load_config
    print("  ✅ config module")
except Exception as e:
    print(f"  ❌ config module - {e}")

try:
    from Weather_Tools.storage.token_store import TokenStore
    print("  ✅ token_store module")
except Exception as e:
    print(f"  ❌ token_store module - {e}")

try:
    from Weather_Tools.schwab.auth import SchwabAuthManager
    print("  ✅ auth module")
except Exception as e:
    print(f"  ❌ auth module - {e}")

try:
    from Weather_Tools.schwab.client import SchwabAPIClient
    print("  ✅ client module")
except Exception as e:
    print(f"  ❌ client module - {e}")

try:
    from Weather_Tools.schwab.contracts import ContractResolver
    print("  ✅ contracts module")
except Exception as e:
    print(f"  ❌ contracts module - {e}")

try:
    from Weather_Tools.regime.calibration import get_calibration
    print("  ✅ calibration module")
except Exception as e:
    print(f"  ❌ calibration module - {e}")

try:
    from Weather_Tools.regime.calculator import FeatureCalculator
    print("  ✅ calculator module")
except Exception as e:
    print(f"  ❌ calculator module - {e}")

try:
    from Weather_Tools.regime.classifier import RegimeClassifier
    print("  ✅ classifier module")
except Exception as e:
    print(f"  ❌ classifier module - {e}")

print()

# Test 5: Configuration loading
print("Test 5: Configuration Loading")
try:
    from config import load_config
    config = load_config()
    print(f"  ✅ Configuration loaded successfully")
    print(f"  Data directory: {config.data_dir}")
    print(f"  DB path: {config.db_path}")
except Exception as e:
    print(f"  ❌ Configuration failed: {e}")
print()

# Test 6: Front month contract detection
print("Test 6: Front Month Contract Detection")
try:
    from Weather_Tools.schwab.contracts import ContractResolver
    es_symbol = ContractResolver.get_front_month_contract('ES')
    nq_symbol = ContractResolver.get_front_month_contract('NQ')
    print(f"  ✅ ES front month: {es_symbol}")
    print(f"  ✅ NQ front month: {nq_symbol}")
except Exception as e:
    print(f"  ❌ Contract detection failed: {e}")
print()

# Summary
print("="*70)
print("Summary")
print("="*70)
print()
print("If all tests passed (✅), you're ready to run:")
print()
print("  python Weather_Tools/weather_tools.py --symbol ES --output pretty")
print()
print("If any tests failed (❌), fix the issues above before proceeding.")
print()
print("Need help? Check README.md or QUICKSTART.md")
print("="*70)
