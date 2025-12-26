import tkinter as tk
from tkinter import messagebox, ttk
import threading
from auth.auth_manager import AuthManager

# Color scheme
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
ERROR_COLOR = "#ff6b6b"
SUCCESS_COLOR = "#51cf66"

class AuthGUI:
    def __init__(self, parent, on_auth_success):
        self.parent = parent
        self.auth_manager = AuthManager()
        self.on_auth_success = on_auth_success
        self.current_frame = None
        self.shadow_canvas = None
        
    def show_auth_card(self, mode="signup"):
        self.clear_frame()
        self.auth_mode = mode  # 'signup' or 'signin'
        # Centered card with shadow and rounded corners
        # Draw a shadow canvas behind the card
        shadow_canvas = tk.Canvas(self.parent, width=460, height=650, bg="#f0f0f0", highlightthickness=0)
        shadow_canvas.place(relx=0.5, rely=0.5, anchor="center")
        def draw_rounded_rect(canvas, x1, y1, x2, y2, radius=24, **kwargs):
            points = [
                x1+radius, y1,
                x2-radius, y1,
                x2, y1,
                x2, y1+radius,
                x2, y2-radius,
                x2, y2,
                x2-radius, y2,
                x1+radius, y2,
                x1, y2,
                x1, y2-radius,
                x1, y1+radius,
                x1, y1
            ]
            return canvas.create_polygon(points, smooth=True, **kwargs)
        draw_rounded_rect(shadow_canvas, 10, 10, 450, 640, radius=32, fill="#d3d3d3", outline="")
        # Card frame (fixed width, increased height, centered)
        card = tk.Frame(self.parent, bg="#fff", bd=0, highlightthickness=0, width=440, height=630)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)
        card.lift()

        # Create a scrollable frame
        canvas = tk.Canvas(card, bg="#fff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(card, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#fff")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)

        # Logo and title
        logo = tk.Label(scrollable_frame, text="🛡️", font=("Segoe UI", 32), bg="#fff")
        logo.pack(pady=(28, 0))
        title = tk.Label(scrollable_frame, text="Cyber Watch", font=("Segoe UI", 26, "bold"), bg="#fff", fg="#232946")
        title.pack(pady=(0, 2))
        subtitle = tk.Label(scrollable_frame, text="Your comprehensive cybersecurity suite", font=("Segoe UI", 12), bg="#fff", fg="#888")
        subtitle.pack(pady=(0, 18))

        # Tabs
        tab_frame = tk.Frame(scrollable_frame, bg="#fff")
        tab_frame.pack(pady=(0, 16), fill="x")
        def switch_to_signin():
            self.show_auth_card("signin")
        def switch_to_signup():
            self.show_auth_card("signup")
        signin_tab = tk.Label(tab_frame, text="Sign In", font=("Segoe UI", 12, "bold"), bg="#fff" if mode=="signin" else "#f3f3f3", fg="#232946" if mode=="signin" else "#888", bd=0, relief="flat", padx=32, pady=8, cursor="hand2")
        signin_tab.pack(side="left", padx=(0, 2))
        signin_tab.bind("<Button-1>", lambda e: switch_to_signin())
        signup_tab = tk.Label(tab_frame, text="Sign Up", font=("Segoe UI", 12, "bold"), bg="#fff" if mode=="signup" else "#f3f3f3", fg="#232946" if mode=="signup" else "#888", bd=0, relief="flat", padx=32, pady=8, cursor="hand2")
        signup_tab.pack(side="left")
        signup_tab.bind("<Button-1>", lambda e: switch_to_signup())

        # Form
        form_frame = tk.Frame(scrollable_frame, bg="#fff")
        form_frame.pack(pady=(0, 0), fill="x")
        if mode == "signup":
            tk.Label(form_frame, text="Username", font=("Segoe UI", 10), bg="#fff", anchor="w").pack(fill="x", padx=8, pady=(8, 0))
            self.signup_username_entry = tk.Entry(form_frame, font=("Segoe UI", 12), bg="#f7f7f7", fg="#232946", relief="flat", bd=2, highlightthickness=1, highlightbackground="#eee", highlightcolor="#4285f4")
            self.signup_username_entry.pack(fill="x", padx=8, pady=(0, 8))
            tk.Label(form_frame, text="Email", font=("Segoe UI", 10), bg="#fff", anchor="w").pack(fill="x", padx=8, pady=(0, 0))
            self.signup_email_entry = tk.Entry(form_frame, font=("Segoe UI", 12), bg="#f7f7f7", fg="#232946", relief="flat", bd=2, highlightthickness=1, highlightbackground="#eee", highlightcolor="#4285f4")
            self.signup_email_entry.pack(fill="x", padx=8, pady=(0, 8))
            tk.Label(form_frame, text="Password", font=("Segoe UI", 10), bg="#fff", anchor="w").pack(fill="x", padx=8, pady=(0, 0))
            self.signup_password_entry = tk.Entry(form_frame, font=("Segoe UI", 12), bg="#f7f7f7", fg="#232946", show="*", relief="flat", bd=2, highlightthickness=1, highlightbackground="#eee", highlightcolor="#4285f4")
            self.signup_password_entry.pack(fill="x", padx=8, pady=(0, 8))
            tk.Label(form_frame, text="Confirm Password", font=("Segoe UI", 10), bg="#fff", anchor="w").pack(fill="x", padx=8, pady=(0, 0))
            self.signup_confirm_entry = tk.Entry(form_frame, font=("Segoe UI", 12), bg="#f7f7f7", fg="#232946", show="*", relief="flat", bd=2, highlightthickness=1, highlightbackground="#eee", highlightcolor="#4285f4")
            self.signup_confirm_entry.pack(fill="x", padx=8, pady=(0, 16))
            signup_btn = tk.Button(form_frame, text="Create Account", command=self.register_user, font=("Segoe UI", 12, "bold"), bg="#232946", fg="#fff", activebackground="#232946", activeforeground="#fff", relief="flat", bd=0, cursor="hand2")
            signup_btn.pack(fill="x", padx=8, pady=(0, 12))
        else:
            tk.Label(form_frame, text="Username or Email", font=("Segoe UI", 10), bg="#fff", anchor="w").pack(fill="x", padx=8, pady=(8, 0))
            self.username_entry = tk.Entry(form_frame, font=("Segoe UI", 12), bg="#f7f7f7", fg="#232946", relief="flat", bd=2, highlightthickness=1, highlightbackground="#eee", highlightcolor="#4285f4")
            self.username_entry.pack(fill="x", padx=8, pady=(0, 8))
            tk.Label(form_frame, text="Password", font=("Segoe UI", 10), bg="#fff", anchor="w").pack(fill="x", padx=8, pady=(0, 0))
            self.password_entry = tk.Entry(form_frame, font=("Segoe UI", 12), bg="#f7f7f7", fg="#232946", show="*", relief="flat", bd=2, highlightthickness=1, highlightbackground="#eee", highlightcolor="#4285f4")
            self.password_entry.pack(fill="x", padx=8, pady=(0, 16))
            signin_btn = tk.Button(form_frame, text="Sign In", command=self.login_user, font=("Segoe UI", 12, "bold"), bg="#232946", fg="#fff", activebackground="#232946", activeforeground="#fff", relief="flat", bd=0, cursor="hand2")
            signin_btn.pack(fill="x", padx=8, pady=(0, 12))

        # Divider (always present) - REMOVED
        # divider_frame = tk.Frame(card, bg="#fff")
        # divider_frame.pack(fill="x", pady=(8, 0))
        # tk.Frame(divider_frame, bg="#eee", height=1).pack(fill="x", padx=8, pady=(0, 0))
        # tk.Label(divider_frame, text="OR SIGN UP WITH" if mode=="signup" else "OR SIGN IN WITH", font=("Segoe UI", 9), bg="#fff", fg="#888").pack(pady=(0, 0))
        # tk.Frame(divider_frame, bg="#eee", height=1).pack(fill="x", padx=8, pady=(0, 0))
        # OAuth buttons (clean, centered) - REMOVED
        # oauth_frame = tk.Frame(card, bg="#fff")
        # oauth_frame.pack(side="bottom", pady=(20, 24))
        # google_btn = tk.Button(oauth_frame, text="Google", command=self.google_signup, font=("Segoe UI", 12, "bold"), bg="#fff", fg="#4285f4", activebackground="#e8f0fe", activeforeground="#4285f4", relief="groove", bd=1, cursor="hand2", highlightbackground="#4285f4", highlightcolor="#4285f4", padx=24, pady=8)
        # google_btn.pack(side="left", padx=16)
        # self.add_tooltip(google_btn, "Sign in with Google")
        # github_btn = tk.Button(oauth_frame, text="GitHub", command=self.github_signup, font=("Segoe UI", 12, "bold"), bg="#fff", fg="#232946", activebackground="#f3f3f3", activeforeground="#232946", relief="groove", bd=1, cursor="hand2", highlightbackground="#232946", highlightcolor="#232946", padx=24, pady=8)
        # github_btn.pack(side="left", padx=16)
        # self.add_tooltip(github_btn, "Sign in with GitHub")
        # def on_enter_google(e):
        #     google_btn.config(bg="#e8f0fe")
        # def on_leave_google(e):
        #     google_btn.config(bg="#fff")
        # google_btn.bind("<Enter>", on_enter_google)
        # google_btn.bind("<Leave>", on_leave_google)
        # def on_enter_github(e):
        #     github_btn.config(bg="#f3f3f3")
        # def on_leave_github(e):
        #     github_btn.config(bg="#fff")
        # github_btn.bind("<Enter>", on_enter_github)
        # github_btn.bind("<Leave>", on_leave_github)

        self.current_frame = card
        self.shadow_canvas = shadow_canvas
        self.parent.bind("<Return>", lambda e: self.register_user() if mode=="signup" else self.login_user())
        
        # Focus on first entry
        if mode == "signup":
            self.signup_username_entry.focus()
        else:
            self.username_entry.focus()

    def clear_frame(self):
        """Clear current frame"""
        if hasattr(self, 'shadow_canvas') and self.shadow_canvas:
            self.shadow_canvas.destroy()
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None
    
    def login_user(self):
        """Handle user login"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        # Show loading
        self.show_loading("Signing in...")
        
        # Run login in thread to avoid blocking UI
        def login_thread():
            success, result = self.auth_manager.login_user(username, password)
            
            # Update UI in main thread
            self.parent.after(0, lambda: self.handle_login_result(success, result))
        
        threading.Thread(target=login_thread, daemon=True).start()
    
    def register_user(self):
        """Handle user registration"""
        username = self.signup_username_entry.get().strip()
        email = self.signup_email_entry.get().strip()
        password = self.signup_password_entry.get()
        confirm_password = self.signup_confirm_entry.get()
        
        if not username or not email or not password or not confirm_password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long")
            return
        
        # Show loading
        self.show_loading("Creating account...")
        
        # Run registration in thread
        def register_thread():
            success, result = self.auth_manager.register_user(username, email, password)
            
            # Update UI in main thread
            self.parent.after(0, lambda: self.handle_register_result(success, result))
        
        threading.Thread(target=register_thread, daemon=True).start()
    
    def google_signup(self):
        """Handle Google OAuth signup"""
        self.show_loading("Connecting to Google...")
        
        def google_thread():
            success, result = self.auth_manager.google_signup()
            self.parent.after(0, lambda: self.handle_oauth_result(success, result, "Google"))
        
        threading.Thread(target=google_thread, daemon=True).start()
    
    def github_signup(self):
        """Handle GitHub OAuth signup"""
        self.show_loading("Connecting to GitHub...")
        
        def github_thread():
            success, result = self.auth_manager.github_signup()
            self.parent.after(0, lambda: self.handle_oauth_result(success, result, "GitHub"))
        
        threading.Thread(target=github_thread, daemon=True).start()
    
    def microsoft_signup(self):
        """Handle Microsoft OAuth signup"""
        self.show_loading("Connecting to Microsoft...")
        
        def microsoft_thread():
            success, result = self.auth_manager.microsoft_signup()
            self.parent.after(0, lambda: self.handle_oauth_result(success, result, "Microsoft"))
        
        threading.Thread(target=microsoft_thread, daemon=True).start()
    
    def facebook_signup(self):
        """Handle Facebook OAuth signup"""
        self.show_loading("Connecting to Facebook...")
        
        def facebook_thread():
            success, result = self.auth_manager.facebook_signup()
            self.parent.after(0, lambda: self.handle_oauth_result(success, result, "Facebook"))
        
        threading.Thread(target=facebook_thread, daemon=True).start()
    
    def show_loading(self, message):
        """Show loading message (now does nothing, overlay removed)"""
        self.clear_frame()
        # No overlay, no spinner, no message
        # self.current_frame = None
    
    def handle_login_result(self, success, result):
        """Handle login result"""
        if success:
            self.on_auth_success(result)
        else:
            self.clear_frame()
            self.show_auth_card("signin")
            messagebox.showerror("Login Failed", result)
    
    def handle_register_result(self, success, result):
        """Handle registration result"""
        if success:
            messagebox.showinfo("Success", "Account created successfully! Please sign in.")
            self.show_auth_card("signin")
        else:
            self.clear_frame()
            self.show_auth_card("signup")
            messagebox.showerror("Registration Failed", result)
    
    def handle_oauth_result(self, success, result, provider):
        """Handle OAuth result"""
        if success:
            self.on_auth_success(result)
        else:
            self.clear_frame()
            self.show_auth_card("signup")
            messagebox.showerror(f"{provider} Login Failed", result)

    def add_tooltip(self, button, text):
        """Add a tooltip to a button"""
        tooltip = tk.Label(
            button, 
            text=text, 
            font=("Segoe UI", 10),
            bg=BG_FRAME, 
            fg=FG_MAIN
        )
        tooltip.pack(pady=(0, 5))
        tooltip.pack_forget()
        
        def show_tooltip(event):
            tooltip.pack(pady=(0, 5))
        
        def hide_tooltip(event):
            tooltip.pack_forget()
        
        button.bind("<Enter>", show_tooltip)
        button.bind("<Leave>", hide_tooltip) 