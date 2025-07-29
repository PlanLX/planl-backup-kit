#!/usr/bin/env python3
"""PlanLX Elasticsearch Backup Kit - 主入口点"""

import sys
from pathlib import Path

# Add src to path for development
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from cli import main

if __name__ == "__main__":
    main()
