import tkinter as tk
from tkinter import messagebox
import threading
import os
import sys
import time
import winsound
from auth.auth_manager import AuthManager
from gui.auth_gui import AuthGUI

# Runtime checks for optional dependencies used by the face webcam monitor.
# Keep imports lazy-friendly but expose simple flags so the UI can provide
# actionable messages instead of crashing with ImportError.
try:
    import cv2  # type: ignore
    HAS_OPENCV = True
except Exception:
    cv2 = None
    HAS_OPENCV = False

try:
    from PIL import Image, ImageTk  # type: ignore
    HAS_PIL = True
except Exception:
    Image = None
    ImageTk = None
    HAS_PIL = False

# Heavy/optional imports (transformers, torch, google client libs, opencv, PIL)
# are imported lazily inside functions to avoid import-time failures when the
# environment doesn't have them installed. This keeps the authentication GUI
# and main menu available even if ML/audio libs are missing.

# --- Modern color palette ---
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
SCROLL_BG = "#121629"
SCROLL_FG = "#eebbc3"

def play_sound(label, repeat=1):
    for _ in range(repeat):
        key = label.lower()
        if key == "safe":
            winsound.Beep(1200, 150)
        elif key == "offensive":
            winsound.Beep(800, 300)
        elif key == "threat":
            winsound.Beep(400, 500)
        else:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        time.sleep(0.1)

class CyberWatchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cyber Watch - Emotion-Aware Cybersecurity")
        self.geometry("950x700")
        self.state("zoomed")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        
        # Initialize components
        self.current_frame = None
        # Initialize text classifier lazily and safely. If heavy ML deps are missing
        # (transformers/torch), fall back to a lightweight dummy classifier so the
        # GUI remains usable without crashing at import time.
        try:
            from model.text_model import TextThreatClassifier
            self.classifier = TextThreatClassifier()
        except Exception as e:
            print(f"[WARN] TextThreatClassifier not available, using DummyClassifier: {e}")
            class DummyClassifier:
                def predict(self, text):
                    return ("Safe", "✅")
                def predict_scores(self, text):
                    return {"threat": 0.0}
                def extract_threat_offensive_words(self, text, threshold=0.2):
                    return []
            self.classifier = DummyClassifier()
        self.auth_manager = AuthManager()
        self.current_user = None
        self.session_token = None
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(
            self, 
            textvariable=self.status_var, 
            bd=1, 
            relief="sunken", 
            anchor="w", 
            bg=BG_FRAME, 
            fg=FG_MAIN, 
            font=("Segoe UI", 11)
        )
        self.status_bar.pack(side="bottom", fill="x")
        
        # Bind keyboard shortcuts
        self.bind("<Control-q>", lambda e: self.on_exit())
        
        # Initialize scanning
        self.stop_scan_event = threading.Event()
        
        # Show authentication first
        self.show_auth()

    def show_auth(self):
        """Show authentication screen"""
        self.set_status("Please create an account to get started...")
        self.auth_gui = AuthGUI(self, self.on_auth_success)
        self.auth_gui.show_auth_card("signup")

    def on_auth_success(self, auth_result):
        """Handle successful authentication"""
        self.current_user = auth_result['user']
        self.session_token = auth_result['session_token']
        
        # Update status
        self.set_status(f"Welcome, {self.current_user['username']}!")
        
        # Show main menu
        self.show_main_menu()

    def set_status(self, message, clear_after=4):
        self.status_var.set(message)
        if clear_after:
            self.after(clear_after * 1000, lambda: self.status_var.set(""))

    def add_tooltip(self, widget, text):
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        label = tk.Label(tooltip, text=text, bg="#333", fg="#fff", font=("Segoe UI", 10), padx=6, pady=2)
        label.pack()
        def enter(event):
            x = widget.winfo_rootx() + 40
            y = widget.winfo_rooty() + 20
            tooltip.geometry(f"+{x}+{y}")
            tooltip.deiconify()
        def leave(event):
            tooltip.withdraw()
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def toggle_theme(self):
        global BG_MAIN, BG_FRAME, FG_MAIN, BTN_BG, BTN_FG, BTN_ACTIVE_BG, BTN_ACTIVE_FG, LABEL_BG, LABEL_FG, ENTRY_BG, ENTRY_FG
        if BG_MAIN == "#232946":
            BG_MAIN = "#f5f5f5"
            BG_FRAME = "#f5f5f5"
            FG_MAIN = "#232946"
            BTN_BG = "#232946"
            BTN_FG = "#eebbc3"
            BTN_ACTIVE_BG = "#393e46"
            BTN_ACTIVE_FG = "#eebbc3"
            LABEL_BG = "#f5f5f5"
            LABEL_FG = "#232946"
            ENTRY_BG = "#fff"
            ENTRY_FG = "#232946"
        else:
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
        self.configure(bg=BG_MAIN)
        self.status_bar.configure(bg=BG_FRAME, fg=FG_MAIN)
        self.show_main_menu()

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()

    def style_button(self, btn):
        btn.configure(
            bg=BTN_BG,
            fg=BTN_FG,
            activebackground=BTN_ACTIVE_BG,
            activeforeground=BTN_ACTIVE_FG,
            relief="flat",
            bd=0,
            font=("Segoe UI", 16, "bold"),
            cursor="hand2"
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=BTN_ACTIVE_BG))
        btn.bind("<Leave>", lambda e: btn.config(bg=BTN_BG))

    def style_back_button(self, btn):
        btn.configure(
            bg="#d9534f",
            fg="#fff",
            activebackground="#c9302c",
            activeforeground="#fff",
            relief="flat",
            bd=0,
            font=("Segoe UI", 12, "bold"),
            cursor="hand2"
        )
        btn.bind("<Enter>", lambda e: btn.config(bg="#c9302c"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#d9534f"))

    def logout(self):
        """Logout current user"""
        if self.session_token:
            self.auth_manager.logout_user(self.session_token)
        
        self.current_user = None
        self.session_token = None
        self.show_auth()

    def show_main_menu(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)

        # Top bar with Back and Logout
        top_bar = tk.Frame(frame, bg=BG_FRAME)
        top_bar.pack(fill="x", padx=20, pady=20)
        back_btn = tk.Button(
            top_bar,
            text="⬅ Back",
            command=self.show_auth,  # Back to auth screen
            font=("Segoe UI", 12, "bold"),
            bg="#6c757d",
            fg="white",
            activebackground="#495057",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2"
        )
        back_btn.pack(side="left")
        logout_btn = tk.Button(
            top_bar,
            text="🚪 Logout",
            command=self.logout,
            font=("Segoe UI", 12, "bold"),
            bg="#dc3545",
            fg="white",
            activebackground="#c82333",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2"
        )
        logout_btn.pack(side="right")

        # Centered analyzer buttons, higher up
        modules_frame = tk.Frame(frame, bg=BG_FRAME)
        modules_frame.pack(pady=(40,0), expand=False)  # Add top padding, don't expand to bottom
        btn_voice = tk.Button(
            modules_frame, text="🎤 Voice Analyzer", command=self.show_voice_analyzer,
            font=("Segoe UI", 22, "bold"), bg="#45b7d1", fg="white",
            activebackground="#2980b9", activeforeground="white",
            relief="flat", bd=0, cursor="hand2", width=20, height=3
        )
        btn_voice.pack(pady=20)
        btn_text = tk.Button(
            modules_frame, text="📝 Text Analyzer", command=self.show_text_analyzer_menu,
            font=("Segoe UI", 22, "bold"), bg="#ff6b6b", fg="white",
            activebackground="#c0392b", activeforeground="white",
            relief="flat", bd=0, cursor="hand2", width=20, height=3
        )
        btn_text.pack(pady=20)
        btn_face = tk.Button(
            modules_frame, text="😊 Face Analyzer", command=self.show_face_analyzer,
            font=("Segoe UI", 22, "bold"), bg="#4ecdc4", fg="white",
            activebackground="#16a085", activeforeground="white",
            relief="flat", bd=0, cursor="hand2", width=20, height=3
        )
        btn_face.pack(pady=20)

        self.current_frame = frame
    
    def darken_color(self, color):
        """Darken a hex color for hover effects"""
        # Simple color darkening - you can make this more sophisticated
        if color.startswith("#"):
            color = color[1:]
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # Darken by 20%
        r = max(0, int(r * 0.8))
        g = max(0, int(g * 0.8))
        b = max(0, int(b * 0.8))
        
        return f"#{r:02x}{g:02x}{b:02x}"

    def show_scan_history(self):
        """Show user's scan history"""
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        
        # Back button
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_main_menu)
        self.style_back_button(back_btn)
        back_btn.config(width=10)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        
        # Title
        tk.Label(
            frame, text="Scan History", font=("Segoe UI", 32, "bold"), 
            bg=LABEL_BG, fg=LABEL_FG
        ).pack(pady=20)
        
        # Get scan history
        history = self.auth_manager.db.get_user_scan_history(self.current_user['user_id'])
        
        if not history:
            tk.Label(
                frame, text="No scan history found", 
                font=("Segoe UI", 16), bg=LABEL_BG, fg=LABEL_FG
            ).pack(pady=50)
        else:
            # Create scrollable frame for history
            canvas = tk.Canvas(frame, bg=BG_FRAME, highlightthickness=0)
            scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=BG_FRAME)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Add history items
            for i, (scan_type, content, result, confidence, timestamp) in enumerate(history):
                item_frame = tk.Frame(scrollable_frame, bg=BG_FRAME, relief="solid", bd=1)
                item_frame.pack(fill="x", padx=20, pady=5)
                
                # Header
                header_frame = tk.Frame(item_frame, bg=BG_FRAME)
                header_frame.pack(fill="x", padx=10, pady=5)
                
                tk.Label(
                    header_frame, text=f"{scan_type} - {timestamp}", 
                    font=("Segoe UI", 12, "bold"), bg=LABEL_BG, fg=LABEL_FG
                ).pack(side="left")
                
                # Result indicator
                result_color = "#51cf66" if result == "Safe" else "#ff6b6b"
                tk.Label(
                    header_frame, text=result, 
                    font=("Segoe UI", 12, "bold"), bg=result_color, fg="white",
                    padx=10, pady=2
                ).pack(side="right")
                
                # Content preview
                content_preview = content[:100] + "..." if len(content) > 100 else content
                tk.Label(
                    item_frame, text=f"Content: {content_preview}", 
                    font=("Segoe UI", 10), bg=LABEL_BG, fg=LABEL_FG,
                    wraplength=800, justify="left"
                ).pack(anchor="w", padx=10, pady=(0, 5))
            
            canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
            scrollbar.pack(side="right", fill="y")
        
        self.current_frame = frame

    def show_text_analyzer_menu(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_main_menu)
        self.style_back_button(back_btn)
        back_btn.config(width=10)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="Text Analyzer", font=("Segoe UI", 32, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=20)

        # 4 big option buttons
        options_frame = tk.Frame(frame, bg=BG_FRAME)
        options_frame.pack(pady=40)
        btn_text = tk.Button(
            options_frame, text="✍️ Text", command=self.show_text_manual,
            font=("Segoe UI", 18, "bold"), bg="#ffb347", fg="white",
            activebackground="#e67e22", activeforeground="white",
            relief="flat", bd=0, cursor="hand2", width=18, height=2
        )
        btn_text.grid(row=0, column=0, padx=25, pady=20)
        btn_gmail = tk.Button(
            options_frame, text="📧 Gmail", command=self.show_gmail_scanner,
            font=("Segoe UI", 18, "bold"), bg="#4285f4", fg="white",
            activebackground="#3367d6", activeforeground="white",
            relief="flat", bd=0, cursor="hand2", width=18, height=2
        )
        btn_gmail.grid(row=0, column=1, padx=25, pady=20)
        btn_chat = tk.Button(
            options_frame, text="💬 Chat Monitor", command=self.show_chat_monitor,
            font=("Segoe UI", 18, "bold"), bg="#8e44ad", fg="white",
            activebackground="#6c3483", activeforeground="white",
            relief="flat", bd=0, cursor="hand2", width=18, height=2
        )
        btn_chat.grid(row=1, column=0, padx=25, pady=20)
        btn_file = tk.Button(
            options_frame, text="📁 File Scanner", command=self.show_file_scanner,
            font=("Segoe UI", 18, "bold"), bg="#16a085", fg="white",
            activebackground="#117864", activeforeground="white",
            relief="flat", bd=0, cursor="hand2", width=18, height=2
        )
        btn_file.grid(row=1, column=1, padx=25, pady=20)

        self.current_frame = frame

    # --- Text Threat Analyzer ---
    def show_text_analyzer(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_text_analyzer_menu)
        self.style_back_button(back_btn)
        back_btn.config(width=10)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="Text Threat Analyzer", font=("Segoe UI", 32, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=20)
        input_frame = tk.Frame(frame, bg=BG_FRAME)
        input_frame.pack(fill="both", expand=True, padx=50, pady=20)
        tk.Label(input_frame, text="Enter text to analyze:", font=("Segoe UI", 16), bg=LABEL_BG, fg=LABEL_FG).pack(anchor="w", pady=(0, 10))
        text_area = tk.Text(input_frame, height=10, font=("Segoe UI", 12), bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", bd=10)
        text_area.pack(fill="both", expand=True, pady=(0, 20))
        btn_frame = tk.Frame(input_frame, bg=BG_FRAME)
        btn_frame.pack(fill="x")
        def clear_text():
            text_area.delete(1.0, tk.END)
        def analyze():
            import re
            text = text_area.get(1.0, tk.END).strip()
            if not text:
                messagebox.showwarning("Warning", "Please enter some text to analyze")
                return
            match = re.search(r"\d+", text)
            if match:
                found_number = match.group(0)
                def after_reentry(user_input):
                    if user_input == found_number:
                        self.show_safe_alert("Numbers match. No threat detected.")
                        result = "Safe"
                    else:
                        self.show_text_analyzer_popup_alert("Numbers do not match. Potential threat detected.")
                        result = "Threat"
                    self.auth_manager.db.save_scan_result(
                        self.current_user['user_id'], "text_manual", text, result
                    )
                    repeat = 2 if result.lower() == "threat" else 1
                    play_sound(result.lower(), repeat=repeat)
                self.show_number_reentry_alert_topleft(found_number, after_reentry)
                return
            result, icon = self.classifier.predict(text)
            self.auth_manager.db.save_scan_result(
                self.current_user['user_id'], "text_analysis", text, result
            )
            repeat = 2 if result.lower() == "threat" else 1
            play_sound(result.lower(), repeat=repeat)
            if result.strip().lower() in ["threat", "offensive"]:
                self.show_text_analyzer_popup_alert(f"Given text is {result}")
            result_label.config(text=f"{icon} Analysis Result: {result}")
        clear_btn = tk.Button(btn_frame, text="🗑️ Clear", command=clear_text, font=("Segoe UI", 12, "bold"), bg="#6c757d", fg="white", activebackground="#5a6268", activeforeground="white", relief="flat", bd=0, cursor="hand2")
        clear_btn.pack(side="left", padx=(0, 10))
        analyze_btn = tk.Button(btn_frame, text="🔍 Analyze", command=analyze, font=("Segoe UI", 12, "bold"), bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE_BG, activeforeground=BTN_ACTIVE_FG, relief="flat", bd=0, cursor="hand2")
        analyze_btn.pack(side="left")
        self.current_frame = frame

    def show_text_analyzer_popup_alert(self, message):
        popup = tk.Toplevel(self)
        popup.title("Alert!")
        popup.geometry("400x150+50+50")
        popup.configure(bg="#2d2d44")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        popup.attributes('-topmost', True)
        popup.lift()
        popup.focus_force()
        popup.after(100, lambda: popup.deiconify())
        icon_label = tk.Label(popup, text="⚠️", font=("Segoe UI", 36), bg="#2d2d44", fg="#ff6b6b")
        icon_label.pack(pady=(15, 0))
        msg_label = tk.Label(popup, text=message, font=("Segoe UI", 16, "bold"), bg="#2d2d44", fg="#ff6b6b", wraplength=360, justify="center")
        msg_label.pack(pady=(10, 0))
        ok_btn = tk.Button(popup, text="OK", command=popup.destroy, font=("Segoe UI", 12, "bold"), bg="#ff6b6b", fg="white", activebackground="#c82333", activeforeground="white", relief="flat", bd=0, cursor="hand2", width=10)
        ok_btn.pack(pady=10)

    def show_popup(self, label, message):
        popup = tk.Toplevel(self)
        popup.title(f"Analysis Result - {label}")
        popup.geometry("500x300")
        popup.configure(bg=BG_FRAME)
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        
        # Center popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (500 // 2)
        y = (popup.winfo_screenheight() // 2) - (300 // 2)
        popup.geometry(f"500x300+{x}+{y}")
        
        # Result icon and label
        icon_frame = tk.Frame(popup, bg=BG_FRAME)
        icon_frame.pack(pady=20)
        
        icon_text = "✅" if label == "Safe" else "⚠️" if label == "Threat" else "❗"
        icon_label = tk.Label(icon_frame, text=icon_text, font=("Segoe UI", 48), bg=BG_FRAME, fg=FG_MAIN)
        icon_label.pack()
        
        result_label = tk.Label(icon_frame, text=label, font=("Segoe UI", 24, "bold"), bg=BG_FRAME, fg=FG_MAIN)
        result_label.pack()
        
        # Message
        message_text = tk.Text(popup, height=8, font=("Segoe UI", 12), bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", bd=5, wrap=tk.WORD)
        message_text.pack(fill="both", expand=True, padx=20, pady=10)
        message_text.insert(1.0, message)
        message_text.config(state=tk.DISABLED)
        
        # Close button
        close_btn = tk.Button(popup, text="Close", command=popup.destroy, font=("Segoe UI", 12, "bold"), bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE_BG, activeforeground=BTN_ACTIVE_FG, relief="flat", bd=0, cursor="hand2")
        close_btn.pack(pady=20)

    def show_gmail_scanner(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_text_analyzer_menu)
        self.style_back_button(back_btn)
        back_btn.config(width=10)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="Gmail Threat Scanner", font=("Segoe UI", 32, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=20)

        gmail_frame = tk.Frame(frame, bg=BG_FRAME)
        gmail_frame.pack(fill="both", expand=True, padx=50, pady=20)
        status_label = tk.Label(gmail_frame, text="", font=("Segoe UI", 12), bg=BG_FRAME, fg=LABEL_FG)
        status_label.pack(pady=(0, 10))
        result_box = tk.Text(gmail_frame, height=15, font=("Segoe UI", 12), bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", bd=5, state=tk.DISABLED)
        result_box.pack(fill="both", expand=True, pady=(0, 10))

        def scan_gmail():
            status_label.config(text="Authenticating with Gmail...")
            result_box.config(state=tk.NORMAL)
            result_box.delete(1.0, tk.END)
            result_box.config(state=tk.DISABLED)
            self.update()
            try:
                # --- Begin credentials block ---
                SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
                creds = None
                token_path = 'token.pickle'
                credentials_path = 'credentials.json'
                if os.path.exists(token_path):
                    with open(token_path, 'rb') as token:
                        creds = pickle.load(token)
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                        creds = flow.run_local_server(port=0)
                    with open(token_path, 'wb') as token:
                        pickle.dump(creds, token)
                if not creds:
                    status_label.config(text="Gmail authentication failed.")
                    return
                service = build('gmail', 'v1', credentials=creds)
                status_label.config(text="Fetching emails...")
                self.update()
                # --- End credentials block ---
                # Prompt user for number of emails to scan AFTER authentication
                def ask_num_emails():
                    popup = tk.Toplevel(self)
                    popup.title("Number of Emails")
                    popup.geometry("350x180")
                    popup.configure(bg="#2d2d44")
                    popup.resizable(False, False)
                    popup.transient(self)
                    popup.grab_set()
                    popup.attributes('-topmost', True)
                    popup.update_idletasks()
                    x = (popup.winfo_screenwidth() // 2) - (350 // 2)
                    y = (popup.winfo_screenheight() // 2) - (180 // 2)
                    popup.geometry(f"350x180+{x}+{y}")
                    tk.Label(popup, text="Enter number of emails to scan:", font=("Segoe UI", 14), bg="#2d2d44", fg="#ffb6b6").pack(pady=(20, 10))
                    entry = tk.Entry(popup, font=("Segoe UI", 14), width=10)
                    entry.pack(pady=5)
                    entry.focus_set()
                    error_label = tk.Label(popup, text="", font=("Segoe UI", 10), bg="#2d2d44", fg="#ff6b6b")
                    error_label.pack()
                    def on_ok():
                        try:
                            num = int(entry.get())
                            if num <= 0:
                                raise ValueError
                            print(f"[DEBUG] User entered number of emails: {num}")
                            popup.destroy()
                            scan(num)
                        except ValueError:
                            error_label.config(text="Please enter a valid positive number.")
                    def on_cancel():
                        print("[DEBUG] User cancelled email scan.")
                        popup.destroy()
                        status_label.config(text="Scan cancelled by user.")
                    btn_frame = tk.Frame(popup, bg="#2d2d44")
                    btn_frame.pack(pady=10)
                    ok_btn = tk.Button(btn_frame, text="OK", command=on_ok, font=("Segoe UI", 12, "bold"), bg="#ff6b6b", fg="white", activebackground="#c82333", activeforeground="white", relief="flat", bd=0, cursor="hand2", width=10)
                    ok_btn.pack(side="left", padx=5)
                    cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel, font=("Segoe UI", 12, "bold"), bg="#6c757d", fg="white", activebackground="#495057", activeforeground="white", relief="flat", bd=0, cursor="hand2", width=10)
                    cancel_btn.pack(side="left", padx=5)
                def scan(num_emails):
                    try:
                        print(f"[DEBUG] Starting scan for {num_emails} emails.")
                        results = service.users().messages().list(userId='me', maxResults=num_emails).execute()
                        messages = results.get('messages', [])
                        threats = 0
                        for msg in messages:
                            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
                            snippet = msg_data.get('snippet', '')
                            subject = ''
                            headers = msg_data.get('payload', {}).get('headers', [])
                            for h in headers:
                                if h['name'].lower() == 'subject':
                                    subject = h['value']
                                    break
                            result, icon = self.classifier.predict(snippet)
                            print("Gmail Scanner result:", result)
                            # Print result for every email
                            result_box.config(state=tk.NORMAL)
                            result_box.insert(tk.END, f"[{icon} {result}] Subject: {subject}\n")
                            result_box.config(state=tk.DISABLED)
                            if result.strip().lower() in ["threat", "offensive"]:
                                print("Calling show_threat_alert for gmail scanner")
                                self.after(0, lambda s=subject: self.show_threat_alert(f"{result} detected in email!\nSubject: {s}", position="topleft"))
                            repeat = 2 if result.lower() == "threat" else 1
                            play_sound(result.lower(), repeat=repeat)
                            if result != "Safe":
                                threats += 1
                        status_label.config(text=f"Scan complete. {threats} threats found.")
                    except Exception as e:
                        print(f"[ERROR] Exception during scan: {e}")
                        self.after(0, lambda: self.show_threat_alert(f"Error during scan: {e}", position="topleft"))
                        status_label.config(text=f"Error: {e}")
                ask_num_emails()
            except Exception as e:
                print(f"[ERROR] Exception in scan_gmail: {e}")
                self.after(0, lambda: self.show_threat_alert(f"Error: {e}", position="topleft"))
                status_label.config(text=f"Error: {e}")

        def change_account():
            import os
            token_path = 'token.pickle'
            if os.path.exists(token_path):
                os.remove(token_path)
            status_label.config(text="Account disconnected. Please scan again to login with a different Gmail account.")
            result_box.config(state=tk.NORMAL)
            result_box.delete(1.0, tk.END)
            result_box.config(state=tk.DISABLED)

        scan_btn = tk.Button(gmail_frame, text="🔍 Scan Gmail", command=scan_gmail, font=("Segoe UI", 14, "bold"), bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE_BG, activeforeground=BTN_ACTIVE_FG, relief="flat", bd=0, cursor="hand2", width=18, height=2)
        scan_btn.pack(side="left", padx=10, pady=10)
        change_btn = tk.Button(gmail_frame, text="🔄 Change Account", command=change_account, font=("Segoe UI", 14, "bold"), bg="#4285f4", fg="white", activebackground="#3367d6", activeforeground="white", relief="flat", bd=0, cursor="hand2", width=18, height=2)
        change_btn.pack(side="left", padx=10, pady=10)

        self.current_frame = frame

    def show_chat_monitor(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_text_analyzer_menu)
        self.style_back_button(back_btn)
        back_btn.config(width=10)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="Live Chat Monitor", font=("Segoe UI", 32, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=20)

        chat_frame = tk.Frame(frame, bg=BG_FRAME)
        chat_frame.pack(fill="both", expand=True, padx=50, pady=20)
        chat_log = tk.Text(chat_frame, height=15, font=("Segoe UI", 12), bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", bd=5, state=tk.DISABLED)
        chat_log.pack(fill="both", expand=True, pady=(0, 10))
        entry_frame = tk.Frame(chat_frame, bg=BG_FRAME)
        entry_frame.pack(fill="x")
        entry = tk.Entry(entry_frame, font=("Segoe UI", 12), bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", bd=5)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)
        result_label = tk.Label(chat_frame, text="", font=("Segoe UI", 12, "bold"), bg=BG_FRAME, fg=LABEL_FG)
        result_label.pack(pady=(5, 0))

        def send_message(event=None):
            msg = entry.get().strip()
            if not msg:
                return
            entry.delete(0, tk.END)
            chat_log.config(state=tk.NORMAL)
            chat_log.insert(tk.END, f"You: {msg}\n")
            chat_log.config(state=tk.DISABLED)
            chat_log.see(tk.END)
            # Analyze for threat
            # result, icon = self.classifier.predict(msg)
            result, icon = self.classifier.predict(msg)
            print("Chat Monitor result:", result)
            if result.strip().lower() in ["threat", "offensive"]:
                print("Calling show_threat_alert for chat monitor")
                self.after(0, lambda: self.show_threat_alert(f"{result} detected in chat message!", position="topleft"))
            repeat = 2 if result.lower() == "threat" else 1
            play_sound(result.lower(), repeat=repeat)
            if result != "Safe":
                result_label.config(text=f"{icon} Threat detected: {result}", fg="#ff6b6b")
            else:
                result_label.config(text="No threat detected.", fg="#51cf66")
            self.auth_manager.db.save_scan_result(
                self.current_user['user_id'], "chat_monitor", msg, result
            )

        entry.bind("<Return>", send_message)
        # Optionally, auto-analyze as user types (uncomment below for instant feedback)
        # def on_typing(event):
        #     msg = entry.get().strip()
        #     if msg:
        #         result, icon = self.classifier.predict(msg)
        #         if result != "Safe":
        #             result_label.config(text=f"{icon} Threat detected: {result}", fg="#ff6b6b")
        #         else:
        #             result_label.config(text="No threat detected.", fg="#51cf66")
        # entry.bind("<KeyRelease>", on_typing)

        self.current_frame = frame

    def show_file_scanner(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_text_analyzer_menu)
        self.style_back_button(back_btn)
        back_btn.config(width=10)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="File Scanner", font=("Segoe UI", 32, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=20)

        file_frame = tk.Frame(frame, bg=BG_FRAME)
        file_frame.pack(fill="both", expand=True, padx=50, pady=20)
        status_label = tk.Label(file_frame, text="", font=("Segoe UI", 12), bg=BG_FRAME, fg=LABEL_FG)
        status_label.pack(pady=(0, 10))
        result_box = tk.Text(file_frame, height=10, font=("Segoe UI", 12), bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", bd=5, state=tk.DISABLED)
        result_box.pack(fill="both", expand=True, pady=(0, 10))

        def select_and_scan():
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(filetypes=[("Text, PDF, DOCX", "*.txt *.pdf *.docx")])
            if not file_path:
                return
            status_label.config(text=f"Scanning: {file_path}")
            try:
                from utils.file_utils import extract_text_from_file
                text = extract_text_from_file(file_path)
                lines = text.splitlines()
                threshold = 2  # Number of threat/offensive words/phrases to flag line
                any_threat = False
                from model.text_model import TextThreatClassifier
                classifier = self.classifier if hasattr(self, 'classifier') else TextThreatClassifier()
                threat_lines = []
                offensive_lines = []
                safe_lines = []
                for line in lines:
                    highlights = classifier.extract_threat_offensive_words(line, threshold=0.2)
                    whole_line_threat = any(word == line and label == "Threat" for word, label in highlights)
                    whole_line_offensive = any(word == line and label == "Offensive" for word, label in highlights)
                    threat_count = sum(1 for _, label in highlights if label == "Threat")
                    offensive_count = sum(1 for _, label in highlights if label == "Offensive")
                    if whole_line_threat or threat_count >= threshold:
                        threat_lines.append(line)
                        any_threat = True
                    elif whole_line_offensive or offensive_count >= threshold:
                        offensive_lines.append(line)
                        any_threat = True
                    else:
                        safe_lines.append(line)
                # Print results in sections
                result_box.config(state=tk.NORMAL)
                result_box.delete(1.0, tk.END)
                result_box.insert(tk.END, "Threat:\n")
                for l in threat_lines:
                    result_box.insert(tk.END, l + "\n")
                result_box.insert(tk.END, "\nOffensive:\n")
                for l in offensive_lines:
                    result_box.insert(tk.END, l + "\n")
                result_box.insert(tk.END, "\nSafe:\n")
                for l in safe_lines:
                    result_box.insert(tk.END, l + "\n")
                result_box.config(state=tk.DISABLED)
                if any_threat:
                    self.show_popup("⚠️ Threat/Offensive", "Threat or offensive content detected in file!")
                    self.set_status("File scanned: Threat/Offensive content found")
                    play_sound("threat", repeat=2)
                else:
                    self.show_popup("✅ Safe", "File is Safe! No threat or offensive content detected.")
                    self.set_status("File scanned: Safe")
                    play_sound("safe")
                status_label.config(text="Scan complete.")
            except Exception as e:
                result_box.delete("1.0", tk.END)
                result_box.insert(tk.END, f"Error: {e}")
                self.set_status("Error scanning file.")

        scan_btn = tk.Button(file_frame, text="📁 Select and Scan File", command=select_and_scan, font=("Segoe UI", 14, "bold"), bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE_BG, activeforeground=BTN_ACTIVE_FG, relief="flat", bd=0, cursor="hand2", width=22, height=2)
        scan_btn.pack(pady=10)

        self.current_frame = frame

    def show_voice_analyzer(self):
        """Show the comprehensive voice analyzer interface"""
        print("DEBUG: show_voice_analyzer() called")
        from gui.voice_gui import create_voice_analyzer_gui
        
        self.clear_frame()
        print("DEBUG: Frame cleared")
        
        # Create main frame for voice analyzer
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        print("DEBUG: Main frame created and packed")
        
        # Back button
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_main_menu)
        self.style_back_button(back_btn)
        back_btn.config(width=10)
        back_btn.pack(anchor="nw", padx=20, pady=(20, 0))  # Remove extra bottom padding
        print("DEBUG: Back button created and packed")
        
        # Remove any black line or separator after the back button
        # (If there is a Frame, Label, or Canvas here, remove it)
        # Previously there may have been a separator here, now omitted
        
        # Create voice analyzer GUI in the frame
        print("DEBUG: About to call create_voice_analyzer_gui(frame, user_id)")
        user_id = self.current_user['user_id']
        voice_gui = create_voice_analyzer_gui(frame, user_id)
        print("DEBUG: create_voice_analyzer_gui() completed")
        
        # Store reference for cleanup
        self.voice_gui = voice_gui
        self.current_frame = frame
        print("DEBUG: Voice analyzer setup completed")

    def show_face_analyzer(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_main_menu)
        self.style_back_button(back_btn)
        back_btn.config(width=10)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="Face Analyzer", font=("Segoe UI", 32, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=20)

        face_frame = tk.Frame(frame, bg=BG_FRAME)
        face_frame.pack(fill="both", expand=True, padx=50, pady=20)
        tk.Label(face_frame, text="Analyze your facial emotion using your webcam.", font=("Segoe UI", 14), bg=BG_FRAME, fg=LABEL_FG).pack(pady=(0, 20))
        status_label = tk.Label(face_frame, text="", font=("Segoe UI", 12), bg=BG_FRAME, fg=LABEL_FG)
        status_label.pack(pady=(0, 10))
        result_label = tk.Label(face_frame, text="", font=("Segoe UI", 14, "bold"), bg=BG_FRAME, fg=LABEL_FG)
        result_label.pack(pady=(10, 0))

        def capture_and_analyze():
            import cv2
            import numpy as np
            status_label.config(text="Capturing image...")
            result_label.config(text="")
            try:
                cap = cv2.VideoCapture(0)
                ret, frame_img = cap.read()
                cap.release()
                if not ret:
                    status_label.config(text="Could not access webcam.")
                    return
                # Force result to 'Threat' for testing
                result, icon = "Threat", "❌"
                result_label.config(text=f"{icon} Analysis Result: {result}")
                self.auth_manager.db.save_scan_result(
                    self.current_user['user_id'], "face_analysis", "[face]", result
                )
                repeat = 2 if result.lower() == "threat" else 1
                play_sound(result.lower(), repeat=repeat)
                print("Face analysis result:", result)  # Debug
                if result.strip().lower() == "threat":
                    self.after(0, lambda: self.show_threat_alert("Threat detected in face analysis!", position="topleft"))
                status_label.config(text="Capture complete.")
            except Exception as e:
                status_label.config(text=f"Error: {e}")

        def show_webcam_mode():
            print("Webcam mode selected")
            # Real-time webcam monitoring using facial_emotion_analyzer
            try:
                import cv2
                from PIL import Image, ImageTk
                from facial_emotion_analyzer import FacialEmotionAnalyzer
            except Exception as e:
                messagebox.showerror("Dependency error", f"Required packages for webcam monitoring are missing: {e}")
                return

            # Create a toplevel window for live feed
            win = tk.Toplevel(self)
            win.title("Live Webcam Monitoring")
            win.geometry("900x700")
            win.configure(bg=BG_FRAME)
            win.protocol("WM_DELETE_WINDOW", lambda: stop_webcam())

            status_lbl = tk.Label(win, text="Initializing models...", bg=BG_FRAME, fg=LABEL_FG, font=("Segoe UI", 12))
            status_lbl.pack(anchor="nw", padx=10, pady=6)

            video_label = tk.Label(win, bg=BG_FRAME)
            video_label.pack(fill="both", expand=True, padx=10, pady=10)

            control_frame = tk.Frame(win, bg=BG_FRAME)
            control_frame.pack(fill="x", padx=10, pady=(0,10))
            stop_btn = tk.Button(control_frame, text="⏹ Stop", font=("Segoe UI", 12, "bold"), bg="#d9534f", fg="white", relief="flat", bd=0, cursor="hand2")
            stop_btn.pack(side="right")

            analyzer = FacialEmotionAnalyzer()
            analyzer.start_initialization()

            stop_event = threading.Event()

            def stop_webcam():
                stop_event.set()
                try:
                    win.destroy()
                except Exception:
                    pass

            stop_btn.config(command=stop_webcam)

            def webcam_loop():
                cap = None
                try:
                    cap = cv2.VideoCapture(0)
                    if not cap or not cap.isOpened():
                        self.after(0, lambda: messagebox.showerror("Webcam Error", "Could not open webcam"))
                        return
                    status = "Loading models..."
                    while not stop_event.is_set():
                        ret, frame = cap.read()
                        if not ret:
                            break
                        # Resize frame for performance
                        h, w = frame.shape[:2]
                        maxw = 900
                        if w > maxw:
                            scale = maxw / w
                            frame = cv2.resize(frame, (int(w*scale), int(h*scale)))

                        # If models ready, analyze; otherwise show loading text
                        annotations = []
                        if analyzer.is_initialized:
                            status = "Models loaded - running"
                            try:
                                results = analyzer.analyze_frame(frame)
                                for det in results:
                                    bbox = det.get('bbox')
                                    emotion = det.get('emotion')
                                    category = det.get('category')
                                    confidence = det.get('confidence', 0)
                                    emoji = det.get('emoji', '')
                                    if bbox:
                                        x, y, wbox, hbox = bbox
                                        annotations.append((x, y, wbox, hbox, f"{emoji} {emotion} {confidence:.2f}", category))
                            except Exception as _e:
                                print(f"[WARN] analysis error: {_e}")
                        else:
                            status = "Initializing models..."

                        # Draw annotations
                        vis = frame.copy()
                        for (x, y, ww, hh, label_text, category) in annotations:
                            color = (0,255,0) if category == 'Safe' else (0,165,255) if category == 'Offensive' else (0,0,255)
                            try:
                                cv2.rectangle(vis, (x, y), (x+ww, y+hh), color, 2)
                                cv2.putText(vis, label_text, (x, max(y-10,0)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                            except Exception:
                                pass

                        # Convert BGR to RGB and display
                        try:
                            vis_rgb = cv2.cvtColor(vis, cv2.COLOR_BGR2RGB)
                            img = Image.fromarray(vis_rgb)
                            imgtk = ImageTk.PhotoImage(image=img)
                            # UI update must run in main thread
                            self.after(0, lambda im=imgtk: video_label.configure(image=im) or setattr(video_label, 'imgtk', im))
                        except Exception as _e:
                            print(f"[WARN] display error: {_e}")

                        # Update status label
                        self.after(0, lambda s=status: status_lbl.config(text=s))

                        time.sleep(0.03)
                except Exception as e:
                    print(f"[ERROR] Webcam loop exception: {e}")
                    self.after(0, lambda: messagebox.showerror("Webcam Error", str(e)))
                finally:
                    try:
                        if cap:
                            cap.release()
                    except Exception:
                        pass

            threading.Thread(target=webcam_loop, daemon=True).start()
            return
            # Example: self.show_face_analyzer() # Recursive call to re-show the face analyzer

        def show_video_mode():
            print("Video file mode selected")
            # Implement video file analysis logic here
            # This would involve loading a video file and analyzing frames
            messagebox.showinfo("Face Analyzer", "Video file analysis mode is not yet fully implemented.")
            # Example: self.show_face_analyzer() # Recursive call to re-show the face analyzer

        def show_snapshot_mode():
            print("Snapshot mode selected")
            # Implement snapshot analysis logic here
            # This would involve taking a single image and analyzing it
            messagebox.showinfo("Face Analyzer", "Snapshot analysis mode is not yet fully implemented.")
            # Example: self.show_face_analyzer() # Recursive call to re-show the face analyzer

        # If OpenCV or Pillow are missing, present the user with a clear install message
        if HAS_OPENCV and HAS_PIL:
            webcam_btn = tk.Button(face_frame, text="🎥 Live Webcam Monitoring", command=show_webcam_mode, font=("Segoe UI", 14, "bold"), bg=BTN_BG, fg=BTN_FG, relief="flat", bd=0, cursor="hand2")
        else:
            def webcam_missing():
                missing = []
                if not HAS_OPENCV:
                    missing.append("opencv-python (cv2)")
                if not HAS_PIL:
                    missing.append("Pillow (PIL)")
                msg = (
                    "Live webcam analysis requires the following Python packages:\n\n"
                    + "\n".join(f"- {m}" for m in missing)
                    + "\n\nInstall inside your active virtual environment and restart the app:\n\n"
                    + "pip install opencv-python pillow"
                )
                messagebox.showerror("Missing dependencies", msg)
            webcam_btn = tk.Button(face_frame, text="🎥 Live Webcam Monitoring (install required)", command=webcam_missing, font=("Segoe UI", 14, "bold"), bg="#7f8c8d", fg="white", relief="flat", bd=0, cursor="hand2")
        webcam_btn.pack(pady=10, ipadx=20, ipady=8)
        video_btn = tk.Button(face_frame, text="🎬 Video File Analyzer", command=show_video_mode, font=("Segoe UI", 14, "bold"), bg=BTN_BG, fg=BTN_FG, relief="flat", bd=0, cursor="hand2")
        video_btn.pack(pady=10, ipadx=20, ipady=8)
        snapshot_btn = tk.Button(face_frame, text="🖼️ Snapshot (Image) Analyzer", command=show_snapshot_mode, font=("Segoe UI", 14, "bold"), bg=BTN_BG, fg=BTN_FG, relief="flat", bd=0, cursor="hand2")
        snapshot_btn.pack(pady=10, ipadx=20, ipady=8)

        self.current_frame = frame

    def show_url_scanner(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_main_menu)
        self.style_back_button(back_btn)
        back_btn.config(width=10)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="URL Scanner", font=("Segoe UI", 32, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=20)
        
        # URL input area
        input_frame = tk.Frame(frame, bg=BG_FRAME)
        input_frame.pack(fill="both", expand=True, padx=50, pady=20)
        
        tk.Label(input_frame, text="Enter URL to scan:", font=("Segoe UI", 16), bg=LABEL_BG, fg=LABEL_FG).pack(anchor="w", pady=(0, 10))
        
        url_entry = tk.Entry(input_frame, font=("Segoe UI", 12), bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", bd=10)
        url_entry.pack(fill="x", pady=(0, 20))
        url_entry.insert(0, "https://")
        
        # Buttons
        btn_frame = tk.Frame(input_frame, bg=BG_FRAME)
        btn_frame.pack(fill="x")
        
        def clear_url():
            url_entry.delete(0, tk.END)
            url_entry.insert(0, "https://")
        
        def scan_url():
            url = url_entry.get().strip()
            if not url or url == "https://":
                messagebox.showwarning("Warning", "Please enter a valid URL")
                return
            
            # Simple URL validation
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Analyze URL for threats
            threat_keywords = ['malware', 'phishing', 'scam', 'virus', 'hack', 'steal', 'password']
            url_lower = url.lower()
            
            threats_found = []
            for keyword in threat_keywords:
                if keyword in url_lower:
                    threats_found.append(keyword)
            
            if threats_found:
                result = "Threat"
                message = f"⚠️ POTENTIAL THREAT DETECTED!\n\nURL: {url}\n\nThreats found: {', '.join(threats_found)}\n\nThis URL contains suspicious keywords that may indicate a security threat."
            else:
                result = "Safe"
                message = f"✅ URL appears safe\n\nURL: {url}\n\nNo obvious threats detected in this URL."
            
            # Save to database if not demo user
            if self.current_user['user_id'] != 0:
                self.auth_manager.db.save_scan_result(
                    self.current_user['user_id'], 
                    "url_scan", 
                    url, 
                    result
                )
            
            # Show result
            self.show_popup(result, message)
            
            # Play sound
            repeat = 2 if result.lower() == "threat" else 1
            play_sound(result.lower(), repeat=repeat)
        
        clear_btn = tk.Button(btn_frame, text="🗑️ Clear", command=clear_url, font=("Segoe UI", 12, "bold"), bg="#6c757d", fg="white", activebackground="#5a6268", activeforeground="white", relief="flat", bd=0, cursor="hand2")
        clear_btn.pack(side="left", padx=(0, 10))
        
        scan_btn = tk.Button(btn_frame, text="🔍 Scan URL", command=scan_url, font=("Segoe UI", 12, "bold"), bg="#96ceb4", fg="white", activebackground="#7fb069", activeforeground="white", relief="flat", bd=0, cursor="hand2")
        scan_btn.pack(side="left")
        
        # Quick scan examples
        examples_frame = tk.Frame(input_frame, bg=BG_FRAME)
        examples_frame.pack(pady=30)
        
        tk.Label(examples_frame, text="Quick Scan Examples:", font=("Segoe UI", 14, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=(0, 10))
        
        examples = [
            ("google.com", "Safe example"),
            ("malware-test.com", "Threat example"),
            ("phishing-site.net", "Threat example")
        ]
        
        for url, desc in examples:
            example_frame = tk.Frame(examples_frame, bg=BG_FRAME)
            example_frame.pack(fill="x", pady=2)
            
            example_btn = tk.Button(
                example_frame, 
                text=f"🔗 {url}", 
                command=lambda u=url: url_entry.delete(0, tk.END) or url_entry.insert(0, u),
                font=("Segoe UI", 10),
                bg="#f8f9fa", 
                fg="#495057",
                relief="flat",
                bd=1,
                cursor="hand2"
            )
            example_btn.pack(side="left", padx=(0, 10))
            
            tk.Label(example_frame, text=f"- {desc}", font=("Segoe UI", 10), bg=LABEL_BG, fg=LABEL_FG).pack(side="left")
        
        self.current_frame = frame

    def show_text_manual(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_text_analyzer_menu)
        self.style_back_button(back_btn)
        back_btn.config(width=10)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="Manual Text Entry", font=("Segoe UI", 32, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=20)

        input_frame = tk.Frame(frame, bg=BG_FRAME)
        input_frame.pack(fill="both", expand=True, padx=50, pady=20)
        tk.Label(input_frame, text="Enter text or number to analyze:", font=("Segoe UI", 16), bg=LABEL_BG, fg=LABEL_FG).pack(anchor="w", pady=(0, 10))
        text_area = tk.Text(input_frame, height=6, font=("Segoe UI", 12), bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", bd=10)
        text_area.pack(fill="both", expand=True, pady=(0, 20))

        btn_frame = tk.Frame(input_frame, bg=BG_FRAME)
        btn_frame.pack(fill="x")
        result_label = tk.Label(input_frame, text="", font=("Segoe UI", 14, "bold"), bg=BG_FRAME, fg=LABEL_FG)
        result_label.pack(pady=(10, 0))

        def clear_text():
            text_area.delete(1.0, tk.END)
            result_label.config(text="")

        def analyze():
            import re
            user_input = text_area.get(1.0, tk.END).strip()
            if not user_input:
                messagebox.showwarning("Warning", "Please enter some text or a number.")
                return
            match = re.search(r"\d+", user_input)
            if match:
                found_number = match.group(0)
                def after_reentry(reentered):
                    if reentered == found_number:
                        self.show_safe_alert("Numbers match. No threat detected.")
                        result = "Safe"
                    else:
                        self.show_text_analyzer_popup_alert("Numbers do not match. Potential threat detected.")
                        result = "Threat"
                    self.auth_manager.db.save_scan_result(
                        self.current_user['user_id'], "text_manual", user_input, result
                    )
                    repeat = 2 if result.lower() == "threat" else 1
                    play_sound(result.lower(), repeat=repeat)
                self.show_number_reentry_alert_topleft(found_number, after_reentry)
                return
            # Otherwise, use normal threat analysis
            result, icon = self.classifier.predict(user_input)
            msg = f"{icon} Analysis Result: {result}\n\nText: {user_input[:200]}{'...' if len(user_input) > 200 else ''}"
            result_label.config(text=msg)
            self.auth_manager.db.save_scan_result(
                self.current_user['user_id'], "text_manual", user_input, result
            )
            repeat = 2 if result.lower() == "threat" else 1
            play_sound(result.lower(), repeat=repeat)
            if result.strip().lower() in ["threat", "offensive"]:
                self.show_text_analyzer_popup_alert(f"Given text is {result}")

        clear_btn = tk.Button(btn_frame, text="🗑️ Clear", command=clear_text, font=("Segoe UI", 12, "bold"), bg="#6c757d", fg="white", activebackground="#5a6268", activeforeground="white", relief="flat", bd=0, cursor="hand2")
        clear_btn.pack(side="left", padx=(0, 10))
        analyze_btn = tk.Button(btn_frame, text="🔍 Analyze", command=analyze, font=("Segoe UI", 12, "bold"), bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACTIVE_BG, activeforeground=BTN_ACTIVE_FG, relief="flat", bd=0, cursor="hand2")
        analyze_btn.pack(side="left")

        self.current_frame = frame

    def show_threat_alert(self, message, position="center"):
        print("show_threat_alert called with message:", message)
        popup = tk.Toplevel(self)
        popup.title("Threat Detected!")
        popup.geometry("400x250")
        popup.configure(bg="#2d2d44")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        popup.attributes('-topmost', True)
        popup.update_idletasks()
        if position == "topleft":
            x, y = 50, 50
        else:
            x = (popup.winfo_screenwidth() // 2) - (400 // 2)
            y = (popup.winfo_screenheight() // 2) - (250 // 2)
        popup.geometry(f"400x250+{x}+{y}")
        icon_label = tk.Label(popup, text="⚠️", font=("Segoe UI", 48), bg="#2d2d44", fg="#ff6b6b")
        icon_label.pack(pady=(20, 0))
        msg_label = tk.Label(popup, text=message, font=("Segoe UI", 16, "bold"), bg="#2d2d44", fg="#ff6b6b" , wraplength=360, justify="center")
        msg_label.pack(pady=(10, 0))
        ok_btn = tk.Button(popup, text="OK", command=popup.destroy, font=("Segoe UI", 12, "bold"), bg="#ff6b6b", fg="white", activebackground="#c82333", activeforeground="white", relief="flat", bd=0, cursor="hand2", width=10)
        ok_btn.pack(pady=20)
        # Ensure popup is always visible and focused
        popup.lift()
        popup.focus_force()
        popup.after(100, lambda: popup.deiconify())

    def show_safe_alert(self, message):
        popup = tk.Toplevel(self)
        popup.title("Safe")
        popup.geometry("400x200")
        popup.configure(bg="#2d2d44")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        popup.attributes('-topmost', True)
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (200 // 2)
        popup.geometry(f"400x200+{x}+{y}")
        # Removed icon_label (checkmark image)
        msg_label = tk.Label(popup, text=message, font=("Segoe UI", 16, "bold"), bg="#2d2d44", fg="#51cf66")
        msg_label.pack(pady=(60, 0))
        ok_btn = tk.Button(popup, text="OK", command=popup.destroy, font=("Segoe UI", 12, "bold"), bg="#51cf66", fg="white", activebackground="#388e3c", activeforeground="white", relief="flat", bd=0, cursor="hand2", width=10)
        ok_btn.pack(pady=20)

    def show_number_reentry_alert_topleft(self, found_number, on_submit):
        popup = tk.Toplevel(self)
        popup.title("Number Verification")
        popup.geometry("400x220")
        popup.configure(bg="#2d2d44")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        popup.attributes('-topmost', True)
        popup.update_idletasks()
        x, y = 50, 50
        popup.geometry(f"400x220+{x}+{y}")
        msg_label = tk.Label(popup, text=f"Please re-enter the number: {found_number}", font=("Segoe UI", 14), bg="#2d2d44", fg="#eebbc3")
        msg_label.pack(pady=(40, 0))
        entry = tk.Entry(popup, font=("Segoe UI", 16), bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", bd=5)
        entry.pack(pady=10)
        def submit():
            user_input = entry.get().strip()
            popup.destroy()
            on_submit(user_input)
        ok_btn = tk.Button(popup, text="OK", command=submit, font=("Segoe UI", 12, "bold"), bg="#ff6b6b", fg="white", activebackground="#c82333", activeforeground="white", relief="flat", bd=0, cursor="hand2", width=10)
        ok_btn.pack(pady=10)

    def on_exit(self):
        """Handle application exit"""
        # Cleanup voice GUI if it exists
        if hasattr(self, 'voice_gui'):
            self.voice_gui.cleanup()
        
        if self.session_token:
            self.auth_manager.logout_user(self.session_token)
        self.quit()

if __name__ == "__main__":
    app = CyberWatchApp()
    app.mainloop() 