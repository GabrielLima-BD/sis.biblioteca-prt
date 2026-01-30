#!/usr/bin/env python3
import sys
from pathlib import Path

PROJETO_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJETO_ROOT))

from app import main

main()
