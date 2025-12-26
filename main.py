import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import re
import threading
import os
import sys
import time
import winsound
from model.text_model import TextThreatClassifier
from utils.file_utils import extract_text_from_file


from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
import pickle

# Optional audio / ML libs may not be present in every environment. Import
# them defensively so the app can show helpful messages instead of failing
# to import at module import time (IDE linters also stop flagging errors).
try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    import soundfile as sf
except Exception:
    sf = None

try:
    import numpy as np
except Exception:
    np = None

try:
    import librosa
except Exception:
    librosa = None

try:
    from scipy.io.wavfile import write as scipy_write
except Exception:
    scipy_write = None

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
        self.current_frame = None
        self.classifier = TextThreatClassifier()
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self, textvariable=self.status_var, bd=1, relief="sunken", anchor="w", bg=BG_FRAME, fg=FG_MAIN, font=("Segoe UI", 11))
        self.status_bar.pack(side="bottom", fill="x")
        self.set_status("Welcome to Cyber Watch!")
        self.bind("<Control-q>", lambda e: self.on_exit())
        self.stop_scan_event = threading.Event()
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

    def show_main_menu(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        
        # Back to auth button
        back_btn = tk.Button(frame, text="⬅ Back to Auth", command=self.back_to_auth)
        self.style_back_button(back_btn)
        back_btn.config(width=15)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        
        tk.Label(
            frame, text="Cyber Watch", font=("Segoe UI", 40, "bold"),
            bg=LABEL_BG, fg=LABEL_FG
        ).pack(pady=40)
        btns = [
            ("📝 Text Analyzer", self.show_text_analyzer_menu, "Analyze text, files, and chats for threats"),
            ("😊 Face Analyzer", self.show_face_analyzer, "Detect your facial emotion"),
            ("🎤 Voice Analyzer", self.show_voice_analyzer, "Analyze voice for threats or emotion"),
        ]
        for text, cmd, tip in btns:
            btn = tk.Button(frame, text=text, width=30, height=2, command=cmd)
            self.style_button(btn)
            btn.pack(pady=18)
            self.add_tooltip(btn, tip)
        theme_btn = tk.Button(frame, text="🌗 Toggle Theme", command=self.toggle_theme)
        self.style_button(theme_btn)
        theme_btn.pack(pady=8)
        self.add_tooltip(theme_btn, "Switch between light and dark mode")
        self.current_frame = frame
    
    def back_to_auth(self):
        """Return to authentication system"""
        if messagebox.askyesno("Logout", "Do you want to logout and return to authentication?"):
            self.destroy()
            # Restart the launcher
            os.system(f"{sys.executable} launcher.py")

    def show_text_analyzer_menu(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_main_menu)
        self.style_back_button(back_btn)
        back_btn.config(width=10)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="Text Analyzer", font=("Segoe UI", 32, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=20)
        btns = [
            ("✅ Text Threat Analyzer", self.show_text_analyzer, "Analyze entered text for threats"),
            ("📧 Gmail Threat Scanner", self.show_gmail_scanner, "Scan your Gmail for threats"),
            ("💬 Chat Monitor", self.show_chat_monitor, "Monitor chat messages for threats"),
            ("📁 File Scanner", self.show_file_scanner, "Scan files for threats"),
        ]
        for text, cmd, tip in btns:
            btn = tk.Button(frame, text=text, width=30, height=2, command=cmd)
            self.style_button(btn)
            btn.pack(pady=12)
            self.add_tooltip(btn, tip)
        self.current_frame = frame

    # --- Text Threat Analyzer ---
    def show_text_analyzer(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_text_analyzer_menu)
        self.style_back_button(back_btn)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="Text Threat Analyzer", font=("Segoe UI", 28, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=10)
        text_box = scrolledtext.ScrolledText(frame, font=("Segoe UI", 14), width=80, height=10, bg=ENTRY_BG, fg=ENTRY_FG)
        text_box.pack(pady=10)
        result_box = tk.Label(frame, text="", font=("Segoe UI", 20, "bold"), width=40, height=2, bg="#fff")
        result_box.pack(pady=10)

        def clear_text():
            text_box.delete("1.0", tk.END)
            result_box.config(text="", bg="#fff")

        def analyze():
            try:
                self.set_status("Analyzing...")
                text = text_box.get("1.0", tk.END).strip()
                if not text:
                    messagebox.showwarning("Input Required", "Please enter some text.")
                    self.set_status("No text entered.")
                    return

                # Enhanced money detection patterns - more comprehensive
                money_patterns = [
                    r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
                    r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',   # ₹1,234.56
                    r'rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', # rs 1,234.56
                    r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|rupees?|rs)', # 1234.56 dollars
                    r'(?:transfer|payment|send|pay)\s+(?:me\s+)?(\d+(?:,\d{3})*(?:\.\d{2})?)', # transfer me 1234.56
                    r'(?:send|transfer|give)\s+(?:me\s+)?(\d+(?:,\d{3})*(?:\.\d{2})?)', # send me 1234.56
                    r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s+(?:immediately|now|urgently|asap)', # 1234.56 immediately
                    r'(?:amount|sum|money)\s+(?:of\s+)?(\d+(?:,\d{3})*(?:\.\d{2})?)', # amount of 1234.56
                    r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s+(?:to\s+)?(?:transfer|send|pay)', # 1234.56 to transfer
                ]
                
                money_found = None
                extracted_amount = None
                
                for pattern in money_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        money_found = match.group(0)  # Full match
                        extracted_amount = match.group(1)  # Just the amount
                        print(f"Money detected: {money_found} -> Amount: {extracted_amount}")  # Debug
                        break

                if money_found:
                    result_box.config(text="💰 Amount Detected", bg="#fff3cd", fg="#856404")
                    play_sound("offensive")
                    self.set_status(f"Amount detected: {extracted_amount}")
                    self.show_money_confirmation(frame, result_box, extracted_amount, money_found)
                    return
                else:
                    print(f"No money pattern matched for text: {text}")  # Debug

                label, emoji = self.classifier.predict(text)
                color = {"Safe": "#d4edda", "Offensive": "#ffe066", "Threat": "#f8d7da"}[label]
                fg = {"Safe": "#155724", "Offensive": "#856404", "Threat": "#721c24"}[label]
                result_box.config(text=f"{emoji} {label}", bg=color, fg=fg)
                sound_label = label.lower()
                repeat = 2 if label == "Threat" else 1
                play_sound(sound_label, repeat=repeat)
                self.set_status(f"Text analyzed: {label}")
                if label in ["Offensive", "Threat"]:
                    self.show_popup(f"{emoji} {label}", f"Detected: {label}")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
                self.set_status("Error during analysis.")

        btn = tk.Button(frame, text="Analyze", command=lambda: threading.Thread(target=analyze).start())
        self.style_button(btn)
        btn.pack(pady=10)

        clear_btn = tk.Button(frame, text="Clear", command=clear_text)
        self.style_button(clear_btn)
        clear_btn.pack(pady=10)

        self.add_tooltip(btn, "Analyze the entered text")
        self.current_frame = frame

    def show_money_confirmation(self, parent, result_box, amount, original_text):
        popup = tk.Toplevel(parent)
        popup.title("💰 Amount Verification Required")
        popup.configure(bg="#1a1a2e")
        popup.minsize(450, 300)
        popup.transient(self)
        popup.grab_set()
        
        # Modern UI styling
        main_frame = tk.Frame(popup, bg="#1a1a2e", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Header with icon
        header_frame = tk.Frame(main_frame, bg="#1a1a2e")
        header_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            header_frame,
            text="💰",
            font=("Segoe UI", 32),
            bg="#1a1a2e",
            fg="#ffd700"
        ).pack(side="left", padx=(0, 10))
        
        title_frame = tk.Frame(header_frame, bg="#1a1a2e")
        title_frame.pack(side="left", fill="y")
        
        tk.Label(
            title_frame,
            text="Amount Verification",
            font=("Segoe UI", 18, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        ).pack(anchor="w")
        
        tk.Label(
            title_frame,
            text="Please re-enter the detected amount to verify",
            font=("Segoe UI", 10),
            bg="#1a1a2e",
            fg="#a0a0a0"
        ).pack(anchor="w")
        
        # Original text display
        original_frame = tk.Frame(main_frame, bg="#16213e", relief="flat", bd=1)
        original_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            original_frame,
            text="Original Text:",
            font=("Segoe UI", 10, "bold"),
            bg="#16213e",
            fg="#4fc3f7"
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        text_display = tk.Label(
            original_frame,
            text=f'"{original_text}"',
            font=("Segoe UI", 11),
            bg="#16213e",
            fg="#ffffff",
            wraplength=400,
            justify="left"
        )
        text_display.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Detected amount
        amount_frame = tk.Frame(main_frame, bg="#0f3460", relief="flat", bd=1)
        amount_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            amount_frame,
            text="Detected Amount:",
            font=("Segoe UI", 10, "bold"),
            bg="#0f3460",
            fg="#4fc3f7"
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        tk.Label(
            amount_frame,
            text=f"${amount}" if amount else "Amount not clearly specified",
            font=("Segoe UI", 16, "bold"),
            bg="#0f3460",
            fg="#ffd700"
        ).pack(anchor="w", padx=10, pady=(0, 10))
        
        # Input section
        input_frame = tk.Frame(main_frame, bg="#1a1a2e")
        input_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            input_frame,
            text="Please re-enter the amount:",
            font=("Segoe UI", 12, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        ).pack(anchor="w", pady=(0, 5))
        
        entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 14),
            bg="#2d3748",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightcolor="#4fc3f7",
            highlightbackground="#4a5568"
        )
        entry.pack(fill="x", pady=(0, 10))
        entry.focus()
        
        # Status label
        status_label = tk.Label(
            input_frame,
            text="",
            font=("Segoe UI", 11),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        status_label.pack(anchor="w")
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg="#1a1a2e")
        button_frame.pack(fill="x", pady=(10, 0))
        
        def confirm():
            entered = entry.get().strip()
            if not entered:
                status_label.config(text="⚠️ Please enter an amount", fg="#ff9800")
                return
                
            # Clean and compare amounts
            entered_clean = re.sub(r'[^\d.]', '', entered)
            amount_clean = re.sub(r'[^\d.]', '', amount) if amount else ""
            
            if entered_clean == amount_clean:
                result_box.config(text="✅ Safe - Amount Verified", bg="#d4edda", fg="#155724")
                play_sound("safe")
                status_label.config(text="✅ Amount verified successfully!", fg="#28a745")
                self.set_status("Amount verified as safe.")
                popup.after(1500, popup.destroy)
            else:
                result_box.config(text="🚨 Threat - Amount Mismatch", bg="#f8d7da", fg="#721c24")
                play_sound("threat")
                status_label.config(text="❌ Amount mismatch detected!", fg="#dc3545")
                self.set_status("Amount mismatch! Threat detected.")
                self.show_popup("🚨 Threat", "Entered amount does not match the original. This could be a potential threat!")
                popup.after(1500, popup.destroy)

        def cancel():
            popup.destroy()
        
        # Modern styled buttons
        confirm_btn = tk.Button(
            button_frame,
            text="✅ Verify Amount",
            command=confirm,
            font=("Segoe UI", 12, "bold"),
            bg="#28a745",
            fg="#ffffff",
            activebackground="#218838",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        confirm_btn.pack(side="left", padx=(0, 10))
        
        cancel_btn = tk.Button(
            button_frame,
            text="❌ Cancel",
            command=cancel,
            font=("Segoe UI", 12, "bold"),
            bg="#6c757d",
            fg="#ffffff",
            activebackground="#5a6268",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        cancel_btn.pack(side="left")
        
        # Bind Enter key to confirm
        entry.bind("<Return>", lambda e: confirm())
        
        # Center the popup
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        
        popup.wait_window()

    def show_popup(self, label, message):
        popup = tk.Toplevel(self)
        popup.title(f"{label.capitalize()} Alert")
        popup.configure(bg=BG_FRAME)
        
        # --- UI Enhancements for Popups ---
        icon = ""
        bg_color = BG_FRAME
        fg_color = FG_MAIN
        btn_bg = BTN_BG
        btn_fg = BTN_FG
        btn_active_bg = BTN_ACTIVE_BG

        if "Offensive" in label:
            icon = "⚠️"
            bg_color = "#4A044E"  # Dark purple
            fg_color = "#F3E8FF"
            btn_bg = "#C026D3"
            btn_fg = "#FFFFFF"
            btn_active_bg = "#A21CAF"
        elif "Threat" in label:
            icon = "🚨"
            bg_color = "#7F1D1D"  # Dark red
            fg_color = "#FEE2E2"
            btn_bg = "#EF4444"
            btn_fg = "#FFFFFF"
            btn_active_bg = "#DC2626"
        
        popup.configure(bg=bg_color)
        popup.minsize(350, 150)

        title_text = f"{icon} {label.capitalize()} {icon}"
        title_label = tk.Label(popup, text=title_text, font=("Segoe UI", 18, "bold"), bg=bg_color, fg=fg_color)
        title_label.pack(pady=(15, 10))

        msg_label = tk.Label(popup, text=message, wraplength=380, justify="center", font=("Segoe UI", 12), bg=bg_color, fg=fg_color)
        msg_label.pack(pady=5, padx=20, expand=True, fill='both')
        
        ok_btn = tk.Button(
            popup, 
            text="Acknowledge", 
            command=popup.destroy, 
            width=15,
            bg=btn_bg,
            fg=btn_fg,
            activebackground=btn_active_bg,
            activeforeground=btn_fg,
            relief="flat",
            font=("Segoe UI", 12, "bold"),
            bd=0,
            pady=5
        )
        ok_btn.pack(pady=(10, 15))
        
        popup.transient(self)
        popup.grab_set()
        
        # Center the popup
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        
        self.wait_window(popup)

    # --- Gmail Threat Scanner ---
    def show_gmail_scanner(self):
        from tkinter import ttk
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_text_analyzer_menu)
        self.style_back_button(back_btn)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="Gmail Threat Scanner", font=("Segoe UI", 28, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=10)

        entry_frame = tk.Frame(frame, bg=BG_FRAME)
        entry_frame.pack(pady=5)
        tk.Label(entry_frame, text="Number of emails to scan (or 'all'):", font=("Segoe UI", 12), bg=BG_FRAME, fg=FG_MAIN).pack(side="left")
        num_emails_var = tk.StringVar(value="10")
        num_emails_entry = tk.Entry(entry_frame, textvariable=num_emails_var, width=8, font=("Segoe UI", 12), bg=ENTRY_BG, fg=ENTRY_FG)
        num_emails_entry.pack(side="left", padx=5)

        tk.Label(entry_frame, text="Area:", font=("Segoe UI", 12), bg=BG_FRAME, fg=FG_MAIN).pack(side="left", padx=(10,0))
        area_var = tk.StringVar(value="All")
        area_combo = ttk.Combobox(entry_frame, textvariable=area_var, values=["All", "Read", "Unread"], state="readonly", width=8)
        area_combo.pack(side="left", padx=5)

        result_box = scrolledtext.ScrolledText(frame, font=("Segoe UI", 12), width=100, height=20, bg=ENTRY_BG, fg=ENTRY_FG)
        result_box.pack(pady=10)

        def scan_gmail():
            try:
                self.set_status("Scanning Gmail...")
                num_val = num_emails_var.get().strip().lower()
                area = area_var.get().lower()
                max_results = None
                if num_val != "all":
                    try:
                        max_results = int(num_val)
                        if max_results <= 0:
                            raise ValueError
                    except ValueError:
                        messagebox.showerror("Invalid Input", "Please enter a valid positive number or 'all'.")
                        return

                SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
                creds = None
                token_path = 'token.pickle'
                credentials_path = 'credentials.json'
                if os.path.exists(token_path ):
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
                service = build('gmail', 'v1', credentials=creds)
                query = ""
                if area == "read":
                    query = "is:read"
                elif area == "unread":
                    query = "is:unread"

                result_box.delete("1.0", tk.END)
                messages = []
                next_page_token = None
                while True:
                    params = {'userId': 'me', 'q': query}
                    if max_results:
                        params['maxResults'] = min(max_results - len(messages), 500)
                    if next_page_token:
                        params['pageToken'] = next_page_token
                    results = service.users().messages().list(**params).execute()
                    batch = results.get('messages', [])
                    messages.extend(batch)
                    next_page_token = results.get('nextPageToken')
                    if not next_page_token or (max_results and len(messages) >= max_results):
                        break
                if not messages:
                    result_box.insert(tk.END, "No emails found.")
                    return

                for i, msg in enumerate(messages):
                    if self.stop_scan_event.is_set():
                        result_box.insert(tk.END, "\nScan stopped by user.\n")
                        self.set_status("Gmail scan stopped.")
                        self.stop_scan_event.clear()
                        return

                    msg_id = msg["id"]
                    try:
                        full_message = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
                        payload = full_message["payload"]
                        headers = payload.get("headers", [])
                        subject = ""
                        sender = ""
                        for header in headers:
                            if header["name"] == "Subject":
                                subject = header["value"]
                            if header["name"] == "From":
                                sender = header["value"]

                        parts = payload.get("parts", [])
                        body = ""
                        if parts:
                            for part in parts:
                                if part["mimeType"] == "text/plain":
                                    body_data = part["body"].get("data", "")
                                    body = base64.urlsafe_b64decode(body_data).decode("utf-8")
                                    break
                        else:
                            body_data = payload["body"].get("data", "")
                            body = base64.urlsafe_b64decode(body_data).decode("utf-8")

                        full_text = f"Subject: {subject}\nFrom: {sender}\nBody: {body}"
                        label, emoji = self.classifier.predict(full_text)
                        display_text = f"Email {i+1}: Subject: {subject[:70]}... | From: {sender[:70]}... | Status: {emoji} {label}\n"
                        result_box.insert(tk.END, display_text)
                        result_box.see(tk.END)
                        if label in ["Offensive", "Threat"]:
                            play_sound(label.lower())
                            self.show_popup(f"{emoji} {label}", f"Threat detected in email from {sender} with subject: {subject}")

                    except Exception as e:
                        result_box.insert(tk.END, f"Error processing email {msg_id}: {e}\n")
                        result_box.see(tk.END)

                self.set_status("Gmail scan complete.")
                self.stop_scan_event.clear()
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred during Gmail scan: {e}")
                self.set_status("Error during Gmail scan.")
                self.stop_scan_event.clear()

        scan_btn = tk.Button(frame, text="Scan Gmail", command=lambda: threading.Thread(target=scan_gmail).start())
        self.style_button(scan_btn)
        scan_btn.pack(pady=10)
        self.add_tooltip(scan_btn, "Scan your Gmail inbox for threats")

        stop_btn = tk.Button(frame, text="Stop Scan", command=self.stop_scan_event.set)
        self.style_button(stop_btn)
        stop_btn.pack(pady=10)

        def copy_results():
            self.clipboard_clear()
            self.clipboard_append(result_box.get("1.0", tk.END))
            self.set_status("Results copied to clipboard.")

        copy_btn = tk.Button(frame, text="Copy Results", command=copy_results)
        self.style_button(copy_btn)
        copy_btn.pack(pady=5)

        self.current_frame = frame

    # --- Chat Monitor ---
    def show_chat_monitor(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_text_analyzer_menu)
        self.style_back_button(back_btn)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="Chat Monitor", font=("Segoe UI", 28, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=10)
        chat_box = scrolledtext.ScrolledText(frame, font=("Segoe UI", 12), width=80, height=10, bg=ENTRY_BG, fg=ENTRY_FG)
        chat_box.pack(pady=10)
        result_box = scrolledtext.ScrolledText(frame, font=("Segoe UI", 12), width=80, height=10, bg=ENTRY_BG, fg=ENTRY_FG)
        result_box.pack(pady=10)

        def clear_chat():
            chat_box.delete("1.0", tk.END)
            result_box.delete("1.0", tk.END)

        def analyze_chat():
            try:
                self.set_status("Analyzing chat...")
                text = chat_box.get("1.0", tk.END).strip()
                if not text:
                    messagebox.showwarning("Input Required", "Please enter chat messages.")
                    self.set_status("No chat entered.")
                    return
                lines = text.splitlines()
                result_box.delete("1.0", tk.END)
                for line in lines:
                    label, emoji = self.classifier.predict(line)
                    color = {"Safe": "green", "Offensive": "orange", "Threat": "red"}[label]
                    result_box.insert(tk.END, f"{emoji} {label}: {line}\n", color)
                    play_sound(label.lower())
                result_box.tag_config("green", foreground="green")
                result_box.tag_config("orange", foreground="orange")
                result_box.tag_config("red", foreground="red")
                result_box.see(tk.END)
                self.set_status("Chat scan complete.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
                self.set_status("Error during chat analysis.")

        btn = tk.Button(frame, text="Analyze Chat", command=lambda: threading.Thread(target=analyze_chat).start())
        self.style_button(btn)
        btn.pack(pady=10)

        clear_btn = tk.Button(frame, text="Clear", command=clear_chat)
        self.style_button(clear_btn)
        clear_btn.pack(pady=10)

        self.add_tooltip(btn, "Analyze chat messages for threats")
        self.current_frame = frame

    # --- File Scanner ---
    def show_file_scanner(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_text_analyzer_menu)
        self.style_back_button(back_btn)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="File Scanner", font=("Segoe UI", 28, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=20)

        result_box = scrolledtext.ScrolledText(frame, font=("Segoe UI", 12), width=100, height=20, bg=ENTRY_BG, fg=ENTRY_FG)
        result_box.pack(pady=10)

        def select_and_scan():
            try:
                self.set_status("Scanning file...")
                file_path = filedialog.askopenfilename(
                    filetypes=[
                        ("All Supported", "*.txt *.pdf *.docx"),
                        ("Text files", "*.txt"),
                        ("PDF files", "*.pdf"),
                        ("Word files", "*.docx"),
                        ("All files", "*.*"),
                    ]
                )
                if not file_path:
                    self.set_status("No file selected.")
                    return
                text = extract_text_from_file(file_path)
                lines = text.splitlines()
                result_box.delete("1.0", tk.END)
                result_box.insert(tk.END, f"File: {os.path.basename(file_path)}\n", "bold")
                result_box.insert(tk.END, "--- File Content Preview ---\n\n")
                threat_found = False
                for line in lines:
                    label, emoji = self.classifier.predict(line)
                    if label == "Threat":
                        result_box.insert(tk.END, line + "\n", "threat_bg")
                        threat_found = True
                    elif label == "Offensive":
                        result_box.insert(tk.END, line + "\n", "offensive_bg")
                        threat_found = True
                    else:
                        result_box.insert(tk.END, line + "\n")
                result_box.tag_config("bold", font=("Segoe UI", 12, "bold"))
                result_box.tag_config("threat_bg", background="#ffcccc", foreground="#b20000")
                result_box.tag_config("offensive_bg", background="#ffe5b4", foreground="#b26a00")
                result_box.see(tk.END)
                # Play sound and show popup if any threat/offensive found
                if threat_found:
                    self.show_popup("⚠️ Threat/Offensive", "Threat or offensive content detected in file! Highlighted in red/orange.")
                    self.set_status("File scanned: Threat/Offensive content found")
                    play_sound("threat", repeat=2)
                else:
                    self.show_popup("✅ Safe", "File is Safe! No threat or offensive content detected.")
                    self.set_status("File scanned: Safe")
                    play_sound("safe")
            except Exception as e:
                result_box.delete("1.0", tk.END)
                result_box.insert(tk.END, f"Error: {e}")
                self.set_status("Error scanning file.")

        btn = tk.Button(frame, text="Select and Scan File", command=lambda: threading.Thread(target=select_and_scan).start())
        self.style_button(btn)
        btn.pack(pady=10)
        self.add_tooltip(btn, "Select a file and scan for threats")

        def copy_results():
            self.clipboard_clear()
            self.clipboard_append(result_box.get("1.0", tk.END))
            self.set_status("Results copied to clipboard.")

        copy_btn = tk.Button(frame, text="Copy Results", command=copy_results)
        self.style_button(copy_btn)
        copy_btn.pack(pady=5)

        self.current_frame = frame

    # --- Face Analyzer ---
    def show_face_analyzer(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)
        back_btn = tk.Button(frame, text="⬅ Back", command=self.show_main_menu)
        self.style_back_button(back_btn)
        back_btn.pack(anchor="nw", padx=20, pady=20)
        tk.Label(frame, text="Face Analyzer", font=("Segoe UI", 32, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=20)
        tk.Label(frame, text="Select Face Analysis Mode", font=("Segoe UI", 18, "bold"), bg=LABEL_BG, fg=LABEL_FG).pack(pady=10)
        webcam_btn = tk.Button(frame, text="🎥 Live Webcam Monitoring", command=self.show_webcam_mode, font=("Segoe UI", 14, "bold"), bg=BTN_BG, fg=BTN_FG, relief="flat", bd=0, cursor="hand2")
        webcam_btn.pack(pady=10, ipadx=20, ipady=8)
        video_btn = tk.Button(frame, text="🎬 Video File Analyzer", command=self.show_video_mode, font=("Segoe UI", 14, "bold"), bg=BTN_BG, fg=BTN_FG, relief="flat", bd=0, cursor="hand2")
        video_btn.pack(pady=10, ipadx=20, ipady=8)
        snapshot_btn = tk.Button(frame, text="🖼️ Snapshot (Image) Analyzer", command=self.show_snapshot_mode, font=("Segoe UI", 14, "bold"), bg=BTN_BG, fg=BTN_FG, relief="flat", bd=0, cursor="hand2")
        snapshot_btn.pack(pady=10, ipadx=20, ipady=8)
        
        self.current_frame = frame

    # --- Voice Analyzer ---
    def show_voice_analyzer(self):
        self.clear_frame()
        frame = tk.Frame(self, bg=BG_FRAME)
        frame.pack(fill="both", expand=True)

        # Use legacy compact UI for voice analyzer
        try:
            from gui.voice_gui import create_legacy_voice_analyzer_gui
            create_legacy_voice_analyzer_gui(frame)
        except Exception as e:
            # Fallback to previous rich UI if legacy constructor fails
            print(f"Failed to create legacy voice UI: {e}")
            # Back button (consistent with other screens)
            back_btn = tk.Button(frame, text="⬅ Back", command=self.show_main_menu)
            self.style_back_button(back_btn)
            back_btn.pack(anchor="nw", padx=20, pady=20)

            # Title
            tk.Label(frame, text="🎤 Voice Threat Analyzer", font=("Segoe UI", 32, "bold"), 
                bg=LABEL_BG, fg=LABEL_FG).pack(pady=20)
            
            # Subtitle
            tk.Label(frame, text="Detect emotional distress, threats, or scam attempts in voice", 
                font=("Segoe UI", 14), bg=LABEL_BG, fg=LABEL_FG).pack(pady=(0, 30))
            
            # Create notebook for different voice analysis modes
            notebook = ttk.Notebook(frame)
            notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            
            # Tab 1: Voice Chat Monitor
            chat_frame = tk.Frame(notebook, bg=BG_FRAME)
            notebook.add(chat_frame, text="💬 Voice Chat Monitor")
            self.create_voice_chat_tab(chat_frame)
            
            # Tab 2: Voice Call Scanner
            call_frame = tk.Frame(notebook, bg=BG_FRAME)
            notebook.add(call_frame, text="📞 Voice Call Scanner")
            self.create_voice_call_tab(call_frame)
            
            # Tab 3: Voice File Scanner
            file_frame = tk.Frame(notebook, bg=BG_FRAME)
            notebook.add(file_frame, text="📁 Voice File Scanner")
            self.create_voice_file_tab(file_frame)
            
            # Tab 4: Live Mic Monitor
            live_frame = tk.Frame(notebook, bg=BG_FRAME)
            notebook.add(live_frame, text="🎙️ Live Mic Monitor")
            self.create_live_mic_tab(live_frame)
            
            # Tab 5: Real-time Alert System
            alert_frame = tk.Frame(notebook, bg=BG_FRAME)
            notebook.add(alert_frame, text="🚨 Real-time Alerts")
            self.create_alert_system_tab(alert_frame)
        
        self.current_frame = frame

    def create_voice_chat_tab(self, parent):
        """Create voice chat monitoring tab with all required buttons and features"""
        import csv
        import webbrowser
        # Use top-level sound libs if available, otherwise try local import; fall back to None
        try:
            sd_local = sd if 'sd' in globals() and sd is not None else __import__('sounddevice')
        except Exception:
            sd_local = None
        try:
            sf_local = sf if 'sf' in globals() and sf is not None else __import__('soundfile')
        except Exception:
            sf_local = None
        # Instructions
        tk.Label(parent, text="Monitor short voice clips (WhatsApp, Telegram, etc.)", 
                font=("Segoe UI", 12), bg=LABEL_BG, fg=LABEL_FG).pack(pady=10)
        
        # Status and result labels
        status_label = tk.Label(parent, text="Ready to analyze voice clips", 
                               font=("Segoe UI", 12), bg=LABEL_BG, fg=FG_MAIN)
        status_label.pack(pady=10)
        
        result_label = tk.Label(parent, text="", font=("Segoe UI", 16, "bold"), 
                               bg=BG_FRAME, fg=FG_MAIN)
        result_label.pack(pady=10)
        
        # Result history/log
        tk.Label(parent, text="Result History:", font=("Segoe UI", 10, "bold"), bg=BG_FRAME, fg=FG_MAIN).pack(anchor=tk.W, padx=20)
        log_frame = tk.Frame(parent, bg=BG_FRAME)
        log_frame.pack(padx=20, pady=(0, 10), fill="x")
        self.voice_chat_log = tk.Listbox(log_frame, font=("Consolas", 10), height=6, width=80, bg=ENTRY_BG, fg=ENTRY_FG, selectmode=tk.SINGLE)
        self.voice_chat_log.pack(side=tk.LEFT, fill="x", expand=True)
        log_scroll = tk.Scrollbar(log_frame, orient="vertical", command=self.voice_chat_log.yview)
        log_scroll.pack(side=tk.RIGHT, fill="y")
        self.voice_chat_log.config(yscrollcommand=log_scroll.set)
        self.voice_chat_log_data = []
        
        # Play audio on log double-click
        def play_selected_log(event=None):
            try:
                idx = self.voice_chat_log.curselection()
                if not idx:
                    return
                entry = self.voice_chat_log_data[idx[0]]
                file_path = entry['file_path']
                if not os.path.exists(file_path):
                    messagebox.showerror("File Not Found", f"Audio file not found: {file_path}")
                    return
                if not sf_local or not sd_local:
                    messagebox.showwarning("Playback Unavailable", "Required audio libraries (soundfile/sounddevice) are not available.")
                    return
                data, samplerate = sf_local.read(file_path)
                sd_local.play(data, samplerate)
                sd_local.wait()
            except Exception as e:
                messagebox.showerror("Playback Error", f"Could not play audio: {e}")
        self.voice_chat_log.bind('<Double-1>', play_selected_log)
        
        # Delete log entry
        def delete_selected_log():
            idx = self.voice_chat_log.curselection()
            if not idx:
                return
            self.voice_chat_log.delete(idx)
            del self.voice_chat_log_data[idx[0]]
        delete_btn = tk.Button(parent, text="🗑️ Delete Entry", command=delete_selected_log)
        self.style_button(delete_btn)
        delete_btn.pack(pady=2)
        self.add_tooltip(delete_btn, "Delete selected log entry")
        
        # Clear log
        def clear_log():
            self.voice_chat_log.delete(0, tk.END)
            self.voice_chat_log_data.clear()
        clear_btn = tk.Button(parent, text="🧹 Clear Log", command=clear_log)
        self.style_button(clear_btn)
        clear_btn.pack(pady=2)
        self.add_tooltip(clear_btn, "Clear all log entries")
        
        # Export log
        def export_log():
            if not self.voice_chat_log_data:
                messagebox.showinfo("Export Log", "No log entries to export.")
                return
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
            if not file_path:
                return
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=["timestamp", "label", "emoji", "confidence", "filename", "file_path"])
                    writer.writeheader()
                    for entry in self.voice_chat_log_data:
                        writer.writerow(entry)
                messagebox.showinfo("Export Log", f"Log exported to {file_path}")
                webbrowser.open(file_path)
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export log: {e}")
        export_btn = tk.Button(parent, text="💾 Export Log", command=export_log)
        self.style_button(export_btn)
        export_btn.pack(pady=2)
        self.add_tooltip(export_btn, "Export log as CSV file")
        
        # Progress bar for batch analysis
        progress_var = tk.DoubleVar(value=0)
        progress_bar = ttk.Progressbar(parent, variable=progress_var, maximum=100)
        progress_bar.pack(fill="x", padx=20, pady=5)
        progress_bar.pack_forget()
        
        # Record button
        def quick_record():
            try:
                if not sd_local:
                    messagebox.showwarning("Recording Unavailable", "sounddevice library not available; cannot record.")
                    return
                from scipy.io.wavfile import write
                status_label.config(text="Recording voice clip (10 seconds)...")
                self.set_status("Recording voice clip...")
                samplerate = 16000
                duration = 10
                recording = sd_local.rec(int(samplerate * duration), samplerate=samplerate, channels=1)
                sd_local.wait()
                filename = f"voice_chat_{int(time.time())}.wav"
                write(filename, samplerate, recording)
                status_label.config(text="Voice clip recorded. Analyzing...")
                self.analyze_voice_file_with_log(filename, result_label, status_label)
            except Exception as e:
                messagebox.showerror("Error", f"Recording failed: {e}")
                self.set_status("Recording failed.")
        record_btn = tk.Button(parent, text="🎙️ Record Voice Clip (10s)", command=lambda: threading.Thread(target=quick_record).start())
        self.style_button(record_btn)
        record_btn.pack(pady=5)
        self.add_tooltip(record_btn, "Record a short voice clip for analysis")
        
        # Browse button
        def browse_and_analyze():
            file_path = filedialog.askopenfilename(
                title="Select Audio File",
                filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg"), ("All files", "*.*")]
            )
            if file_path:
                status_label.config(text="Analyzing selected audio file...")
                self.analyze_voice_file_with_log(file_path, result_label, status_label)
        browse_btn = tk.Button(parent, text="📁 Browse and Analyze Audio File", command=browse_and_analyze)
        self.style_button(browse_btn)
        browse_btn.pack(pady=5)
        self.add_tooltip(browse_btn, "Upload and analyze any audio file")
        
        # Batch Analyze button
        def batch_analyze():
            file_paths = filedialog.askopenfilenames(
                title="Select Audio Files for Batch Analysis",
                filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg"), ("All files", "*.*")]
            )
            if file_paths:
                progress_bar.pack(fill="x", padx=20, pady=5)
                progress_var.set(0)
                status_label.config(text=f"Batch analyzing {len(file_paths)} files...")
                self.set_status(f"Batch analyzing {len(file_paths)} files...")
                for i, file_path in enumerate(file_paths):
                    try:
                        self.analyze_voice_file_with_log(file_path, result_label, status_label)
                    except Exception as e:
                        messagebox.showerror("Batch Analysis Error", f"Error analyzing {file_path}: {e}")
                    progress_var.set((i + 1) / len(file_paths) * 100)
                    parent.update_idletasks()
                status_label.config(text="Batch analysis complete.")
                self.set_status("Batch analysis complete.")
                progress_bar.pack_forget()
        batch_btn = tk.Button(parent, text="🗂️ Batch Analyze Files", command=batch_analyze)
        self.style_button(batch_btn)
        batch_btn.pack(pady=5)
        self.add_tooltip(batch_btn, "Select and analyze multiple audio files at once")

    def analyze_voice_file_with_log(self, file_path, result_label, status_label):
        """Analyze voice file and log the result in the Voice Chat Monitor tab"""
        import datetime
        try:
            from model.voice_model import VoiceThreatClassifier
            classifier = VoiceThreatClassifier()
            label, emoji, confidence = classifier.predict(file_path, fast_mode=True)
            result_label.config(text=f"Detected: {emoji} {label}\nConfidence: {confidence:.2f}%")
            play_sound(label.lower())
            if label in ["Threat", "Offensive"]:
                self.show_popup(f"{emoji} {label}", f"Voice Analysis: {label} detected!\nConfidence: {confidence:.1f}%")
            status_label.config(text="Analysis complete")
            self.set_status(f"Voice analyzed: {label} ({confidence:.1f}%)")
            # Log the result
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                "timestamp": timestamp,
                "label": label,
                "emoji": emoji,
                "confidence": f"{confidence:.2f}",
                "filename": os.path.basename(file_path),
                "file_path": file_path
            }
            self.voice_chat_log.insert(0, f"[{timestamp}] {emoji} {label} (Confidence: {confidence:.2f}) - {os.path.basename(file_path)}")
            self.voice_chat_log_data.insert(0, log_entry)
        except Exception as e:
            result_label.config(text="❌ Analysis Failed")
            status_label.config(text=f"Error: {str(e)}")
            self.set_status("Voice analysis failed")
            messagebox.showerror("Analysis Error", f"Could not analyze file: {e}")

    def create_voice_call_tab(self, parent):
        """Create voice call scanning tab"""
        # Instructions
        tk.Label(parent, text="Scan recorded call files (MP3/WAV)", 
                font=("Segoe UI", 12), bg=LABEL_BG, fg=LABEL_FG).pack(pady=10)
        
        # File selection
        file_frame = tk.Frame(parent, bg=BG_FRAME)
        file_frame.pack(fill="x", padx=20, pady=10)
        
        self.call_file_var = tk.StringVar()
        file_entry = tk.Entry(file_frame, textvariable=self.call_file_var, 
                             font=("Segoe UI", 10), bg=ENTRY_BG, fg=ENTRY_FG, 
                             relief="flat", bd=10)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        def browse_call_file():
            file_path = filedialog.askopenfilename(
                title="Select Call Recording",
                filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac"), ("All files", "*.*")]
            )
            if file_path:
                self.call_file_var.set(file_path)
        
        browse_btn = tk.Button(file_frame, text="📁 Browse", command=browse_call_file,
                              font=("Segoe UI", 10, "bold"), bg=BTN_BG, fg=BTN_FG,
                              relief="flat", bd=0, cursor="hand2", padx=15)
        browse_btn.pack(side=tk.RIGHT)
        
        # Status and result labels
        call_status_label = tk.Label(parent, text="Select a call recording file", 
                                    font=("Segoe UI", 12), bg=LABEL_BG, fg=FG_MAIN)
        call_status_label.pack(pady=10)
        
        call_result_label = tk.Label(parent, text="", font=("Segoe UI", 16, "bold"), 
                                    bg=BG_FRAME, fg=FG_MAIN)
        call_result_label.pack(pady=10)
        
        # Analyze button
        def analyze_call():
            file_path = self.call_file_var.get()
            if not file_path:
                messagebox.showwarning("No File", "Please select a call recording file.")
                return
            if not os.path.exists(file_path):
                messagebox.showerror("File Not Found", "Selected file does not exist.")
                return
            
            call_status_label.config(text="Analyzing call recording...")
            self.analyze_voice_file(file_path, call_result_label, call_status_label)
        
        analyze_btn = tk.Button(parent, text="🔍 Analyze Call Recording", 
                               command=lambda: threading.Thread(target=analyze_call).start())
        self.style_button(analyze_btn)
        analyze_btn.pack(pady=10)
        self.add_tooltip(analyze_btn, "Analyze the selected call recording for threats")

    def create_voice_file_tab(self, parent):
        """Create voice file scanning tab"""
        # Instructions
        tk.Label(parent, text="Upload and analyze audio files", 
                font=("Segoe UI", 12), bg=LABEL_BG, fg=LABEL_FG).pack(pady=10)
        
        # File selection
        file_frame = tk.Frame(parent, bg=BG_FRAME)
        file_frame.pack(fill="x", padx=20, pady=10)
        
        self.audio_file_var = tk.StringVar()
        file_entry = tk.Entry(file_frame, textvariable=self.audio_file_var, 
                             font=("Segoe UI", 10), bg=ENTRY_BG, fg=ENTRY_FG, 
                             relief="flat", bd=10)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        def browse_audio_file():
            file_path = filedialog.askopenfilename(
                title="Select Audio File",
                filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg"), ("All files", "*.*")]
            )
            if file_path:
                self.audio_file_var.set(file_path)
        
        browse_btn = tk.Button(file_frame, text="📁 Browse", command=browse_audio_file,
                              font=("Segoe UI", 10, "bold"), bg=BTN_BG, fg=BTN_FG,
                              relief="flat", bd=0, cursor="hand2", padx=15)
        browse_btn.pack(side=tk.RIGHT)
        
        # Analysis options
        options_frame = tk.Frame(parent, bg=BG_FRAME)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        self.fast_mode_var = tk.BooleanVar(value=False)
        fast_check = tk.Checkbutton(options_frame, text="⚡ Fast Mode (skip deep analysis)", 
                                   variable=self.fast_mode_var, font=("Segoe UI", 10),
                                   bg=BG_FRAME, fg=FG_MAIN, selectcolor=BG_FRAME,
                                   activebackground=BG_FRAME, activeforeground=FG_MAIN)
        fast_check.pack(anchor=tk.W)
        
        # Status and result labels
        file_status_label = tk.Label(parent, text="Select an audio file to analyze", 
                                    font=("Segoe UI", 12), bg=LABEL_BG, fg=FG_MAIN)
        file_status_label.pack(pady=10)
        
        file_result_label = tk.Label(parent, text="", font=("Segoe UI", 16, "bold"), 
                                    bg=BG_FRAME, fg=FG_MAIN)
        file_result_label.pack(pady=10)
        
        # Analyze button
        def analyze_audio_file():
            file_path = self.audio_file_var.get()
            if not file_path:
                messagebox.showwarning("No File", "Please select an audio file.")
                return
            if not os.path.exists(file_path):
                messagebox.showerror("File Not Found", "Selected file does not exist.")
                return
            
            file_status_label.config(text="Analyzing audio file...")
            self.analyze_voice_file(file_path, file_result_label, file_status_label, 
                                  fast_mode=self.fast_mode_var.get())
        
        analyze_btn = tk.Button(parent, text="🔍 Analyze Audio File", 
                               command=lambda: threading.Thread(target=analyze_audio_file).start())
        self.style_button(analyze_btn)
        analyze_btn.pack(pady=10)
        self.add_tooltip(analyze_btn, "Analyze the selected audio file for threats")

    def create_live_mic_tab(self, parent):
        """Create live microphone monitoring tab with all required controls and real-time analysis"""
        # Prefer top-level sound libs if available, otherwise try local import; fall back to None
        try:
            sd_local = sd if 'sd' in globals() and sd is not None else __import__('sounddevice')
        except Exception:
            sd_local = None
        try:
            sf_local = sf if 'sf' in globals() and sf is not None else __import__('soundfile')
        except Exception:
            sf_local = None
        # Instructions
        tk.Label(parent, text="Real-time threat detection from microphone", 
                font=("Segoe UI", 12), bg=LABEL_BG, fg=LABEL_FG).pack(pady=10)
        
        # Microphone device selector
        device_frame = tk.Frame(parent, bg=BG_FRAME)
        device_frame.pack(pady=5)
        tk.Label(device_frame, text="Select Microphone:", font=("Segoe UI", 10), bg=BG_FRAME, fg=FG_MAIN).pack(side=tk.LEFT)
        # Query devices defensively
        input_devices = []
        if sd_local:
            try:
                devices = sd_local.query_devices()
                input_devices = [(i, d.get('name', f'Device {i}')) for i, d in enumerate(devices) if d.get('max_input_channels', 0) > 0]
            except Exception:
                input_devices = []
        if not input_devices:
            input_devices = [(-1, "No input devices found")]
        # Selected device index (actual device id)
        self.mic_device_var = tk.IntVar(value=input_devices[0][0])
        device_names = [f"{i}: {name}" for i, name in input_devices]
        # Map displayed name -> device index
        self.device_index_map = {device_names[idx]: dev_idx for idx, (dev_idx, _) in enumerate(input_devices)}
        self.device_dropdown = ttk.Combobox(device_frame, values=device_names, state="readonly", width=40)
        self.device_dropdown.current(0)
        self.device_dropdown.pack(side=tk.LEFT, padx=10)
        def on_device_change(event):
            selected_name = self.device_dropdown.get()
            dev_idx = self.device_index_map.get(selected_name, -1)
            try:
                self.mic_device_var.set(dev_idx)
            except Exception:
                self.mic_device_var.set(-1)
        self.device_dropdown.bind("<<ComboboxSelected>>", on_device_change)
        
        # Status and result labels
        live_status_label = tk.Label(parent, text="Click 'Start Monitoring' to begin", 
                                    font=("Segoe UI", 12), bg=LABEL_BG, fg=FG_MAIN)
        live_status_label.pack(pady=10)
        
        live_result_label = tk.Label(parent, text="", font=("Segoe UI", 16, "bold"), 
                                    bg=BG_FRAME, fg=FG_MAIN)
        live_result_label.pack(pady=10)
        
        # Real-time transcript and features
        transcript_label = tk.Label(parent, text="Transcript: ", font=("Segoe UI", 10), bg=BG_FRAME, fg=FG_MAIN, anchor="w", justify="left")
        transcript_label.pack(fill="x", padx=20, pady=(5, 0))
        features_label = tk.Label(parent, text="Features: ", font=("Segoe UI", 10), bg=BG_FRAME, fg=FG_MAIN, anchor="w", justify="left")
        features_label.pack(fill="x", padx=20, pady=(0, 10))
        
        # Monitoring controls
        self.is_monitoring = False
        self._live_monitoring_thread = None
        self._stop_monitoring_flag = False
        self._last_chunk_file = None
        
        def toggle_monitoring():
            if not self.is_monitoring:
                self.is_monitoring = True
                self._stop_monitoring_flag = False
                live_status_label.config(text="🎙️ Live monitoring active...")
                self.set_status("Live voice monitoring started")
                monitor_btn.config(text="⏹️ Stop Monitoring")
                self.start_live_monitoring(live_result_label, live_status_label, transcript_label, features_label, device_index=self.mic_device_var.get())
            else:
                self._stop_monitoring_flag = True
                self.is_monitoring = False
                live_status_label.config(text="Monitoring stopped")
                self.set_status("Live voice monitoring stopped")
                monitor_btn.config(text="🎙️ Start Monitoring")
        monitor_btn = tk.Button(parent, text="🎙️ Start Monitoring", command=toggle_monitoring)
        self.style_button(monitor_btn)
        monitor_btn.pack(pady=10)
        self.add_tooltip(monitor_btn, "Start/stop real-time voice monitoring")
        
        # Play last chunk button
        def play_last_chunk():
            if self._last_chunk_file and os.path.exists(self._last_chunk_file):
                try:
                    if not sf_local or not sd_local:
                        messagebox.showwarning("Playback Unavailable", "Required audio libraries (soundfile/sounddevice) are not available.")
                        return
                    data, samplerate = sf_local.read(self._last_chunk_file)
                    sd_local.play(data, samplerate)
                    sd_local.wait()
                except Exception as e:
                    messagebox.showerror("Playback Error", f"Could not play last chunk: {e}")
            else:
                messagebox.showinfo("No Audio", "No recent audio chunk to play.")
        play_btn = tk.Button(parent, text="▶️ Play Last Chunk", command=play_last_chunk)
        self.style_button(play_btn)
        play_btn.pack(pady=2)
        self.add_tooltip(play_btn, "Play the most recent audio chunk recorded")
        
        # Show transcript button
        def show_transcript_popup():
            transcript = transcript_label.cget("text").replace("Transcript: ", "").strip()
            if transcript:
                self.show_popup("📝 Transcript", transcript)
            else:
                messagebox.showinfo("No Transcript", "No transcript available yet.")
        transcript_btn = tk.Button(parent, text="📝 Show Transcript", command=show_transcript_popup)
        self.style_button(transcript_btn)
        transcript_btn.pack(pady=2)
        self.add_tooltip(transcript_btn, "Show the transcript of the last chunk")
        
        # Show features button
        def show_features_popup():
            features = features_label.cget("text").replace("Features: ", "").strip()
            if features:
                self.show_popup("📊 Features", features)
            else:
                messagebox.showinfo("No Features", "No features available yet.")
        features_btn = tk.Button(parent, text="📊 Show Features", command=show_features_popup)
        self.style_button(features_btn)
        features_btn.pack(pady=2)
        self.add_tooltip(features_btn, "Show features of the last chunk")

    def start_live_monitoring(self, result_label, status_label, transcript_label, features_label, device_index=None):
        """Start live microphone monitoring with real-time analysis and device selection"""
        import sounddevice as sd
        import numpy as np
        import tempfile
        import wave
        import os
        from model.voice_model import VoiceThreatClassifier
        import threading
        def monitor_loop():
            try:
                classifier = VoiceThreatClassifier()
                while self.is_monitoring and not self._stop_monitoring_flag:
                    samplerate = 16000
                    duration = 5
                    status_label.config(text="🎙️ Recording chunk...")
                    rec_kwargs = dict(samplerate=samplerate, channels=1)
                    if device_index is not None and device_index >= 0:
                        rec_kwargs['device'] = device_index
                    recording = sd.rec(int(samplerate * duration), **rec_kwargs)
                    sd.wait()
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                        with wave.open(tmp_file.name, 'wb') as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(samplerate)
                            wf.writeframes((recording * 32767).astype(np.int16).tobytes())
                        self._last_chunk_file = tmp_file.name
                        try:
                            label, emoji, confidence = classifier.predict(tmp_file.name, fast_mode=True)
                            result_label.config(text=f"Detected: {emoji} {label}\nConfidence: {confidence:.2f}%")
                            play_sound(label.lower())
                            if label in ["Threat", "Offensive"]:
                                self.show_popup(f"{emoji} {label}", f"Voice Analysis: {label} detected!\nConfidence: {confidence:.1f}%")
                            status_label.config(text="Analysis complete")
                            self.set_status(f"Voice analyzed: {label} ({confidence:.1f}%)")
                            # Transcript
                            transcript = classifier.transcribe_audio(tmp_file.name)
                            transcript_label.config(text=f"Transcript: {transcript}")
                            # Features
                            features = classifier.analyze_voice_characteristics(tmp_file.name)
                            features_str = ', '.join([f"{k}: {v:.2f}" for k, v in features.items()])
                            features_label.config(text=f"Features: {features_str}")
                        except Exception as e:
                            result_label.config(text="❌ Analysis Failed")
                            status_label.config(text=f"Error: {str(e)}")
                            self.set_status("Voice analysis failed")
                            transcript_label.config(text="Transcript: ")
                            features_label.config(text="Features: ")
                        os.unlink(tmp_file.name)
                    status_label.config(text="🎙️ Monitoring active...")
                    for _ in range(10):
                        if not self.is_monitoring or self._stop_monitoring_flag:
                            break
                        time.sleep(0.5)
            except Exception as e:
                status_label.config(text=f"Monitoring error: {str(e)}")
                self.set_status("Live monitoring error")
                self.is_monitoring = False
        self._live_monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._live_monitoring_thread.start()

    def create_alert_system_tab(self, parent):
        """Create real-time alert system tab"""
        # Instructions
        tk.Label(parent, text="Real-time voice threat monitoring with instant alerts", 
                font=("Segoe UI", 12), bg=LABEL_BG, fg=LABEL_FG).pack(pady=10)
        
        # Alert status
        alert_status_frame = tk.Frame(parent, bg=BG_FRAME)
        alert_status_frame.pack(fill="x", padx=20, pady=10)
        
        self.alert_status_label = tk.Label(alert_status_frame, text="🔴 Alert System: INACTIVE", 
                                          font=("Segoe UI", 14, "bold"), bg=BG_FRAME, fg="#ff4444")
        self.alert_status_label.pack(side=tk.LEFT)
        
        # Alert counter
        self.alert_counter = 0
        self.alert_counter_label = tk.Label(alert_status_frame, text="Alerts: 0", 
                                           font=("Segoe UI", 12), bg=BG_FRAME, fg=FG_MAIN)
        self.alert_counter_label.pack(side=tk.RIGHT)
        
        # Alert log
        log_frame = tk.Frame(parent, bg=BG_FRAME)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(log_frame, text="Alert Log:", font=("Segoe UI", 12, "bold"), 
                bg=LABEL_BG, fg=LABEL_FG).pack(anchor=tk.W)
        
        self.alert_log = scrolledtext.ScrolledText(log_frame, font=("Consolas", 10), 
                                                  height=10, bg=ENTRY_BG, fg=ENTRY_FG)
        self.alert_log.pack(fill="both", expand=True, pady=(5, 10))
        
        # Control buttons
        button_frame = tk.Frame(parent, bg=BG_FRAME)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        self.alert_start_btn = tk.Button(button_frame, text="🚨 Start Alert System", 
                                        command=self.start_alert_system)
        self.style_button(self.alert_start_btn)
        self.alert_start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.alert_stop_btn = tk.Button(button_frame, text="⏹️ Stop Alert System", 
                                       command=self.stop_alert_system, state=tk.DISABLED)
        self.style_button(self.alert_stop_btn)
        self.alert_stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = tk.Button(button_frame, text="🗑️ Clear Log", command=self.clear_alert_log)
        self.style_button(clear_btn)
        clear_btn.pack(side=tk.LEFT)
        
        # Alert settings
        settings_frame = tk.Frame(parent, bg=BG_FRAME)
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(settings_frame, text="Alert Settings:", font=("Segoe UI", 12, "bold"), 
                bg=LABEL_BG, fg=LABEL_FG).pack(anchor=tk.W)
        
        # Sensitivity slider
        sensitivity_frame = tk.Frame(settings_frame, bg=BG_FRAME)
        sensitivity_frame.pack(fill="x", pady=5)
        
        tk.Label(sensitivity_frame, text="Sensitivity:", font=("Segoe UI", 10), 
                bg=BG_FRAME, fg=FG_MAIN).pack(side=tk.LEFT)
        
        self.sensitivity_var = tk.DoubleVar(value=0.6)
        sensitivity_slider = tk.Scale(sensitivity_frame, from_=0.1, to=0.9, 
                                     variable=self.sensitivity_var, orient=tk.HORIZONTAL,
                                     bg=BG_FRAME, fg=FG_MAIN, highlightbackground=BG_FRAME)
        sensitivity_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Alert types
        alert_types_frame = tk.Frame(settings_frame, bg=BG_FRAME)
        alert_types_frame.pack(fill="x", pady=5)
        
        self.alert_threats = tk.BooleanVar(value=True)
        self.alert_offensive = tk.BooleanVar(value=True)
        self.alert_distress = tk.BooleanVar(value=True)
        
        tk.Checkbutton(alert_types_frame, text="Threats", variable=self.alert_threats,
                      font=("Segoe UI", 10), bg=BG_FRAME, fg=FG_MAIN,
                      selectcolor=BG_FRAME, activebackground=BG_FRAME, activeforeground=FG_MAIN).pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Checkbutton(alert_types_frame, text="Offensive", variable=self.alert_offensive,
                      font=("Segoe UI", 10), bg=BG_FRAME, fg=FG_MAIN,
                      selectcolor=BG_FRAME, activebackground=BG_FRAME, activeforeground=FG_MAIN).pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Checkbutton(alert_types_frame, text="Distress", variable=self.alert_distress,
                      font=("Segoe UI", 10), bg=BG_FRAME, fg=FG_MAIN,
                      selectcolor=BG_FRAME, activebackground=BG_FRAME, activeforeground=FG_MAIN).pack(side=tk.LEFT)

    def start_alert_system(self):
        """Start the real-time alert system"""
        try:
            from model.voice_model import VoiceThreatClassifier
            self.voice_classifier = VoiceThreatClassifier()
            
            # Start real-time monitoring
            success = self.voice_classifier.start_real_time_monitoring(
                alert_callback=self.handle_voice_alert
            )
            
            if success:
                self.alert_status_label.config(text="🟢 Alert System: ACTIVE", fg="#44ff44")
                self.alert_start_btn.config(state=tk.DISABLED)
                self.alert_stop_btn.config(state=tk.NORMAL)
                self.set_status("Real-time alert system started")
                
                # Start alert checking thread
                self.alert_checking = True
                threading.Thread(target=self.check_alerts_loop, daemon=True).start()
            else:
                messagebox.showerror("Error", "Failed to start alert system")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start alert system: {e}")

    def stop_alert_system(self):
        """Stop the real-time alert system"""
        try:
            if hasattr(self, 'voice_classifier'):
                self.voice_classifier.stop_real_time_monitoring()
            
            self.alert_checking = False
            self.alert_status_label.config(text="🔴 Alert System: INACTIVE", fg="#ff4444")
            self.alert_start_btn.config(state=tk.NORMAL)
            self.alert_stop_btn.config(state=tk.DISABLED)
            self.set_status("Real-time alert system stopped")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop alert system: {e}")

    def handle_voice_alert(self, alert_data):
        """Handle voice threat alerts"""
        try:
            # Check if alert type is enabled
            label = alert_data['label']
            if label == "Threat" and not self.alert_threats.get():
                return
            elif label == "Offensive" and not self.alert_offensive.get():
                return
            
            # Check confidence threshold
            if alert_data['confidence'] < self.sensitivity_var.get():
                return
            
            # Increment counter
            self.alert_counter += 1
            self.alert_counter_label.config(text=f"Alerts: {self.alert_counter}")
            
            # Add to log
            timestamp = time.strftime("%H:%M:%S", time.localtime(alert_data['timestamp']))
            log_entry = f"[{timestamp}] {alert_data['emoji']} {label} detected (Confidence: {alert_data['confidence']:.2f})\n"
            
            self.alert_log.insert(tk.END, log_entry)
            self.alert_log.see(tk.END)
            
            # Play alert sound
            play_sound(label.lower(), repeat=2)
            
            # Show popup alert
            self.show_popup("🚨 VOICE THREAT DETECTED", f"{alert_data['emoji']} {label} detected!\nConfidence: {alert_data['confidence']:.1f}%\nTime: {timestamp}")
            
            # Update status
            self.set_status(f"Voice threat detected: {label}")
            
        except Exception as e:
            print(f"Alert handling error: {e}")

    def check_alerts_loop(self):
        """Background thread to check for alerts"""
        while self.alert_checking:
            try:
                if hasattr(self, 'voice_classifier'):
                    alerts = self.voice_classifier.get_alerts()
                    for alert in alerts:
                        self.handle_voice_alert(alert)
                time.sleep(0.1)
            except Exception as e:
                print(f"Alert checking error: {e}")
                time.sleep(1)

    def clear_alert_log(self):
        """Clear the alert log"""
        self.alert_log.delete("1.0", tk.END)
        self.alert_counter = 0
        self.alert_counter_label.config(text="Alerts: 0")

    def analyze_voice_file(self, file_path, result_label, status_label, fast_mode=False):
        """Analyze voice file using enhanced voice classifier"""
        try:
            # Try to use enhanced voice classifier if available
            try:
                from model.voice_model import VoiceThreatClassifier
                classifier = VoiceThreatClassifier()
                # Perform comprehensive analysis
                label, emoji, confidence = classifier.predict(file_path, fast_mode=fast_mode)
                
                # Get additional analysis results
                voice_analysis = classifier.analyze_voice_characteristics(file_path)
                emotion_scores = classifier.analyze_emotion(file_path)
                transcription = classifier.transcribe_audio(file_path)
                
                # Enhanced analysis with new features
                intensity_analysis = classifier.analyze_voice_intensity(file_path)
                pattern_analysis = classifier.detect_voice_patterns(file_path)
                
                # Display results
                result_text = f"Detected: {emoji} {label}\nConfidence: {confidence:.2f}%"
                
                # Add intensity analysis
                if intensity_analysis:
                    threat_score = intensity_analysis.get('threat_score', 0)
                    if threat_score > 0.6:
                        result_text += f"\n⚠️ High Intensity Threat Score: {threat_score:.2f}"
                    
                    sudden_changes = intensity_analysis.get('sudden_changes', 0)
                    if sudden_changes > 0.3:
                        result_text += f"\n⚡ Sudden Voice Changes: {sudden_changes:.2f}"
                
                # Add pattern analysis
                if pattern_analysis:
                    pattern_score = pattern_analysis.get('pattern_score', 0)
                    if pattern_score > 0.5:
                        result_text += f"\n🎯 Suspicious Voice Pattern: {pattern_score:.2f}"
                
                # Add stress indicators
                if voice_analysis:
                    stress_level = voice_analysis.get('stress_indicators', 0)
                    if stress_level > 0.6:
                        result_text += f"\n😰 High Stress Detected: {stress_level:.2f}"
                    
                    aggression_level = voice_analysis.get('aggression_indicators', 0)
                    if aggression_level > 0.6:
                        result_text += f"\n😠 High Aggression Detected: {aggression_level:.2f}"

                # Add emotion scores summary if available
                if emotion_scores:
                    try:
                        # emotion_scores is expected as a dict {emotion: score}
                        sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
                        top_items = sorted_emotions[:3]
                        emo_summary = ', '.join([f"{k}: {v:.2f}" for k, v in top_items])
                        result_text += f"\nEmotions: {emo_summary}"
                    except Exception:
                        # If format is unexpected, include raw repr
                        result_text += f"\nEmotions: {repr(emotion_scores)}"
                
                result_label.config(text=result_text)
                
                # Enhanced alert system
                if label in ["Threat", "Offensive"]:
                    # Play enhanced alert sound
                    play_sound(label.lower(), repeat=3)
                    
                    # Show detailed popup
                    alert_message = f"Voice Analysis: {label} detected!\nConfidence: {confidence:.1f}%"
                    
                    if intensity_analysis and intensity_analysis.get('threat_score', 0) > 0.6:
                        alert_message += "\n\n🚨 HIGH INTENSITY THREAT DETECTED!"
                        alert_message += f"\nThreat Score: {intensity_analysis['threat_score']:.2f}"
                    
                    if pattern_analysis and pattern_analysis.get('pattern_score', 0) > 0.5:
                        alert_message += "\n\n🎯 SUSPICIOUS VOICE PATTERN DETECTED!"
                        alert_message += f"\nPattern Score: {pattern_analysis['pattern_score']:.2f}"
                    
                    if transcription:
                        alert_message += f"\n\n📝 Transcription:\n{transcription[:200]}..."
                    
                    self.show_popup(f"{emoji} {label} - VOICE THREAT", alert_message)
                    
                    # Additional visual alert
                    self.flash_alert_indicator()
                else:
                    # Safe result - gentle sound
                    play_sound(label.lower(), repeat=1)
                
                status_label.config(text="Analysis complete")
                self.set_status(f"Voice analyzed: {label} ({confidence:.1f}%)")
                
            except ImportError:
                # Fallback to basic analysis
                self.basic_voice_analysis(file_path, result_label, status_label)
                
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            result_label.config(text="❌ Analysis Failed")
            status_label.config(text=error_msg)
            self.set_status("Voice analysis failed")
            messagebox.showerror("Analysis Error", error_msg)

    def basic_voice_analysis(self, file_path, result_label, status_label):
        """Basic voice analysis fallback"""
        try:
            import librosa
            import numpy as np
            
            # Load audio
            y, sr = librosa.load(file_path, sr=16000)
            
            # Extract basic features
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
            
            # Simple rule-based analysis
            mfcc_variance = np.var(mfccs)
            centroid_mean = np.mean(spectral_centroid)
            zcr_mean = np.mean(zero_crossing_rate)
            
            # Basic threat detection based on audio characteristics
            if mfcc_variance > 50 and centroid_mean > 2000:
                label, emoji = "Threat", "❌"
            elif mfcc_variance > 30 or centroid_mean > 1500:
                label, emoji = "Offensive", "😠"
            else:
                label, emoji = "Safe", "✅"
            
            # Include some feature summaries in the result so they are visible to users
            result_label.config(text=f"Detected: {emoji} {label}\nMFCC var: {mfcc_variance:.2f} | Centroid: {centroid_mean:.1f} | ZCR: {zcr_mean:.4f}")
            play_sound(label.lower())
            
            if label in ["Threat", "Offensive"]:
                self.show_popup(f"{emoji} {label}", f"Voice Analysis: {label} detected!")
            
            status_label.config(text="Basic analysis complete")
            self.set_status(f"Voice analyzed: {label}")
            
        except Exception as e:
            result_label.config(text="❌ Analysis Failed")
            status_label.config(text=f"Error: {str(e)}")
            self.set_status("Voice analysis failed")

    def flash_alert_indicator(self):
        """Flash the screen or create visual alert for threats"""
        try:
            # Create a temporary alert window
            alert_window = tk.Toplevel(self)
            alert_window.title("🚨 THREAT DETECTED")
            alert_window.geometry("400x200")
            alert_window.configure(bg="#ff0000")
                        
            # Make it appear in center
            alert_window.transient(self)
            alert_window.grab_set()
            
            # Add alert message
            tk.Label(alert_window, text="🚨 VOICE THREAT DETECTED 🚨", 
                    font=("Segoe UI", 16, "bold"), bg="#ff0000", fg="#ffffff").pack(pady=20)
            
            tk.Label(alert_window, text="Check the analysis results immediately!", 
                    font=("Segoe UI", 12), bg="#ff0000", fg="#ffffff").pack(pady=10)
            
            # Auto-close after 3 seconds
            alert_window.after(3000, alert_window.destroy)
            
            # Bring to front
            alert_window.lift()
            alert_window.focus_force()
        except Exception as e:
            print(f"Alert indicator error: {e}")

    def show_webcam_mode(self):
        """Live webcam face emotion detection"""
        try:
            from gui.facial_emotion_gui import FacialEmotionGUI
            # Launch in new window
            webcam_window = tk.Toplevel(self)
            FacialEmotionGUI(webcam_window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start live webcam analysis: {e}")
            self.set_status("Webcam analysis failed")
    
    def show_video_mode(self):
        """Analyze video file for face emotions"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if file_path:
            try:
                from facial_emotion_analyzer import FacialEmotionAnalyzer
                analyzer = FacialEmotionAnalyzer()
                results = analyzer.analyze_video_file(file_path)
                if results and results.get('summary'):
                    summary = results['summary']
                    msg = f"Video analyzed!\n\nTotal faces: {summary.get('total_detections', 0)}\nMost common emotion: {summary.get('most_common_emotion', 'Unknown')}\nThreat level: {summary.get('threat_level', 'Low')}"
                    messagebox.showinfo("Analysis Complete", msg)
                    self.set_status("Video analysis complete")
                else:
                    messagebox.showinfo("Analysis Complete", "Video analyzed but no faces detected.")
                    self.set_status("Video analysis complete")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to analyze video: {e}")
                self.set_status("Video analysis failed")
    
    def show_snapshot_mode(self):
        """Analyze image snapshot for face emotions"""
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )
        if file_path:
            try:
                from facial_emotion_analyzer import FacialEmotionAnalyzer
                analyzer = FacialEmotionAnalyzer()
                result = analyzer.analyze_image(file_path)
                if result and result.get('summary'):
                    summary = result['summary']
                    msg = f"Image analyzed!\n\nTotal faces: {summary.get('total_faces', 0)}\nPrimary emotion: {summary.get('primary_emotion', 'Unknown')}\nThreat level: {summary.get('threat_level', 'Low')}"
                    messagebox.showinfo("Analysis Complete", msg)
                    self.set_status("Image analysis complete")
                else:
                    messagebox.showinfo("Analysis Complete", "Image analyzed but no faces detected.")
                    self.set_status("Image analysis complete")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to analyze image: {e}")
                self.set_status("Image analysis failed")

    def on_exit(self):
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = CyberWatchApp()
    app.mainloop()
