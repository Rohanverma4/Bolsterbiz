import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / "backend" / ".env")

from main import app

application = app
