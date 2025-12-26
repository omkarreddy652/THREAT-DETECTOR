#!/usr/bin/env python3
"""
Cyber Watch Launcher
Starts with authentication and redirects to appropriate modules
"""

import tkinter as tk
import sys
import os
from auth_gui import AuthGUI

def main():
    """Main launcher function"""
    # Create the root window
    root = tk.Tk()
    
    # Start the authentication GUI
    auth_app = AuthGUI(root)
    
    # Run the application
    root.mainloop()

if __name__ == "__main__":
    main() 