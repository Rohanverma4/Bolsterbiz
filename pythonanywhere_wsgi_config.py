import sys
sys.path.insert(0, '/home/<your-username>/Bolsterbiz/backend')

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

from wsgi import application
