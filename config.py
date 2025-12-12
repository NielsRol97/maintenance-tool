from __future__ import annotations
from pathlib import Path
import os

APP_NAME = "Windows Maintenance Tool"
APP_VERSION = "1.0.0"

BASE_DIR = Path(os.getenv("LOCALAPPDATA") or ".") / "MaintenanceTool"
LOG_DIR = BASE_DIR / "logs"

# Explicit 64-bit Windows PowerShell 5.1 to avoid x86 module mismatch
POWERSHELL_51_X64 = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

# cleanmgr profile id (you must run cleanmgr /sageset:100 once manually)
CLEANMGR_PROFILE_ID = 100
