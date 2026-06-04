import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "backend"))

from main import app
from mangum import Mangum

handler = Mangum(app)
