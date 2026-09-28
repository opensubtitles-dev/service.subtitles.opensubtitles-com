"""Thin xbmc.service entry point.

All logic lives in resources/lib/background_service.py - Kodi's repo review
flags declared entry-point libraries that exceed ~15 code lines, and a thin
delegate also keeps the service's real module importable in tests.
"""
from resources.lib.background_service import run_service

if __name__ == "__main__":
    run_service()
