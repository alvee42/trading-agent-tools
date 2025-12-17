# Complete Setup Guide with Virtual Environment

**Recommended setup for Schwab Trading Agent Tools**

This guide will walk you through setting up a clean Python virtual environment for the project.

---

## Why Use a Virtual Environment?

✅ **Isolation** - Dependencies don't conflict with other Python projects
✅ **Reproducibility** - Exact same package versions every time
✅ **Clean** - Easy to delete and recreate if something goes wrong
✅ **Best Practice** - Standard approach for Python projects

---

## 🚀 Complete Setup (5-10 Minutes)

### Step 1: Verify Python Installation

```bash
# Check Python version (need 3.11+)
python --version

# or if python points to Python 2.x
python3 --version
```

**Expected output:** `Python 3.11.x` or higher

If Python is not installed or version is too old:
- Download from: https://www.python.org/downloads/
- Install Python 3.11 or newer
- Make sure to check "Add Python to PATH" during installation

---

### Step 2: Navigate to Project Directory

```bash
cd "c:\Users\Alvee\Desktop\Trading Agent Tools"
```

---

### Step 3: Create Virtual Environment

```bash
# Create a new virtual environment named 'venv'
python -m venv venv

# Alternative if 'python' doesn't work
python3 -m venv venv
```

**What this does:**
- Creates a `venv/` directory in your project
- Contains an isolated Python installation
- Includes pip, setuptools, and other essentials

**Note:** The `venv/` directory is already in `.gitignore` so it won't be committed to git.

---

### Step 4: Activate Virtual Environment

**On Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**On Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**If PowerShell gives an error about execution policy:**
```powershell
# Run PowerShell as Administrator, then:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate:
venv\Scripts\Activate.ps1
```

**On Windows (Git Bash):**
```bash
source venv/Scripts/activate
```

**Success indicator:** Your prompt should now show `(venv)` at the beginning:
```
(venv) C:\Users\Alvee\Desktop\Trading Agent Tools>
```

---

### Step 5: Upgrade pip (Recommended)

```bash
python -m pip install --upgrade pip
```

This ensures you have the latest pip version with all bug fixes.

---

### Step 6: Install Project Dependencies

```bash
pip install -r requirements.txt
```

**What gets installed:**
- requests (HTTP client for API calls)
- pandas (data manipulation)
- numpy (numerical calculations)
- python-dotenv (environment variables)
- pywin32 (Windows DPAPI encryption)
- authlib (OAuth 2.0)

**Expected output:** Successful installation of all packages

---

### Step 7: Verify Installation

```bash
python test_installation.py
```

**All tests should show ✅**

If you see ❌ for .env configuration:
- Continue to Step 8

---

### Step 8: Configure Credentials

```bash
# Copy the example file
copy .env.example .env

# Open .env in your editor (Notepad, VS Code, etc.)
notepad .env
```

**Edit `.env` and add your credentials:**
```
SCHWAB_APP_KEY=your_actual_app_key_from_schwab_developer_portal
SCHWAB_APP_SECRET=your_actual_secret_from_schwab_developer_portal
SCHWAB_REDIRECT_URI=https://localhost:8080
```

**Where to get credentials:**
1. Go to https://developer.schwab.com/
2. Sign in with your Schwab account
3. Create a new app or use existing app
4. Copy "App Key" and "Secret"

**Save the file** and close your editor.

---

### Step 9: Test Configuration

```bash
python test_installation.py
```

**All tests should now show ✅**

---

### Step 10: Run Your First Classification

```bash
# Test with ES
python Weather_Tools\weather_tools.py --symbol ES --output pretty

# Or test with NQ
python Weather_Tools\weather_tools.py --symbol NQ --output pretty
```

**First run:** Browser will open for OAuth authorization
- Log in to Schwab
- Approve the application
- Browser shows "Authorization Successful!"
- Tokens are encrypted and saved

**Subsequent runs:** Automatic (uses cached tokens)

---

## 📝 Daily Usage

### Activate Virtual Environment (every time you open a new terminal)

```bash
# Navigate to project
cd "c:\Users\Alvee\Desktop\Trading Agent Tools"

# Activate venv
venv\Scripts\activate
```

### Run the Weather Agent

```bash
# Basic usage
python Weather_Tools\weather_tools.py --symbol ES

# Pretty output
python Weather_Tools\weather_tools.py --symbol ES --output pretty

# Debug mode
python Weather_Tools\weather_tools.py --symbol ES --debug

# Both instruments
python Weather_Tools\weather_tools.py --symbol ES --output pretty
python Weather_Tools\weather_tools.py --symbol NQ --output pretty
```

### Deactivate Virtual Environment (when done)

```bash
deactivate
```

This returns you to your system Python.

---

## 🛠️ Troubleshooting Virtual Environment

### Problem: "python is not recognized"

**Solution:** Python not in PATH
```bash
# Use full path to Python
C:\Python311\python.exe -m venv venv
```

Or reinstall Python and check "Add Python to PATH"

---

### Problem: PowerShell won't run activate script

**Solution:** Execution policy blocked it
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again.

---

### Problem: Wrong Python version in venv

**Solution:** Specify Python version explicitly
```bash
# Use Python 3.11 specifically
py -3.11 -m venv venv
```

---

### Problem: Virtual environment corrupted

**Solution:** Delete and recreate
```bash
# Deactivate first
deactivate

# Delete venv folder
rmdir /s venv

# Recreate
python -m venv venv

# Activate
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

### Problem: "pip install fails with SSL errors"

**Solution:** Upgrade pip over HTTP first
```bash
python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --upgrade pip
```

Then install requirements normally.

---

## 🔄 Updating Dependencies

If `requirements.txt` is updated in the future:

```bash
# Activate venv
venv\Scripts\activate

# Update packages
pip install --upgrade -r requirements.txt
```

---

## 📦 Managing the Virtual Environment

### Check installed packages

```bash
pip list
```

### Check outdated packages

```bash
pip list --outdated
```

### Freeze current dependencies (if you add new packages)

```bash
pip freeze > requirements.txt
```

### Remove a package

```bash
pip uninstall package_name
```

---

## 🗂️ Project Structure with venv

```
Trading Agent Tools/
├── venv/                          ← Virtual environment (gitignored)
│   ├── Scripts/
│   │   ├── activate.bat
│   │   ├── python.exe
│   │   └── pip.exe
│   ├── Lib/
│   └── pyvenv.cfg
│
├── Weather_Tools/                 ← Your code
│   ├── __init__.py
│   ├── weather_tools.py
│   └── ...
│
├── data/                          ← Generated data (gitignored)
│   ├── .credentials/
│   └── market_data.db
│
├── requirements.txt               ← Dependencies
├── .env                           ← Your credentials (gitignored)
├── .env.example                   ← Template
├── .gitignore                     ← Git ignore rules
└── README.md                      ← Documentation
```

---

## ✅ Checklist

Use this checklist to verify your setup:

- [ ] Python 3.11+ installed
- [ ] Virtual environment created (`venv/` folder exists)
- [ ] Virtual environment activated (prompt shows `(venv)`)
- [ ] pip upgraded to latest version
- [ ] All dependencies installed from `requirements.txt`
- [ ] `.env` file created with Schwab credentials
- [ ] `test_installation.py` passes all tests
- [ ] First run completed successfully (OAuth flow)
- [ ] Tokens encrypted and saved
- [ ] Can run tool with `--symbol ES`

---

## 🎯 Quick Reference

### Activate venv
```bash
venv\Scripts\activate               # Windows CMD
venv\Scripts\Activate.ps1           # Windows PowerShell
source venv/Scripts/activate        # Git Bash
```

### Deactivate venv
```bash
deactivate
```

### Run Weather Agent
```bash
python Weather_Tools\weather_tools.py --symbol ES --output pretty
```

### Update dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Recreate venv
```bash
deactivate
rmdir /s venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🚀 You're Ready!

With your virtual environment set up, you have a clean, isolated environment for the Weather Agent.

**Next:** See **QUICKSTART.md** for usage examples and **README.md** for comprehensive documentation.

**Happy trading!** 📊
