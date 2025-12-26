#!/usr/bin/env python3
"""
Authentication GUI for Cyber Watch
Provides sign-in/sign-up functionality with navigation to modules
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sys
from auth.auth_manager import AuthManager

# Color scheme matching the main app
BG_MAIN = "#232946"
BG_FRAME = "#232946"
FG_MAIN = "#eebbc3"
BTN_BG = "#eebbc3"
BTN_FG = "#232946"
BTN_ACTIVE_BG = "#d4939d"
BTN_ACTIVE_FG = "#232946"
LABEL_BG = "#232946"
LABEL_FG = "#eebbc3"
ENTRY_BG = "#fffffe"
ENTRY_FG = "#232946"
ACCENT_COLOR = "#e94560"

class AuthGUI:
    def __init__(self, root):
        self.root = root
        self.auth_manager = AuthManager()
        self.current_user = None
        self.current_session = None
        
        # Configure main window
        self.root.title("Cyber Watch - Authentication")
        self.root.geometry("500x900")
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(False, False)
        
        # Center the window
        self.center_window()
        
        # Create GUI
        self.create_widgets()
        
        # Show login page by default
        self.show_login_page()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Main container
        self.main_frame = tk.Frame(self.root, bg=BG_MAIN)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Logo and title
        self.create_header()
        
        # Content area (will be updated based on current page)
        self.content_frame = tk.Frame(self.main_frame, bg=BG_MAIN)
        self.content_frame.pack(fill="both", expand=True, pady=20)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Welcome to Cyber Watch!")
        self.status_bar = tk.Label(
            self.root, 
            textvariable=self.status_var, 
            bd=1, 
            relief="sunken", 
            anchor="w", 
            bg=BG_FRAME, 
            fg=FG_MAIN, 
            font=("Segoe UI", 10)
        )
        self.status_bar.pack(side="bottom", fill="x")
    
    def create_header(self):
        """Create the header with logo and title"""
        header_frame = tk.Frame(self.main_frame, bg=BG_MAIN)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Logo (text-based for now)
        logo_label = tk.Label(
            header_frame,
            text="🛡️",
            font=("Segoe UI", 48),
            bg=BG_MAIN,
            fg=ACCENT_COLOR
        )
        logo_label.pack()
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="Cyber Watch",
            font=("Segoe UI", 24, "bold"),
            bg=BG_MAIN,
            fg=LABEL_FG
        )
        title_label.pack()
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Emotion-Aware Cybersecurity",
            font=("Segoe UI", 12),
            bg=BG_MAIN,
            fg=LABEL_FG
        )
        subtitle_label.pack()
    
    def clear_content(self):
        """Clear the content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_login_page(self):
        """Show the login page"""
        self.clear_content()
        
        # Login form
        login_frame = tk.Frame(self.content_frame, bg=BG_MAIN)
        login_frame.pack(expand=True)
        
        # Title
        tk.Label(
            login_frame,
            text="Sign In",
            font=("Segoe UI", 20, "bold"),
            bg=BG_MAIN,
            fg=LABEL_FG
        ).pack(pady=(0, 20))
        
        # Username/Email field
        tk.Label(
            login_frame,
            text="Username or Email:",
            font=("Segoe UI", 12),
            bg=BG_MAIN,
            fg=LABEL_FG
        ).pack(anchor="w", pady=(0, 5))
        
        self.login_username_var = tk.StringVar()
        username_entry = tk.Entry(
            login_frame,
            textvariable=self.login_username_var,
            font=("Segoe UI", 12),
            bg=ENTRY_BG,
            fg=ENTRY_FG,
            relief="flat",
            bd=10
        )
        username_entry.pack(fill="x", pady=(0, 15))
        
        # Password field
        tk.Label(
            login_frame,
            text="Password:",
            font=("Segoe UI", 12),
            bg=BG_MAIN,
            fg=LABEL_FG
        ).pack(anchor="w", pady=(0, 5))
        
        self.login_password_var = tk.StringVar()
        password_entry = tk.Entry(
            login_frame,
            textvariable=self.login_password_var,
            show="*",
            font=("Segoe UI", 12),
            bg=ENTRY_BG,
            fg=ENTRY_FG,
            relief="flat",
            bd=10
        )
        password_entry.pack(fill="x", pady=(0, 20))
        
        # Login button
        login_btn = tk.Button(
            login_frame,
            text="Sign In",
            command=self.handle_login,
            font=("Segoe UI", 14, "bold"),
            bg=BTN_BG,
            fg=BTN_FG,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=30,
            pady=10
        )
        login_btn.pack(pady=(0, 15))
        
        # OAuth buttons
        oauth_frame = tk.Frame(login_frame, bg=BG_MAIN)
        oauth_frame.pack(fill="x", pady=(0, 20))
        
        # Google login
        google_btn = tk.Button(
            oauth_frame,
            text="🔍 Sign in with Google",
            command=self.handle_google_login,
            font=("Segoe UI", 12),
            bg="#4285f4",
            fg="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=8
        )
        google_btn.pack(fill="x", pady=(0, 10))
        
        # GitHub login
        github_btn = tk.Button(
            oauth_frame,
            text="🐙 Sign in with GitHub",
            command=self.handle_github_login,
            font=("Segoe UI", 12),
            bg="#333",
            fg="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=8
        )
        github_btn.pack(fill="x", pady=(0, 10))
        
        # Divider
        divider_frame = tk.Frame(login_frame, bg=BG_MAIN)
        divider_frame.pack(fill="x", pady=20)
        
        divider_label = tk.Label(
            divider_frame,
            text="────────── OR ──────────",
            font=("Segoe UI", 10),
            bg=BG_MAIN,
            fg=LABEL_FG
        )
        divider_label.pack()
        
        # Sign up link
        signup_link = tk.Label(
            login_frame,
            text="Don't have an account? Sign up",
            font=("Segoe UI", 12),
            bg=BG_MAIN,
            fg=ACCENT_COLOR,
            cursor="hand2"
        )
        signup_link.pack(pady=10)
        signup_link.bind("<Button-1>", lambda e: self.show_signup_page())
        
        # Focus on username entry
        username_entry.focus()
    
    def show_signup_page(self):
        """Show the signup page"""
        self.clear_content()
        
        # Signup form
        signup_frame = tk.Frame(self.content_frame, bg=BG_MAIN)
        signup_frame.pack(expand=True)
        
        # Title
        tk.Label(
            signup_frame,
            text="Create Account",
            font=("Segoe UI", 20, "bold"),
            bg=BG_MAIN,
            fg=LABEL_FG
        ).pack(pady=(0, 20))
        
        # Username field
        tk.Label(
            signup_frame,
            text="Username:",
            font=("Segoe UI", 12),
            bg=BG_MAIN,
            fg=LABEL_FG
        ).pack(anchor="w", pady=(0, 5))
        
        self.signup_username_var = tk.StringVar()
        username_entry = tk.Entry(
            signup_frame,
            textvariable=self.signup_username_var,
            font=("Segoe UI", 12),
            bg=ENTRY_BG,
            fg=ENTRY_FG,
            relief="flat",
            bd=10
        )
        username_entry.pack(fill="x", pady=(0, 15))
        
        # Email field
        tk.Label(
            signup_frame,
            text="Email:",
            font=("Segoe UI", 12),
            bg=BG_MAIN,
            fg=LABEL_FG
        ).pack(anchor="w", pady=(0, 5))
        
        self.signup_email_var = tk.StringVar()
        email_entry = tk.Entry(
            signup_frame,
            textvariable=self.signup_email_var,
            font=("Segoe UI", 12),
            bg=ENTRY_BG,
            fg=ENTRY_FG,
            relief="flat",
            bd=10
        )
        email_entry.pack(fill="x", pady=(0, 15))
        
        # Password field
        tk.Label(
            signup_frame,
            text="Password:",
            font=("Segoe UI", 12),
            bg=BG_MAIN,
            fg=LABEL_FG
        ).pack(anchor="w", pady=(0, 5))
        
        self.signup_password_var = tk.StringVar()
        password_entry = tk.Entry(
            signup_frame,
            textvariable=self.signup_password_var,
            show="*",
            font=("Segoe UI", 12),
            bg=ENTRY_BG,
            fg=ENTRY_FG,
            relief="flat",
            bd=10
        )
        password_entry.pack(fill="x", pady=(0, 15))
        
        # Confirm Password field
        tk.Label(
            signup_frame,
            text="Confirm Password:",
            font=("Segoe UI", 12),
            bg=BG_MAIN,
            fg=LABEL_FG
        ).pack(anchor="w", pady=(0, 5))
        
        self.signup_confirm_password_var = tk.StringVar()
        confirm_password_entry = tk.Entry(
            signup_frame,
            textvariable=self.signup_confirm_password_var,
            show="*",
            font=("Segoe UI", 12),
            bg=ENTRY_BG,
            fg=ENTRY_FG,
            relief="flat",
            bd=10
        )
        confirm_password_entry.pack(fill="x", pady=(0, 20))
        
        # Sign up button
        signup_btn = tk.Button(
            signup_frame,
            text="Create Account",
            command=self.handle_signup,
            font=("Segoe UI", 14, "bold"),
            bg=BTN_BG,
            fg=BTN_FG,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=30,
            pady=10
        )
        signup_btn.pack(pady=(0, 15))
        
        # OAuth signup buttons
        oauth_frame = tk.Frame(signup_frame, bg=BG_MAIN)
        oauth_frame.pack(fill="x", pady=(0, 20))
        
        # Google signup
        google_btn = tk.Button(
            oauth_frame,
            text="🔍 Sign up with Google",
            command=self.handle_google_signup,
            font=("Segoe UI", 12),
            bg="#4285f4",
            fg="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=8
        )
        google_btn.pack(fill="x", pady=(0, 10))
        
        # GitHub signup
        github_btn = tk.Button(
            oauth_frame,
            text="🐙 Sign up with GitHub",
            command=self.handle_github_signup,
            font=("Segoe UI", 12),
            bg="#333",
            fg="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=8
        )
        github_btn.pack(fill="x", pady=(0, 10))
        
        # Divider
        divider_frame = tk.Frame(signup_frame, bg=BG_MAIN)
        divider_frame.pack(fill="x", pady=20)
        
        divider_label = tk.Label(
            divider_frame,
            text="────────── OR ──────────",
            font=("Segoe UI", 10),
            bg=BG_MAIN,
            fg=LABEL_FG
        )
        divider_label.pack()
        
        # Sign in link
        signin_link = tk.Label(
            signup_frame,
            text="Already have an account? Sign in",
            font=("Segoe UI", 12),
            bg=BG_MAIN,
            fg=ACCENT_COLOR,
            cursor="hand2"
        )
        signin_link.pack(pady=10)
        signin_link.bind("<Button-1>", lambda e: self.show_login_page())
        
        # Focus on username entry
        username_entry.focus()
    
    def show_module_selection(self):
        """Show module selection page after successful authentication"""
        self.clear_content()
        
        # Welcome message
        welcome_frame = tk.Frame(self.content_frame, bg=BG_MAIN)
        welcome_frame.pack(expand=True)
        
        # Welcome title
        tk.Label(
            welcome_frame,
            text=f"Welcome, {self.current_user['username']}!",
            font=("Segoe UI", 20, "bold"),
            bg=BG_MAIN,
            fg=LABEL_FG
        ).pack(pady=(0, 10))
        
        tk.Label(
            welcome_frame,
            text="Choose a module to analyze:",
            font=("Segoe UI", 14),
            bg=BG_MAIN,
            fg=LABEL_FG
        ).pack(pady=(0, 30))
        
        # Module buttons
        modules_frame = tk.Frame(welcome_frame, bg=BG_MAIN)
        modules_frame.pack(expand=True)
        
        # Text Analyzer
        text_btn = tk.Button(
            modules_frame,
            text="📝 Text Analyzer",
            command=lambda: self.launch_module("text"),
            font=("Segoe UI", 16, "bold"),
            bg=BTN_BG,
            fg=BTN_FG,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=40,
            pady=15,
            width=20
        )
        text_btn.pack(pady=10)
        
        # Voice Analyzer
        voice_btn = tk.Button(
            modules_frame,
            text="🎤 Voice Analyzer",
            command=lambda: self.launch_module("voice"),
            font=("Segoe UI", 16, "bold"),
            bg=BTN_BG,
            fg=BTN_FG,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=40,
            pady=15,
            width=20
        )
        voice_btn.pack(pady=10)
        
        # Face Analyzer
        face_btn = tk.Button(
            modules_frame,
            text="😊 Face Analyzer",
            command=lambda: self.launch_module("face"),
            font=("Segoe UI", 16, "bold"),
            bg=BTN_BG,
            fg=BTN_FG,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=40,
            pady=15,
            width=20
        )
        face_btn.pack(pady=10)
        
        # Logout button
        logout_btn = tk.Button(
            welcome_frame,
            text="🚪 Logout",
            command=self.handle_logout,
            font=("Segoe UI", 12),
            bg="#d9534f",
            fg="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=8
        )
        logout_btn.pack(pady=20)
    
    def handle_login(self):
        """Handle login form submission"""
        username = self.login_username_var.get().strip()
        password = self.login_password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        self.set_status("Signing in...")
        
        def login_thread():
            try:
                success, result = self.auth_manager.login_user(username, password)
                
                if success:
                    self.current_user = result['user']
                    self.current_session = result['session_token']
                    self.root.after(0, lambda: self.login_success())
                else:
                    self.root.after(0, lambda: self.login_error(result))
                    
            except Exception as e:
                self.root.after(0, lambda: self.login_error(f"Login failed: {str(e)}"))
        
        threading.Thread(target=login_thread, daemon=True).start()
    
    def handle_signup(self):
        """Handle signup form submission"""
        username = self.signup_username_var.get().strip()
        email = self.signup_email_var.get().strip()
        password = self.signup_password_var.get()
        confirm_password = self.signup_confirm_password_var.get()
        
        if not username or not email or not password or not confirm_password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long")
            return
        
        self.set_status("Creating account...")
        
        def signup_thread():
            try:
                success, result = self.auth_manager.register_user(username, email, password)
                
                if success:
                    # Auto-login after successful signup
                    login_success, login_result = self.auth_manager.login_user(username, password)
                    if login_success:
                        self.current_user = login_result['user']
                        self.current_session = login_result['session_token']
                        self.root.after(0, lambda: self.signup_success())
                    else:
                        self.root.after(0, lambda: self.signup_error("Registration successful but auto-login failed. Please sign in manually."))
                else:
                    self.root.after(0, lambda: self.signup_error(result))
                    
            except Exception as e:
                self.root.after(0, lambda: self.signup_error(f"Registration failed: {str(e)}"))
        
        threading.Thread(target=signup_thread, daemon=True).start()
    
    def handle_google_login(self):
        """Handle Google OAuth login"""
        self.set_status("Connecting to Google...")
        
        def google_thread():
            try:
                success, result = self.auth_manager.google_login()
                
                if success:
                    self.current_user = result['user']
                    self.current_session = result['session_token']
                    self.root.after(0, lambda: self.login_success())
                else:
                    self.root.after(0, lambda: self.login_error(result))
                    
            except Exception as e:
                self.root.after(0, lambda: self.login_error(f"Google login failed: {str(e)}"))
        
        threading.Thread(target=google_thread, daemon=True).start()
    
    def handle_github_login(self):
        """Handle GitHub OAuth login"""
        self.set_status("Connecting to GitHub...")
        
        def github_thread():
            try:
                success, result = self.auth_manager.github_login()
                
                if success:
                    self.current_user = result['user']
                    self.current_session = result['session_token']
                    self.root.after(0, lambda: self.login_success())
                else:
                    self.root.after(0, lambda: self.login_error(result))
                    
            except Exception as e:
                self.root.after(0, lambda: self.login_error(f"GitHub login failed: {str(e)}"))
        
        threading.Thread(target=github_thread, daemon=True).start()
    
    def handle_google_signup(self):
        """Handle Google OAuth signup"""
        self.set_status("Connecting to Google...")
        
        def google_thread():
            try:
                success, result = self.auth_manager.google_signup()
                
                if success:
                    self.current_user = result['user']
                    self.current_session = result['session_token']
                    self.root.after(0, lambda: self.signup_success())
                else:
                    self.root.after(0, lambda: self.signup_error(result))
                    
            except Exception as e:
                self.root.after(0, lambda: self.signup_error(f"Google signup failed: {str(e)}"))
        
        threading.Thread(target=google_thread, daemon=True).start()
    
    def handle_github_signup(self):
        """Handle GitHub OAuth signup"""
        self.set_status("Connecting to GitHub...")
        
        def github_thread():
            try:
                success, result = self.auth_manager.github_signup()
                
                if success:
                    self.current_user = result['user']
                    self.current_session = result['session_token']
                    self.root.after(0, lambda: self.signup_success())
                else:
                    self.root.after(0, lambda: self.signup_error(result))
                    
            except Exception as e:
                self.root.after(0, lambda: self.signup_error(f"GitHub signup failed: {str(e)}"))
        
        threading.Thread(target=github_thread, daemon=True).start()
    
    def login_success(self):
        """Handle successful login"""
        self.set_status(f"Welcome back, {self.current_user['username']}!")
        messagebox.showinfo("Success", f"Welcome back, {self.current_user['username']}!")
        self.show_module_selection()
    
    def login_error(self, error):
        """Handle login error"""
        self.set_status("Login failed")
        messagebox.showerror("Login Failed", str(error))
    
    def signup_success(self):
        """Handle successful signup"""
        self.set_status(f"Account created successfully!")
        messagebox.showinfo("Success", f"Account created successfully! Welcome, {self.current_user['username']}!")
        self.show_module_selection()
    
    def signup_error(self, error):
        """Handle signup error"""
        self.set_status("Registration failed")
        messagebox.showerror("Registration Failed", str(error))
    
    def launch_module(self, module_type):
        """Launch the selected module"""
        self.set_status(f"Launching {module_type} analyzer...")
        
        # Close the auth window
        self.root.withdraw()
        
        try:
            if module_type == "text":
                # Launch text analyzer
                from main import CyberWatchApp
                app = CyberWatchApp()
                app.show_text_analyzer_menu()
                app.mainloop()
            elif module_type == "voice":
                # Launch voice analyzer
                from main import CyberWatchApp
                app = CyberWatchApp()
                app.show_voice_analyzer()
                app.mainloop()
            elif module_type == "face":
                # Launch face analyzer
                from main import CyberWatchApp
                app = CyberWatchApp()
                app.show_face_analyzer()
                app.mainloop()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch {module_type} analyzer: {str(e)}")
            self.root.deiconify()  # Show auth window again
    
    def handle_logout(self):
        """Handle logout"""
        if self.current_session:
            try:
                self.auth_manager.logout_user(self.current_session)
            except:
                pass
        
        self.current_user = None
        self.current_session = None
        self.set_status("Logged out successfully")
        self.show_login_page()
    
    def set_status(self, message, clear_after=4):
        """Set status message"""
        self.status_var.set(message)
        if clear_after:
            self.root.after(clear_after * 1000, lambda: self.status_var.set(""))

def main():
    """Main function to run the authentication GUI"""
    root = tk.Tk()
    app = AuthGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 