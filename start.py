#!/usr/bin/env python3
"""
Unified entry point for Cyber Watch
Launches the authenticated app with module selection (Text, Voice, Face)
"""

import tkinter as tk

try:
    # Use the unified app that already embeds authentication and module hub
    from app import CyberWatchApp
except Exception:
    # Fallback: run the launcher-based auth flow
    from launcher import main as launcher_main


def main():
    try:
        app = CyberWatchApp()
        app.mainloop()
    except Exception:
        # If unified app import/run fails, fallback to launcher flow
        launcher_main()


if __name__ == "__main__":
    main()


