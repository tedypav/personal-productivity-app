#!/usr/bin/env python
"""Launch script for Personal Productivity App."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.main import main

if __name__ == "__main__":
    main()
