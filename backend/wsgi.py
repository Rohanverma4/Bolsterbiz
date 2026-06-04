import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from main import app
from asgiref.wsgi import AsgiToWsgi

application = AsgiToWsgi(app)
