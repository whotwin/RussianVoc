#!/usr/bin/env python3
"""Entry point for running the app directly."""
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import RussianFlashcardsApp

if __name__ == "__main__":
    RussianFlashcardsApp().run()
