# -*- coding: utf-8 -*-
"""Root-level conftest for admin-law-review smoke tests."""
import sys
from pathlib import Path

# Add backend directory to sys.path so `app.*` modules can be imported
BACKEND_DIR = str(Path(__file__).resolve().parent.parent / "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Also add project root for the root-level main.py
ROOT_DIR = str(Path(__file__).resolve().parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
