from pathlib import Path
import os
import sys

# DATA SETTINGS
FIBER_CHANNELS = 6000
FIBER_NAME = "fiber_0"
FIBER_SAMPLING_RATE = 100

# Python path
PYTHON_PATH = Path(sys.executable)

# EQNet directory (clone of the EQNet repository)
EQNET_DIR = Path(r"C:\Users\prisma\Documents\EQNet")

# Data root directory (absolute path)
DATA_ROOT = Path(r"Z:\Tzahi")

# File list path (absolute path to the file list)
FILE_LIST_PATH = EQNET_DIR / "to_process.txt"

# Results path (absolute path to the results directory)
RESULTS_PATH = EQNET_DIR / "results"
PICKS_DIR = RESULTS_PATH / "picks_phasenet_das_patch"
OUTPUT_DIR = RESULTS_PATH / "figures_phasenet_das"

# Telegram notification settings (read from environment variables)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")