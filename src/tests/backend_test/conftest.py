# src/tests/backend_test/conftest.py
import sys
from pathlib import Path

# .../src/tests/backend_test/conftest.py  -> parents[2] == .../src
SRC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC))
