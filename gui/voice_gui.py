import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import os
import tempfile
import wave
import numpy as np

# Optional heavy/OS-dependent libraries — import safely so GUI can load without them
try:
    import pyaudio
    _HAS_PYAUDIO = True
except Exception:
    pyaudio = None
    _HAS_PYAUDIO = False

# pygame is optional (used for audio playback). Import safely and set a flag.
try:
    import pygame
    _HAS_PYGAME = True
except Exception:
    pygame = None
    _HAS_PYGAME = False

# soundfile / sounddevice are optional for playback/transcription helpers
try:
    import soundfile as sf
    _HAS_SOUNDFILE = True
except Exception:
    sf = None
    _HAS_SOUNDFILE = False

try:
    import sounddevice as sd
    _HAS_SOUNDDEVICE = True
except Exception:
    sd = None
    _HAS_SOUNDDEVICE = False

# PIL for image handling (optional)
try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except Exception:
    Image = None
    ImageTk = None
    _HAS_PIL = False

# matplotlib (optional, GUI charts)
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    _HAS_MATPLOTLIB = True
except Exception:
    matplotlib = None
    plt = None
    FigureCanvasTkAgg = None
    _HAS_MATPLOTLIB = False

from database.database import Database
from model.text_model import TextThreatClassifier
try:
    from playsound import playsound
except Exception:
    # Fallback to pygame playback if playsound is not available
    def playsound(path):
        try:
            # pygame.mixer should already be initialized elsewhere; attempt to play
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception as _e:
            print(f"Fallback playsound failed: {_e}")
# (soundfile/sounddevice already conditionally imported above)

class VoiceAnalyzerGUI:
    def __init__(self, root, user_id):
        print("DEBUG: VoiceAnalyzerGUI.__init__() called")
        self.root = root
        self.user_id = user_id
        self.db = Database()
        print("DEBUG: Root type:", type(root))
        
        # Always maximize the window if root is a window
        if not isinstance(self.root, tk.Frame):
            print("DEBUG: Root is a window, setting title and state")
            self.root.title("🎤 Enhanced Voice Threat Analyzer")
            self.root.state('zoomed')  # Start maximized
            self.root.minsize(900, 600)
            # Remove fixed geometry to allow full resizing
        else:
            print("DEBUG: Root is a frame")
        
        # Color scheme
        self.colors = {
            'bg_primary': '#1a1a2e',
            'bg_secondary': '#16213e',
            'bg_card': '#0f3460',
            'accent': '#e94560',
            'text_primary': '#ffffff',
            'text_secondary': '#b8b8b8',
            'success': '#4ade80',
            'warning': '#fbbf24',
            'danger': '#f87171',
            'info': '#60a5fa',
            'border': '#233554',
        }
        
        # Only configure root if it's a window (not a frame)
        if not isinstance(self.root, tk.Frame):
            self.root.configure(bg=self.colors['bg_primary'])
            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)
        
        # Initialize components
        self.voice_classifier = None
        self.recording = False
        self.audio_data = []
        self.sample_rate = 16000
        self.recording_thread = None
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Initialize pygame for audio playback (optional)
        if _HAS_PYGAME:
            try:
                pygame.mixer.init()
            except Exception as _e:
                print(f"[WARN] pygame.mixer.init() failed: {_e}")
                _HAS_PYGAME = False
        
        # Create GUI
        print("DEBUG: About to call create_widgets()")
        self.create_widgets()
        print("DEBUG: create_widgets() completed")
        print("DEBUG: About to call initialize_classifier()")
        self.initialize_classifier()
        print("DEBUG: initialize_classifier() completed")
        print("DEBUG: VoiceAnalyzerGUI initialization completed successfully!")
        
        self.analysis_history = []
        self.history_file = "analysis_history.json"
        self.load_history()  # Load from DB for this user
        
        self.text_threat_classifier = TextThreatClassifier()
        self.is_playing_audio = False
        
    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill="both", expand=True)
        # Title and subtitle
        header_frame = tk.Frame(main_frame, bg=self.colors['bg_secondary'])
        header_frame.pack(fill="x", padx=0, pady=(0, 0))
        # Navigation row with Back button and title (consistent with other screens)
        nav_row = tk.Frame(header_frame, bg=self.colors['bg_secondary'])
        nav_row.pack(fill="x", padx=0, pady=(6, 0))
        back_btn = tk.Button(nav_row, text="⬅ Back", command=self.on_back, font=("Segoe UI", 10, "bold"), bg=self.colors['bg_card'], fg="white", relief="flat", bd=0, cursor="hand2")
        back_btn.pack(side="left", anchor="nw", padx=16, pady=(6, 0))
        title_label = tk.Label(nav_row, text="🎤 Enhanced Voice Threat Analyzer", font=("Segoe UI", 24, "bold"), bg=self.colors['bg_secondary'], fg=self.colors['text_primary'])
        title_label.pack(side=tk.LEFT, padx=16)
        subtitle_label = tk.Label(header_frame, text="Advanced AI-powered voice analysis with multi-model threat detection", font=("Segoe UI", 12), bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'])
        subtitle_label.pack(side=tk.TOP, pady=(0, 10))
        # Notebook for tabs
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.TNotebook', background=self.colors['bg_primary'], borderwidth=0)
        style.configure('Custom.TNotebook.Tab', background=self.colors['bg_secondary'], foreground=self.colors['text_primary'], padding=[24, 12], font=('Segoe UI', 12, 'bold'), borderwidth=0)
        style.map('Custom.TNotebook.Tab', background=[('selected', self.colors['accent']), ('active', self.colors['bg_card'])], foreground=[('selected', self.colors['text_primary'])])
        self.notebook = ttk.Notebook(main_frame, style='Custom.TNotebook')
        self.notebook.pack(fill="both", expand=True)
        # Create all tabs
        self.create_voice_analyzer_tab()
        self.create_batch_processing_tab()
        self.create_live_monitoring_tab()
        self.create_history_tab()

    def create_voice_analyzer_tab(self):
        tab = tk.Frame(self.notebook, bg=self.colors['bg_primary'])
        self.notebook.add(tab, text="Voice Analyzer")
        # Split left/right
        left_panel = tk.Frame(tab, bg=self.colors['bg_card'], width=350, height=400, bd=2, relief=tk.RIDGE, highlightbackground=self.colors['border'], highlightthickness=2)
        left_panel.pack(side="left", fill="y", padx=(0, 0), pady=20)
        left_panel.pack_propagate(False)
        # Status label (for model loading, errors, etc.)
        self.status_label = tk.Label(left_panel, text="Ready", font=("Segoe UI", 12, "bold"), bg=self.colors['bg_card'], fg=self.colors['success'])
        self.status_label.pack(fill="x", padx=16, pady=(8, 0))
        # Progress bar for model loading/analysis
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(left_panel, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=16, pady=(4, 8))
        # File input
        tk.Label(left_panel, text="Audio File:", font=("Segoe UI", 12, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(anchor="w", padx=16, pady=(16, 4))
        self.audio_file_var = tk.StringVar()
        entry_browse_frame = tk.Frame(left_panel, bg=self.colors['bg_card'])
        entry_browse_frame.pack(fill="x", padx=16, pady=(0, 16))
        audio_entry = tk.Entry(entry_browse_frame, textvariable=self.audio_file_var, font=("Segoe UI", 12), bg="#fff", fg="#232946", relief="flat", bd=2, width=18)
        audio_entry.pack(side="left", fill="x", expand=True)
        browse_btn = tk.Button(entry_browse_frame, text="\U0001F4C2 Browse", command=self.browse_audio_file, font=("Segoe UI", 10, "bold"), bg="#e94560", fg="white", relief="flat", bd=0, cursor="hand2", padx=10, pady=2)
        browse_btn.pack(side="left", padx=(8, 0))
        # Buttons
        self.analyze_btn = tk.Button(left_panel, text="\U0001F50D Analyze", command=self.analyze_audio_file, font=("Segoe UI", 14, "bold"), bg="#6ec1e4", fg="#232946", relief="flat", bd=0, cursor="hand2", padx=10, pady=8, state="disabled")
        self.analyze_btn.pack(fill="x", padx=16, pady=(8, 8))
        self.play_btn = tk.Button(left_panel, text="\U0001F3B5 Play Audio", command=self.play_audio_file, font=("Segoe UI", 14, "bold"), bg="#51cf66", fg="#232946", relief="flat", bd=0, cursor="hand2", padx=10, pady=8, state="disabled")
        self.play_btn.pack(fill="x", padx=16, pady=(0, 8))
        self.transcript_btn = tk.Button(left_panel, text="\U0001F4DD Transcript", command=self.transcribe_audio_file, font=("Segoe UI", 14, "bold"), bg="#ffd600", fg="#232946", relief="flat", bd=0, cursor="hand2", padx=10, pady=8, state="disabled")
        self.transcript_btn.pack(fill="x", padx=16, pady=(0, 8))
        # Right panel
        right_panel = tk.Frame(tab, bg=self.colors['bg_secondary'])
        right_panel.pack(side="left", fill="both", expand=True, padx=(16, 16), pady=20)
        right_panel.pack_propagate(True)
        self.result_label = tk.Label(right_panel, text="Result: ", font=("Segoe UI", 20, "bold"), bg=self.colors['bg_secondary'], fg=self.colors['accent'])
        self.result_label.pack(anchor="nw", pady=(24, 8), padx=24)
        self.emotion_text = tk.Text(right_panel, height=10, font=("Consolas", 12), bg="#fff", fg="#232946", relief="flat", bd=2)
        self.emotion_text.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        self.emotion_text.config(state="disabled")

    def analyze_audio_file(self):
        file_path = self.audio_file_var.get()
        if not file_path:
            self.result_label.config(text="Result: No file selected")
            return
        # Run analysis in a background thread
        threading.Thread(target=self._analyze_file_thread, args=(file_path,), daemon=True).start()

    def play_audio_file(self):
        import os
        import soundfile as sf
        import sounddevice as sd
        file_path = self.audio_file_var.get()
        print(f"[DEBUG] Trying to play: {file_path}")
        if not file_path:
            self.status_label.config(text="No file selected", fg=self.colors['danger'])
            return
        if not os.path.exists(file_path):
            print("[DEBUG] File does not exist!")
            self.status_label.config(text="File does not exist!", fg=self.colors['danger'])
            return
        if getattr(self, 'is_playing_audio', False):
            self.stop_audio_file()
            return

        def play():
            try:
                self.is_playing_audio = True
                self.play_btn.config(text="⏹️ Stop Audio", command=self.stop_audio_file, bg="#e94560", fg="white")
                self.status_label.config(text="Playing audio...", fg=self.colors['info'])
                ext = os.path.splitext(file_path)[1].lower()
                if ext == ".wav":
                    print("[DEBUG] Using sounddevice for WAV playback.")
                    data, samplerate = sf.read(file_path)
                    sd.play(data, samplerate)
                    sd.wait()  # Wait until playback is finished
                else:
                    print("[DEBUG] Using playsound fallback.")
                    from playsound import playsound
                playsound(file_path)
            except Exception as e:
                self.status_label.config(text=f"Playback error: {e}", fg=self.colors['danger'])
                import tkinter.messagebox as messagebox
                messagebox.showerror("Playback Error", f"Could not play audio:\n{e}")
            finally:
                self.is_playing_audio = False
                self.play_btn.config(text="\U0001F3B5 Play Audio", command=self.play_audio_file, bg="#51cf66", fg="#232946")
                self.status_label.config(text="Audio stopped", fg=self.colors['info'])

        self.audio_thread = threading.Thread(target=play, daemon=True)
        self.audio_thread.start()

    def stop_audio_file(self):
        # playsound cannot actually stop playback, but we reset the button
        self.is_playing_audio = False
        self.play_btn.config(text="\U0001F3B5 Play Audio", command=self.play_audio_file, bg="#51cf66", fg="#232946")
        self.status_label.config(text="Audio stopped", fg=self.colors['info'])

    def transcribe_audio_file(self):
        file_path = self.audio_file_var.get()
        if not file_path:
            self.status_label.config(text="No file selected", fg=self.colors['danger'])
            return
        def do_transcribe():
            try:
                self.status_label.config(text="Transcribing...", fg=self.colors['warning'])
                transcript = self.voice_classifier.transcribe_audio(file_path)
                self.status_label.config(text="Transcript ready", fg=self.colors['success'])
                self.root.after(0, lambda: self.show_transcript_popup(transcript))
            except Exception as e:
                self.status_label.config(text=f"Transcription error: {e}", fg=self.colors['danger'])
        threading.Thread(target=do_transcribe, daemon=True).start()

    def show_transcript_popup(self, transcript):
        popup = tk.Toplevel(self.root)
        popup.title("Transcript")
        popup.configure(bg=self.colors['bg_primary'])
        popup.geometry("600x400")
        label = tk.Label(popup, text="Transcript", font=("Segoe UI", 16, "bold"), bg=self.colors['bg_primary'], fg=self.colors['accent'])
        label.pack(pady=10)
        text = tk.Text(popup, wrap=tk.WORD, font=("Consolas", 12), bg="#fff", fg="#232946")
        text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        text.insert(tk.END, transcript)
        text.config(state=tk.DISABLED)
        close_btn = tk.Button(popup, text="Close", command=popup.destroy, font=("Segoe UI", 12, "bold"), bg=self.colors['danger'], fg="white")
        close_btn.pack(pady=10)

    def map_emotion_to_threat(self, emotion):
        # Example mapping
        if emotion in ["Angry", "Fear", "Disgust"]:
            return "Threat"
        elif emotion in ["Sad", "Surprise"]:
            return "Offensive"
        else:
            return "Safe"

    # Stubs for the other tabs (to be implemented in next steps)
    def create_batch_processing_tab(self):
        """Create batch processing tab with modern design and advanced features"""
        batch_frame = tk.Frame(self.notebook, bg=self.colors['bg_primary'])
        self.notebook.add(batch_frame, text="\U0001F4C1 Batch Processing")
        batch_frame.grid_rowconfigure(0, weight=0)
        batch_frame.grid_rowconfigure(1, weight=1)
        batch_frame.grid_columnconfigure(0, weight=1)
        file_card = self.create_card(batch_frame, "Batch File Selection", padding=20)
        file_card.grid(row=0, column=0, sticky="ew")
        button_frame = tk.Frame(file_card, bg=self.colors['bg_card'])
        button_frame.pack(fill=tk.X, expand=True)
        select_folder_btn = tk.Button(button_frame, text="\U0001F4C1 Select Folder", command=self.select_folder, font=("Segoe UI", 12, "bold"), bg="white", fg="black", relief=tk.FLAT, bd=0, cursor="hand2", padx=20, pady=10)
        select_folder_btn.pack(side=tk.LEFT, padx=(0, 10))
        select_files_btn = tk.Button(button_frame, text="\U0001F4C2 Select Files", command=self.select_batch_files, font=("Segoe UI", 12, "bold"), bg="white", fg="black", relief=tk.FLAT, bd=0, cursor="hand2", padx=20, pady=10)
        select_files_btn.pack(side=tk.LEFT, padx=(0, 10))
        process_btn = tk.Button(button_frame, text="\U0001F50D Process All", command=self.process_batch, font=("Segoe UI", 12, "bold"), bg="white", fg="black", relief=tk.FLAT, bd=0, cursor="hand2", padx=20, pady=10)
        process_btn.pack(side=tk.LEFT)
        self.folder_path_var = tk.StringVar()
        folder_label = tk.Label(file_card, textvariable=self.folder_path_var, font=("Consolas", 11), bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        folder_label.pack(side=tk.LEFT, padx=(10, 0))
        self.batch_progress_var = tk.DoubleVar()
        self.batch_progress_bar = ttk.Progressbar(file_card, variable=self.batch_progress_var, maximum=100, length=400)
        self.batch_progress_bar.pack(fill=tk.X, padx=10, pady=(10, 0))
        self.batch_status_var = tk.StringVar()
        self.batch_status_label = tk.Label(file_card, textvariable=self.batch_status_var, font=("Segoe UI", 10), bg=self.colors['bg_card'], fg=self.colors['info'])
        self.batch_status_label.pack(anchor=tk.W, padx=10, pady=(2, 0))
        results_card = self.create_card(batch_frame, "Batch Results", padding=20)
        results_card.grid(row=1, column=0, sticky="nsew")
        batch_frame.grid_rowconfigure(1, weight=1)
        style = ttk.Style()
        style.configure("Custom.Treeview", background=self.colors['bg_secondary'], foreground=self.colors['text_primary'], fieldbackground=self.colors['bg_secondary'], font=('Segoe UI', 10))
        style.configure("Custom.Treeview.Heading", background=self.colors['accent'], foreground=self.colors['text_primary'], font=('Segoe UI', 10, 'bold'))
        columns = ('File', 'Threat Level', 'Confidence', 'Emotion', 'Duration', 'Delete')
        # --- Scrollable Treeview ---
        tree_frame = tk.Frame(results_card, bg=self.colors['bg_card'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.batch_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15, style="Custom.Treeview")
        for col in columns:
            if col == 'Delete':
                self.batch_tree.heading(col, text="\u274C")
                self.batch_tree.column(col, width=50, anchor='center')
            else:
                self.batch_tree.heading(col, text=col)
                self.batch_tree.column(col, width=150)
        self.batch_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.batch_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.batch_tree.configure(yscrollcommand=scrollbar.set)
        self.setup_batch_delete()
        self.batch_summary_var = tk.StringVar()
        self.batch_summary_label = tk.Label(results_card, textvariable=self.batch_summary_var, font=("Segoe UI", 11, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary'])
        self.batch_summary_label.pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.update_batch_summary()
        batch_btn_frame = tk.Frame(results_card, bg=self.colors['bg_card'])
        batch_btn_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        export_btn = tk.Button(batch_btn_frame, text="\U0001F4E4 Export Batch Results", command=self.export_batch_results, font=("Segoe UI", 11, "bold"), bg="white", fg="black", relief=tk.FLAT, bd=0, cursor="hand2", padx=12, pady=6)
        export_btn.pack(side=tk.LEFT, padx=(0, 10))
        clear_btn = tk.Button(batch_btn_frame, text="\U0001F5D1\uFE0F Clear Batch Results", command=self.clear_batch_results, font=("Segoe UI", 11, "bold"), bg="white", fg="black", relief=tk.FLAT, bd=0, cursor="hand2", padx=12, pady=6)
        clear_btn.pack(side=tk.LEFT)
        self.selected_batch_files = []

    def select_batch_files(self):
        from tkinter import filedialog
        filetypes = [
            ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg"),
            ("All files", "*.*")
        ]
        files = filedialog.askopenfilenames(title="Select Audio Files for Batch Processing", filetypes=filetypes)
        if files:
            self.selected_batch_files = list(files)
            self.folder_path_var.set(f"{len(files)} files selected")
            self.batch_status_var.set("")
        else:
            self.selected_batch_files = []
            self.folder_path_var.set("")
            self.batch_status_var.set("No files selected.")

    def process_batch(self):
        # Use selected files if available, else use all files in selected folder
        audio_files = self.selected_batch_files[:]
        if not audio_files:
            # Try to use folder selection fallback
            import glob
            import os
            folder = self.folder_path_var.get()
            if os.path.isdir(folder):
                audio_files = glob.glob(os.path.join(folder, '*.wav')) + \
                              glob.glob(os.path.join(folder, '*.mp3')) + \
                              glob.glob(os.path.join(folder, '*.m4a')) + \
                              glob.glob(os.path.join(folder, '*.flac')) + \
                              glob.glob(os.path.join(folder, '*.ogg'))
        if not audio_files:
            self.batch_status_var.set("No audio files selected for batch processing.")
            return
        # Clear previous results
        for row in self.batch_tree.get_children():
            self.batch_tree.delete(row)
        self.batch_status_var.set(f"Processing {len(audio_files)} files...")
        self.batch_progress_var.set(0)
        import threading
        threading.Thread(target=self._process_batch_thread, args=(audio_files,), daemon=True).start()

    def _process_batch_thread(self, audio_files):
        print(f"DEBUG: Starting batch processing for {len(audio_files)} files: {audio_files}")
        try:
            threat_count = 0
            offensive_count = 0
            safe_count = 0
            for i, file_path in enumerate(audio_files):
                try:
                    print(f"DEBUG: Processing file {i+1}/{len(audio_files)}: {file_path}")
                    # Analyze file
                    label, emoji, confidence = self.voice_classifier.predict(file_path)
                    emotion_scores = self.voice_classifier.analyze_emotion(file_path)
                    features = self.voice_classifier.extract_audio_features(file_path)
                    # Get dominant emotion
                    dominant_emotion = "Unknown"
                    if emotion_scores:
                        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
                    # Map emotion to threat level
                    threat_level = self.map_emotion_to_threat(dominant_emotion)
                    # Play beep feedback for each file
                    self.play_beep(threat_level)
                    if threat_level == "Threat":
                        threat_count += 1
                    elif threat_level == "Offensive":
                        offensive_count += 1
                    else:
                        safe_count += 1
                    # Get duration
                    duration = features.get('duration', 0) if features else 0
                    print(f"DEBUG: Inserting into batch_tree: {os.path.basename(file_path)}, {threat_level}, {confidence}, {dominant_emotion}, {duration}")
                    self.root.after(0, lambda f=file_path, l=threat_level, c=confidence, e=dominant_emotion, d=duration: 
                        self.batch_tree.insert('', 'end', values=(
                            os.path.basename(f), l, f"{c:.1%}", e, f"{d:.1f}s", "❌"
                        ))
                    )
                    print("DEBUG: Insert scheduled for batch_tree")
                    # Add to history
                    transcription = self.voice_classifier.transcribe_audio(file_path)
                    self.add_to_history(file_path, threat_level, dominant_emotion, confidence, duration, transcription, features, scan_type='batch')
                    # Update progress
                    progress = (i + 1) / len(audio_files) * 100
                    self.root.after(0, lambda p=progress: self.batch_progress_var.set(p))
                    self.root.after(0, self.update_batch_summary)
                    # Show alert if Threat or Offensive for each file
                    if threat_level in ("Threat", "Offensive"):
                        self.show_threat_alert(f"Alert: Detected {dominant_emotion} ({threat_level}) in {os.path.basename(file_path)}!")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    continue
            self.root.after(0, lambda: self.folder_path_var.set(f"Completed - {len(audio_files)} files processed"))
            self.root.after(0, self.update_batch_summary)
            self.root.after(0, lambda: self.batch_progress_var.set(0))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Batch processing failed: {str(e)}"))

    def update_batch_summary(self):
        # Count Threat, Offensive, Safe in batch table
        threat, offensive, safe = 0, 0, 0
        for row in self.batch_tree.get_children():
            values = self.batch_tree.item(row, 'values')
            if not values or len(values) < 2:
                continue
            level = values[1]
            if level == "Threat":
                threat += 1
            elif level == "Offensive":
                offensive += 1
            elif level == "Safe":
                safe += 1
        total = threat + offensive + safe
        self.batch_summary_var.set(f"Total: {total} | Threat: {threat} | Offensive: {offensive} | Safe: {safe}")

    def export_batch_results(self):
        # Export current batch table to CSV
        from tkinter import filedialog, messagebox
        import csv
        file_path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')], title="Export Batch Results")
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['File', 'Threat Level', 'Confidence', 'Emotion', 'Duration'])
                for row in self.batch_tree.get_children():
                    values = self.batch_tree.item(row, 'values')
                    writer.writerow(values[:5])
            messagebox.showinfo("Success", f"Batch results exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export batch results: {e}")

    def clear_batch_results(self):
        # Remove all rows from batch table
        for row in self.batch_tree.get_children():
            self.batch_tree.delete(row)
        self.update_batch_summary()
    
    def setup_batch_delete(self):
        # Add delete button handler for batch tree
        self.batch_tree.bind('<Button-1>', self.handle_batch_delete)

    def handle_batch_delete(self, event):
        region = self.batch_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.batch_tree.identify_column(event.x)
            item = self.batch_tree.identify_row(event.y)
            if item and column == "#6":  # Delete column
                self.delete_batch_entry(item)

    def delete_batch_entry(self, item):
        values = self.batch_tree.item(item, 'values')
        if not values:
            return
        file_name = values[0]
        # Remove from batch tree
        self.batch_tree.delete(item)
        # Remove from history as well
        for i, entry in enumerate(self.analysis_history):
            if entry['file_name'] == file_name:
                del self.analysis_history[i]
                self.save_history()
                self.refresh_history()
                break
    
    def create_history_tab(self):
        """Create the history tab with session tracking and analysis history"""
        history_frame = tk.Frame(self.notebook, bg=self.colors['bg_primary'])
        self.notebook.add(history_frame, text="📅 History")
        
        # Initialize history storage
        self.analysis_history = []
        self.session_log = []
        self.history_file = "analysis_history.json"
        self.load_history()
        
        # Layout: 2 columns
        history_frame.grid_rowconfigure(0, weight=1)
        history_frame.grid_columnconfigure(0, weight=0)
        history_frame.grid_columnconfigure(1, weight=1)
        
        # Left: Controls and filters
        left_panel = tk.Frame(history_frame, bg=self.colors['bg_card'], width=300, bd=2, relief=tk.RIDGE, highlightbackground=self.colors['border'], highlightthickness=2)
        left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 0), pady=0)
        left_panel.grid_propagate(False)
        left_panel.pack_propagate(False)
        
        # Title
        tk.Label(left_panel, text="📅 Analysis History", font=("Segoe UI", 16, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(padx=12, pady=(16, 8))
        
        # Filter controls
        filter_frame = tk.Frame(left_panel, bg=self.colors['bg_card'])
        filter_frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        
        tk.Label(filter_frame, text="Filter by Threat Level:", font=("Segoe UI", 11, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(anchor=tk.W)
        
        self.threat_filter_var = tk.StringVar(value="All")
        threat_filters = ["All", "Safe", "Offensive", "Threat"]
        for threat in threat_filters:
            tk.Radiobutton(filter_frame, text=threat, variable=self.threat_filter_var, value=threat, 
                          font=("Segoe UI", 10), bg=self.colors['bg_card'], fg=self.colors['text_primary'],
                          selectcolor=self.colors['bg_secondary'], activebackground=self.colors['bg_card'],
                          activeforeground=self.colors['text_primary'], command=self.refresh_history).pack(anchor=tk.W)
        

        
        # Action buttons
        button_frame = tk.Frame(left_panel, bg=self.colors['bg_card'])
        button_frame.pack(fill=tk.X, padx=12, pady=(16, 8))
        
        refresh_btn = tk.Button(button_frame, text="🔄 Refresh", command=self.refresh_history, 
                               font=("Segoe UI", 11, "bold"), bg=self.colors['info'], fg=self.colors['text_primary'],
                               relief=tk.FLAT, bd=0, cursor="hand2", padx=12, pady=6)
        refresh_btn.pack(fill=tk.X, pady=(0, 8))
        
        export_btn = tk.Button(button_frame, text="📤 Export CSV", command=self.export_history, 
                              font=("Segoe UI", 11, "bold"), bg=self.colors['success'], fg=self.colors['text_primary'],
                              relief=tk.FLAT, bd=0, cursor="hand2", padx=12, pady=6)
        export_btn.pack(fill=tk.X, pady=(0, 8))
        
        clear_btn = tk.Button(button_frame, text="🗑️ Clear History", command=self.clear_history, 
                             font=("Segoe UI", 11, "bold"), bg=self.colors['danger'], fg=self.colors['text_primary'],
                             relief=tk.FLAT, bd=0, cursor="hand2", padx=12, pady=6)
        clear_btn.pack(fill=tk.X)
        
        # Right: History table
        right_panel = tk.Frame(history_frame, bg=self.colors['bg_primary'])
        right_panel.grid(row=0, column=1, sticky="nsew", padx=16, pady=0)
        history_frame.grid_rowconfigure(0, weight=1)
        history_frame.grid_columnconfigure(1, weight=1)
        
        # Treeview with custom styling
        style = ttk.Style()
        style.configure("History.Treeview",
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       fieldbackground=self.colors['bg_secondary'],
                       font=('Segoe UI', 10))
        style.configure("History.Treeview.Heading",
                       background=self.colors['accent'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 10, 'bold'))
        
        columns = ('Time', 'File', 'Threat Level', 'Emotion', 'Confidence', 'Duration', 'Delete')
        self.history_tree = ttk.Treeview(right_panel, columns=columns, show='headings', height=20, style="History.Treeview")
        
        for col in columns:
            if col == 'Delete':
                self.history_tree.heading(col, text="❌")
                self.history_tree.column(col, width=50, anchor='center')
            else:
                self.history_tree.heading(col, text=col, command=lambda c=col: self.sort_history(c))
                if col == 'Time':
                    self.history_tree.column(col, width=150)
                elif col == 'File':
                    self.history_tree.column(col, width=200)
                elif col == 'Duration':
                    self.history_tree.column(col, width=80)
                else:
                    self.history_tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.history_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind double-click to view details and single click for delete
        self.history_tree.bind('<Double-1>', self.view_history_details)
        self.history_tree.bind('<Button-1>', self.handle_history_click)
        
        # Status bar
        self.history_status_label = tk.Label(right_panel, text="No history entries", font=("Segoe UI", 10), 
                                            bg=self.colors['bg_primary'], fg=self.colors['text_secondary'])
        self.history_status_label.pack(anchor=tk.W, pady=(8, 0))
    
    def add_to_history(self, file_path, threat_level, emotion, confidence, duration=None, transcription=None, features=None, scan_type='single'):
        print(f"[DEBUG] add_to_history: user_id={self.user_id}, scan_type={scan_type}, file_path={file_path}, threat_level={threat_level}")
        # Save to DB
        self.db.save_scan_result(
            self.user_id,
            scan_type,
            file_path,
            threat_level,
            confidence,
            emotion,
            duration,
            transcription
        )
        print(f"[DEBUG] add_to_history: saved to DB for user_id={self.user_id}")
        self.load_history()  # Reload from DB
        self.refresh_history()
    
    def refresh_history(self):
        """Refresh the history display with current filters"""
        # Clear current display
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Apply filters
        threat_filter = self.threat_filter_var.get()
        
        filtered_history = []
        for entry in self.analysis_history:
            # Apply threat level filter
            if threat_filter != "All" and entry['threat_level'] != threat_filter:
                continue
            
            filtered_history.append(entry)
        
        # Sort by timestamp (newest first)
        filtered_history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Add to treeview
        for entry in filtered_history:
            time_str = entry['timestamp']
            duration_str = f"{entry['duration']:.1f}s" if entry['duration'] else "N/A"
            
            self.history_tree.insert('', 'end', values=(
                time_str,
                entry['file_name'],
                entry['threat_level'],
                entry['emotion'],
                f"{entry['confidence']:.2f}" if entry['confidence'] is not None else "N/A",
                duration_str,
                "❌"
            ))
        
        # Update status
        self.history_status_label.config(text=f"Showing {len(filtered_history)} of {len(self.analysis_history)} entries")
    
    def sort_history(self, column):
        """Sort history by column"""
        # Get current items
        items = [(self.history_tree.set(item, column), item) for item in self.history_tree.get_children('')]
        
        # Sort items
        items.sort()
        
        # Rearrange items in sorted positions
        for index, (val, item) in enumerate(items):
            self.history_tree.move(item, '', index)
    
    def handle_history_click(self, event):
        """Handle clicks on history tree - delete or view details"""
        region = self.history_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.history_tree.identify_column(event.x)
            item = self.history_tree.identify_row(event.y)
            
            if item and column == "#7":  # Delete column
                self.delete_history_entry(item)
            elif item:
                # Double-click for details (handled by existing method)
                pass
    
    def delete_history_entry(self, item):
        """Delete a specific history entry"""
        values = self.history_tree.item(item, 'values')
        if not values:
            return
        
        time_str = values[0]
        file_name = values[1]
        
        # Find and remove the entry
        for i, entry in enumerate(self.analysis_history):
            if (entry['timestamp'] == time_str and 
                entry['file_name'] == file_name):
                del self.analysis_history[i]
                self.save_history()
                self.refresh_history()
                break
    
    def view_history_details(self, event):
        """View detailed information for selected history entry"""
        selection = self.history_tree.selection()
        if not selection:
            return
        
        # Get selected item
        item = selection[0]
        values = self.history_tree.item(item, 'values')
        
        # Find corresponding history entry
        time_str = values[0]
        file_name = values[1]
        
        for entry in self.analysis_history:
            if (entry['timestamp'] == time_str and 
                entry['file_name'] == file_name):
                self.show_history_details(entry)
                break
    
    def show_history_details(self, entry):
        """Show detailed view of history entry"""
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Analysis Details - {entry['file_name']}")
        details_window.geometry("600x500")
        details_window.configure(bg=self.colors['bg_primary'])
        
        # Make window modal
        details_window.transient(self.root)
        details_window.grab_set()
        
        # Content frame
        content_frame = tk.Frame(details_window, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # Title
        title_label = tk.Label(content_frame, text=f"📊 Analysis Details", 
                              font=("Segoe UI", 18, "bold"), bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
        title_label.pack(anchor=tk.W, pady=(0, 16))
        
        # Details text
        details_text = scrolledtext.ScrolledText(content_frame, height=20, wrap=tk.WORD, 
                                               font=("Consolas", 11), bg=self.colors['bg_secondary'], 
                                               fg=self.colors['text_primary'], relief=tk.FLAT, bd=10)
        details_text.pack(fill=tk.BOTH, expand=True)
        
        # Format details
        details = f"""File: {entry['file_path']}
Time: {entry['timestamp']}
Duration: {entry['duration']:.2f}s (if available)

Threat Analysis:
- Level: {entry['threat_level']}
- Confidence: {entry['confidence']:.3f}

Emotion Analysis:
- Dominant Emotion: {entry['emotion']}

Transcription:
{entry.get('transcription', 'No transcription available')}

Features:
{entry.get('features', 'No features available')}
"""
        
        details_text.insert(tk.END, details)
        details_text.config(state=tk.DISABLED)
        
        # Close button
        close_btn = tk.Button(content_frame, text="Close", command=details_window.destroy,
                             font=("Segoe UI", 12, "bold"), bg=self.colors['accent'], fg=self.colors['text_primary'],
                             relief=tk.FLAT, bd=0, cursor="hand2", padx=20, pady=8)
        close_btn.pack(pady=(16, 0))
    
    def export_history(self):
        """Export history to CSV file"""
        if not self.analysis_history:
            messagebox.showinfo("Info", "No history entries to export.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
            title="Export Analysis History"
        )
        
        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    # Write header
                    writer.writerow(['Timestamp', 'File', 'Threat Level', 'Emotion', 'Confidence', 'Duration', 'Transcription'])
                    
                    # Write data
                    for entry in self.analysis_history:
                        writer.writerow([
                            entry['timestamp'],
                            entry['file_path'],
                            entry['threat_level'],
                            entry['emotion'],
                            f"{entry['confidence']:.3f}",
                            f"{entry['duration']:.2f}" if entry['duration'] else "N/A",
                            entry.get('transcription', '')
                        ])
                
                messagebox.showinfo("Success", f"History exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export history: {str(e)}")
    
    def clear_history(self):
        """Clear all history entries"""
        if not self.analysis_history:
            messagebox.showinfo("Info", "No history entries to clear.")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all history entries? This action cannot be undone."):
            self.analysis_history.clear()
            self.save_history()
            self.refresh_history()
            messagebox.showinfo("Success", "History cleared successfully.")
    
    def save_history(self):
        import json
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def load_history(self):
        # Load from DB for this user
        print(f"[DEBUG] load_history: user_id={self.user_id}")
        rows = self.db.get_user_scan_history(self.user_id, limit=100)
        print(f"[DEBUG] load_history: loaded {len(rows)} rows for user_id={self.user_id}")
        self.analysis_history = []
        for row in rows:
            scan_type, content, threat_level, confidence, emotion, duration, transcription, timestamp = row
            entry = {
                'timestamp': timestamp,
                'file_path': content,
                'file_name': os.path.basename(content) if content else "Live Recording",
                'threat_level': threat_level,
                'emotion': emotion,
                'confidence': confidence,
                'duration': duration,
                'transcription': transcription,
                'features': None
            }
            self.analysis_history.append(entry)
    
    def initialize_classifier(self):
        """Initialize the voice classifier in a background thread for responsive UI"""
        # Disable analysis controls until models are loaded
        self.set_analysis_controls_state('disabled')
        self.status_label.config(text="Loading models...", fg=self.colors['warning'])
        self.progress_var.set(10)
        self.root.update()

        def load_models():
            try:
                from model.voice_model import VoiceThreatClassifier
                classifier = VoiceThreatClassifier()
                self.root.after(0, lambda: self.on_models_loaded(classifier))
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"Error: {e}", fg=self.colors['danger']))

        threading.Thread(target=load_models, daemon=True).start()

    def on_models_loaded(self, classifier):
        """Callback after models are loaded to update UI and enable controls"""
        try:
            self.voice_classifier = classifier
            self.progress_var.set(100)
            self.status_label.config(text="Models loaded successfully", fg=self.colors['success'])
            self.set_analysis_controls_state('normal')
        except tk.TclError:
            # Widget was destroyed, ignore
            pass

    def set_analysis_controls_state(self, state):
        """Enable or disable analysis controls (buttons)"""
        # Single File Analysis tab
        try:
            for btn in [self.file_entry, getattr(self, 'analyze_file_btn', None), getattr(self, 'play_audio_btn', None), getattr(self, 'show_transcription_btn', None), getattr(self, 'show_features_btn', None)]:
                if btn:
                    btn.config(state=state)
        except Exception:
            pass
        # You may need to store button references in __init__ or create_control_panel for this to work

    # In create_control_panel, store button references for easy enabling/disabling
    def create_control_panel(self, parent):
        file_label = tk.Label(parent, text="Audio File:", font=("Segoe UI", 12, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary'])
        file_label.pack(anchor=tk.W, pady=(12, 4), padx=12)
        file_entry_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        file_entry_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(file_entry_frame, textvariable=self.file_path_var, font=("Segoe UI", 11), bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=8)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        browse_btn = tk.Button(file_entry_frame, text="📁 Browse", command=self.browse_file, font=("Segoe UI", 11, "bold"), bg=self.colors['accent'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=14)
        browse_btn.pack(side=tk.RIGHT)
        self.add_tooltip(browse_btn, "Browse for an audio file to analyze")
        # Fast Mode
        self.fast_mode_var = tk.BooleanVar(value=False)
        fast_mode_check = tk.Checkbutton(parent, text="⚡ Fast Mode (skip deep models)", variable=self.fast_mode_var, font=("Segoe UI", 10, "bold"), bg=self.colors['bg_card'], fg=self.colors['accent'], selectcolor=self.colors['bg_secondary'], activebackground=self.colors['bg_card'], activeforeground=self.colors['accent'])
        fast_mode_check.pack(anchor=tk.W, padx=12, pady=(0, 12))
        self.add_tooltip(fast_mode_check, "Enable for faster but less accurate analysis")
        # Analysis Controls
        self.analyze_file_btn = tk.Button(parent, text="🔍 Analyze File", command=self.analyze_file, font=("Segoe UI", 12, "bold"), bg=self.colors['info'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=14, pady=8, activebackground=self.colors['accent'])
        self.analyze_file_btn.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.add_tooltip(self.analyze_file_btn, "Analyze the selected audio file")
        self.play_audio_btn = tk.Button(parent, text="🎵 Play Audio", command=self.play_audio, font=("Segoe UI", 12, "bold"), bg=self.colors['success'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=14, pady=8, activebackground=self.colors['accent'])
        self.play_audio_btn.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.add_tooltip(self.play_audio_btn, "Play the selected audio file")
        self.show_transcription_btn = tk.Button(parent, text="📝 Show Transcription", command=self.show_transcription, font=("Segoe UI", 12, "bold"), bg=self.colors['warning'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=14, pady=8, activebackground=self.colors['accent'])
        self.show_transcription_btn.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.add_tooltip(self.show_transcription_btn, "Show the transcription of the audio")
        self.show_features_btn = tk.Button(parent, text="📊 Show Features", command=self.show_features, font=("Segoe UI", 12, "bold"), bg=self.colors['accent'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=14, pady=8, activebackground=self.colors['accent'])
        self.show_features_btn.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.add_tooltip(self.show_features_btn, "Show extracted audio features")
        # Status
        self.status_label = tk.Label(parent, text="Ready", font=("Segoe UI", 13, "bold"), bg=self.colors['bg_card'], fg=self.colors['success'])
        self.status_label.pack(padx=12, pady=(16, 8))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(parent, variable=self.progress_var, maximum=100, length=300)
        self.progress_bar.pack(padx=12, pady=(0, 12))

    def create_results_panel(self, parent):
        result_card = self.create_card(parent, "Analysis Result", padding=14)
        self.result_label = tk.Label(result_card, text="Emotion Detection", font=("Segoe UI", 14, "bold"), bg=self.colors['bg_card'], fg=self.colors['accent'])
        self.result_label.pack(anchor=tk.W, pady=(0, 8))
        # Main result area
        self.main_result_frame = tk.Frame(result_card, bg=self.colors['bg_card'], bd=2, relief=tk.GROOVE, highlightbackground=self.colors['border'], highlightthickness=2)
        self.main_result_frame.pack(fill=tk.X, pady=(0, 8), padx=2)
        self.main_result_text = tk.Label(self.main_result_frame, text="", font=("Segoe UI", 24, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary'])
        self.main_result_text.pack(pady=8)
        self.confidence_label = tk.Label(self.main_result_frame, text="", font=("Segoe UI", 12), bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.confidence_label.pack()
        self.keywords_label = tk.Label(self.main_result_frame, text="", font=("Segoe UI", 11), bg=self.colors['bg_card'], fg=self.colors['info'])
        self.keywords_label.pack()
        # Buttons below result
        btn_frame = tk.Frame(result_card, bg=self.colors['bg_card'])
        btn_frame.pack(fill=tk.X, pady=(0, 8))
        play_btn = tk.Button(btn_frame, text="🎵 Play Audio", command=self.play_audio, font=("Segoe UI", 11, "bold"), bg=self.colors['success'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=10, pady=6)
        play_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.add_tooltip(play_btn, "Play the analyzed audio")
        details_btn = tk.Button(btn_frame, text="📋 Show Details", command=self.show_features, font=("Segoe UI", 11, "bold"), bg=self.colors['info'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=10, pady=6)
        details_btn.pack(side=tk.LEFT)
        self.add_tooltip(details_btn, "Show detailed analysis features")
        # Text area for additional info
        self.result_text = tk.Text(result_card, height=10, font=("Segoe UI", 11), bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], relief=tk.FLAT, wrap=tk.WORD, bd=0)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=(0, 2))
        self.result_text.config(state=tk.DISABLED)
        
        # Add a session log panel below the results
        results_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        results_frame.pack(fill=tk.BOTH, expand=True)
        # Existing results widgets...
        # Add session log
        log_label = tk.Label(results_frame, text="Session Analysis Log", font=("Segoe UI", 12, "bold"), bg=self.colors['bg_primary'], fg=self.colors['accent'])
        log_label.pack(anchor=tk.W, padx=8, pady=(8, 0))
        self.log_tree = ttk.Treeview(results_frame, columns=("File", "Label", "Confidence", "Time"), show="headings", height=6)
        for col in ("File", "Label", "Confidence", "Time"):
            self.log_tree.heading(col, text=col)
            self.log_tree.column(col, width=120)
        self.log_tree.pack(fill=tk.X, padx=8, pady=(0, 8))
        # Log control buttons
        log_btn_frame = tk.Frame(results_frame, bg=self.colors['bg_primary'])
        log_btn_frame.pack(anchor=tk.W, padx=8, pady=(0, 8))
        play_btn = tk.Button(log_btn_frame, text="▶ Play", command=self.play_log_entry, font=("Segoe UI", 10, "bold"), bg=self.colors['success'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=10)
        play_btn.pack(side=tk.LEFT, padx=(0, 8))
        delete_btn = tk.Button(log_btn_frame, text="🗑 Delete", command=self.delete_log_entry, font=("Segoe UI", 10, "bold"), bg=self.colors['danger'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=10)
        delete_btn.pack(side=tk.LEFT, padx=(0, 8))
        clear_btn = tk.Button(log_btn_frame, text="🧹 Clear Log", command=self.clear_log, font=("Segoe UI", 10, "bold"), bg=self.colors['warning'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=10)
        clear_btn.pack(side=tk.LEFT, padx=(0, 8))
        export_btn = tk.Button(log_btn_frame, text="💾 Export Log", command=self.export_log, font=("Segoe UI", 10, "bold"), bg=self.colors['info'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=10)
        export_btn.pack(side=tk.LEFT)
        # Store log data in memory
        self.session_log = []
        
    def create_card(self, parent, title, padding=12):
        """Create a modern card widget"""
        card = tk.Frame(parent, bg=self.colors['bg_card'], bd=2, relief=tk.RIDGE, highlightbackground=self.colors['border'], highlightthickness=2)
        label = tk.Label(card, text=title, font=("Segoe UI", 14, "bold"), bg=self.colors['bg_card'], fg=self.colors['accent'])
        label.pack(anchor=tk.W, padx=padding, pady=(padding, 0))
        # Use grid if parent uses grid, else pack
        if hasattr(parent, 'grid_slaves') and parent.grid_slaves():
            card.grid(sticky="nsew", padx=2, pady=8)
        else:
            card.pack(fill=tk.X, pady=8, padx=2)
        return card
        
    def create_threat_analysis_tab(self):
        """Create threat analysis results tab with modern design"""
        threat_frame = tk.Frame(self.results_notebook, bg=self.colors['bg_primary'])
        self.results_notebook.add(threat_frame, text="⚠️ Threat Analysis")
        threat_frame.pack(fill=tk.BOTH, expand=True)
        
        # Main result card
        result_card = self.create_card(threat_frame, "Analysis Result", padding=10)
        
        self.result_label = tk.Label(
            result_card,
            text="No analysis performed",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary']
        )
        self.result_label.pack(pady=10)
        
        self.confidence_label = tk.Label(
            result_card,
            text="",
            font=("Segoe UI", 11),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary']
        )
        self.confidence_label.pack()
        
        # Detailed scores card
        scores_card = self.create_card(threat_frame, "Detailed Scores", padding=10)
        
        # Create score bars with modern styling
        self.score_vars = {}
        score_names = ['Audio Score', 'Text Score', 'Emotion Score', 'Toxicity Score', 'Sentiment Score']
        
        for name in score_names:
            score_frame = tk.Frame(scores_card, bg=self.colors['bg_card'])
            score_frame.pack(fill=tk.X, pady=2)
            
            # Score name
            name_label = tk.Label(score_frame, text=f"{name}:", 
                                font=("Segoe UI", 9, "bold"),
                                bg=self.colors['bg_card'], 
                                fg=self.colors['text_primary'],
                                width=13, anchor=tk.W)
            name_label.pack(side=tk.LEFT)
            
            # Progress bar
            var = tk.DoubleVar()
            self.score_vars[name] = var
            
            progress = ttk.Progressbar(score_frame, variable=var, maximum=1.0, 
                                     length=120, style='Custom.Horizontal.TProgressbar')
            progress.pack(side=tk.LEFT, padx=(6, 6))
            
            # Score label
            label = tk.Label(score_frame, text="0.0%", 
                           font=("Segoe UI", 8, "bold"),
                           bg=self.colors['bg_card'], 
                           fg=self.colors['text_primary'],
                           width=7)
            label.pack(side=tk.LEFT)
            
            # Store label reference for updating
            setattr(self, f"{name.lower().replace(' ', '_')}_label", label)
        
    def create_emotion_analysis_tab(self):
        """Create emotion analysis results tab with modern design"""
        emotion_frame = tk.Frame(self.results_notebook, bg=self.colors['bg_primary'])
        self.results_notebook.add(emotion_frame, text="😊 Emotion Analysis")
        
        # Emotion scores card
        emotion_card = self.create_card(emotion_frame, "Emotion Detection", padding=20)
        
        self.emotion_text = scrolledtext.ScrolledText(
            emotion_card,
            height=12,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            relief=tk.FLAT,
            bd=10
        )
        self.emotion_text.pack(fill=tk.BOTH, expand=True)
        
        # Emotion visualization card
        viz_card = self.create_card(emotion_frame, "Emotion Visualization", padding=20)
        
        # Placeholder for emotion chart
        self.emotion_canvas = None
        
    def create_voice_characteristics_tab(self):
        """Create voice characteristics results tab with modern design"""
        voice_frame = tk.Frame(self.results_notebook, bg=self.colors['bg_primary'])
        self.results_notebook.add(voice_frame, text="🎵 Voice Characteristics")
        
        # Voice analysis card
        voice_card = self.create_card(voice_frame, "Voice Analysis", padding=20)
        
        self.voice_text = scrolledtext.ScrolledText(
            voice_card,
            height=18,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            relief=tk.FLAT,
            bd=10
        )
        self.voice_text.pack(fill=tk.BOTH, expand=True)
        
    def create_text_analysis_tab(self):
        """Create text analysis results tab with modern design"""
        text_frame = tk.Frame(self.results_notebook, bg=self.colors['bg_primary'])
        self.results_notebook.add(text_frame, text="📝 Text Analysis")
        
        # Back button with modern styling
        back_btn = tk.Button(text_frame, text="⬅ Back to Main Menu", 
                           command=self.on_back_from_text_analysis,
                           font=("Segoe UI", 11, "bold"),
                           bg=self.colors['accent'],
                           fg=self.colors['text_primary'],
                           relief=tk.FLAT,
                           bd=0,
                           cursor="hand2",
                           padx=15,
                           pady=8)
        back_btn.pack(anchor=tk.NW, padx=20, pady=20)
        
        # Transcription card
        transcription_card = self.create_card(text_frame, "Speech Transcription", padding=20)
        
        self.transcription_text = scrolledtext.ScrolledText(
            transcription_card,
            height=8,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            relief=tk.FLAT,
            bd=10
        )
        self.transcription_text.pack(fill=tk.BOTH, expand=True)
        
        # Toxicity analysis card
        toxicity_card = self.create_card(text_frame, "Toxicity Analysis", padding=20)
        
        self.toxicity_text = scrolledtext.ScrolledText(
            toxicity_card,
            height=10,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            relief=tk.FLAT,
            bd=10
        )
        self.toxicity_text.pack(fill=tk.BOTH, expand=True)
        
        # Sentiment analysis card
        sentiment_card = self.create_card(text_frame, "Sentiment Analysis", padding=20)
        
        self.sentiment_text = scrolledtext.ScrolledText(
            sentiment_card,
            height=8,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            relief=tk.FLAT,
            bd=10
        )
        self.sentiment_text.pack(fill=tk.BOTH, expand=True)
        
    def create_audio_features_tab(self):
        """Create audio features results tab with modern design"""
        features_frame = tk.Frame(self.results_notebook, bg=self.colors['bg_primary'])
        self.results_notebook.add(features_frame, text="🔧 Audio Features")
        
        # Features display card
        features_card = self.create_card(features_frame, "Extracted Features", padding=20)
        
        self.features_text = scrolledtext.ScrolledText(
            features_card,
            height=22,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            relief=tk.FLAT,
            bd=10
        )
        self.features_text.pack(fill=tk.BOTH, expand=True)
        
    def create_live_monitoring_tab(self):
        """Create live monitoring tab with modern design and microphone selector"""
        import pyaudio
        import datetime
        live_frame = tk.Frame(self.notebook, bg=self.colors['bg_primary'])
        self.notebook.add(live_frame, text="🎙️ Live Monitoring")
        # Layout: 2 columns
        live_frame.grid_rowconfigure(0, weight=1)
        live_frame.grid_columnconfigure(0, weight=0)
        live_frame.grid_columnconfigure(1, weight=1)
        # Left: Controls
        left_panel = tk.Frame(live_frame, bg=self.colors['bg_card'], width=340, bd=2, relief=tk.RIDGE, highlightbackground=self.colors['border'], highlightthickness=2)
        left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 0), pady=0)
        left_panel.grid_propagate(False)
        left_panel.pack_propagate(False)
        # Status label
        self.live_status_label = tk.Label(left_panel, text="Ready", font=("Segoe UI", 13, "bold"), bg=self.colors['bg_card'], fg=self.colors['success'])
        self.live_status_label.pack(padx=12, pady=(16, 8), anchor=tk.N)
        # Microphone selector
        tk.Label(left_panel, text="Select Microphone:", font=("Segoe UI", 11, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(anchor=tk.W, padx=12, pady=(0, 2))
        self.mic_devices = self.get_microphone_devices()
        self.mic_var = tk.StringVar()
        mic_names = [f"{i}: {name}" for i, name in self.mic_devices]
        if mic_names:
            self.mic_var.set(mic_names[0])
        self.mic_dropdown = tk.OptionMenu(left_panel, self.mic_var, *mic_names)
        self.mic_dropdown.config(font=("Segoe UI", 10), bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], width=28)
        self.mic_dropdown.pack(padx=12, pady=(0, 8))
        # Start/Stop Monitoring button
        self.is_live_monitoring = False
        self.live_monitor_btn = tk.Button(left_panel, text="🎙️ Start Monitoring", command=self.toggle_live_monitoring, font=("Segoe UI", 12, "bold"), bg=self.colors['success'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=14, pady=8, activebackground=self.colors['accent'])
        self.live_monitor_btn.pack(fill=tk.X, padx=12, pady=(0, 8))
        # Recording controls (simple lightweight controls to avoid missing-attribute errors)
        record_frame = tk.Frame(left_panel, bg=self.colors['bg_card'])
        record_frame.pack(fill=tk.X, padx=12, pady=(4, 8))
        self.record_button = tk.Button(record_frame, text="🎙️ Start Recording", command=self.toggle_recording, font=("Segoe UI", 11), bg=self.colors['success'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2")
        self.record_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.play_record_button = tk.Button(record_frame, text="▶ Play Recording", command=self.play_recording, font=("Segoe UI", 11), bg=self.colors['info'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2")
        self.play_record_button.pack(side=tk.LEFT, padx=(8, 0))
        self.save_record_button = tk.Button(record_frame, text="💾 Save", command=self.save_recording, font=("Segoe UI", 11), bg=self.colors['accent'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2")
        self.save_record_button.pack(side=tk.LEFT, padx=(8, 0))
        if not mic_names:
            self.live_monitor_btn.config(state=tk.DISABLED)
            self.live_status_label.config(text="No microphones found", fg=self.colors['danger'])
        # Right: Real-time results
        right_panel = tk.Frame(live_frame, bg=self.colors['bg_primary'])
        right_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        live_frame.grid_rowconfigure(0, weight=1)
        live_frame.grid_columnconfigure(1, weight=1)
        # Dominant Emotion
        self.live_emotion_label = tk.Label(right_panel, text="Dominant Emotion: -", font=("Segoe UI", 16, "bold"), bg=self.colors['bg_primary'], fg=self.colors['accent'])
        self.live_emotion_label.pack(anchor=tk.W, padx=16, pady=(24, 8))
        # Transcript
        tk.Label(right_panel, text="Transcript:", font=("Segoe UI", 12, "bold"), bg=self.colors['bg_primary'], fg=self.colors['text_primary']).pack(anchor=tk.W, padx=16)
        self.live_transcript_text = scrolledtext.ScrolledText(right_panel, height=4, wrap=tk.WORD, font=("Consolas", 11), bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=10)
        self.live_transcript_text.pack(fill=tk.X, padx=16, pady=(0, 12))
        # All Emotion Scores
        tk.Label(right_panel, text="All Emotion Scores:", font=("Segoe UI", 12, "bold"), bg=self.colors['bg_primary'], fg=self.colors['text_primary']).pack(anchor=tk.W, padx=16)
        self.live_emotion_scores_text = scrolledtext.ScrolledText(right_panel, height=4, wrap=tk.WORD, font=("Consolas", 11), bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=10)
        self.live_emotion_scores_text.pack(fill=tk.X, padx=16, pady=(0, 12))
        # Lightweight live result and detail areas used by recording analysis
        self.live_result_label = tk.Label(right_panel, text="Result: -", font=("Segoe UI", 14, "bold"), bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
        self.live_result_label.pack(anchor=tk.W, padx=16, pady=(4, 6))
        self.live_voice_text = scrolledtext.ScrolledText(right_panel, height=6, wrap=tk.WORD, font=("Consolas", 11), bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=10)
        self.live_voice_text.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.live_emotion_text = scrolledtext.ScrolledText(right_panel, height=6, wrap=tk.WORD, font=("Consolas", 11), bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=10)
        self.live_emotion_text.pack(fill=tk.X, padx=16, pady=(0, 8))
        # --- Segment Table ---
        segment_card = self.create_card(right_panel, "Session Segments", padding=10)
        segment_card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
        columns = ("Timestamp", "Emotion", "Threat", "Confidence", "Transcript")
        self.live_segment_tree = ttk.Treeview(segment_card, columns=columns, show='headings', height=8)
        for col in columns:
            self.live_segment_tree.heading(col, text=col)
            self.live_segment_tree.column(col, width=120 if col!="Transcript" else 300)
        self.live_segment_tree.pack(fill=tk.BOTH, expand=True)
        # Scrollbar
        scrollbar = ttk.Scrollbar(segment_card, orient=tk.VERTICAL, command=self.live_segment_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.live_segment_tree.configure(yscrollcommand=scrollbar.set)
        # Bind double-click to show details
        self.live_segment_tree.bind('<Double-1>', self.show_live_segment_details)
        # Internal session segment list
        self.live_segments = []

    def get_microphone_devices(self):
        import pyaudio
        pa = pyaudio.PyAudio()
        devices = []
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info.get('maxInputChannels', 0) > 0:
                devices.append((i, info.get('name', f"Device {i}")))
        pa.terminate()
        return devices
        
    def create_batch_processing_tab(self):
        """Create batch processing tab with modern design and advanced features"""
        batch_frame = tk.Frame(self.notebook, bg=self.colors['bg_primary'])
        self.notebook.add(batch_frame, text="\U0001F4C1 Batch Processing")
        batch_frame.grid_rowconfigure(0, weight=0)
        batch_frame.grid_rowconfigure(1, weight=1)
        batch_frame.grid_columnconfigure(0, weight=1)
        file_card = self.create_card(batch_frame, "Batch File Selection", padding=20)
        file_card.grid(row=0, column=0, sticky="ew")
        button_frame = tk.Frame(file_card, bg=self.colors['bg_card'])
        button_frame.pack(fill=tk.X, expand=True)
        select_folder_btn = tk.Button(button_frame, text="\U0001F4C1 Select Folder", command=self.select_folder, font=("Segoe UI", 12, "bold"), bg="white", fg="black", relief=tk.FLAT, bd=0, cursor="hand2", padx=20, pady=10)
        select_folder_btn.pack(side=tk.LEFT, padx=(0, 10))
        select_files_btn = tk.Button(button_frame, text="\U0001F4C2 Select Files", command=self.select_batch_files, font=("Segoe UI", 12, "bold"), bg="white", fg="black", relief=tk.FLAT, bd=0, cursor="hand2", padx=20, pady=10)
        select_files_btn.pack(side=tk.LEFT, padx=(0, 10))
        process_btn = tk.Button(button_frame, text="\U0001F50D Process All", command=self.process_batch, font=("Segoe UI", 12, "bold"), bg="white", fg="black", relief=tk.FLAT, bd=0, cursor="hand2", padx=20, pady=10)
        process_btn.pack(side=tk.LEFT)
        self.folder_path_var = tk.StringVar()
        folder_label = tk.Label(file_card, textvariable=self.folder_path_var, font=("Consolas", 11), bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        folder_label.pack(side=tk.LEFT, padx=(10, 0))
        self.batch_progress_var = tk.DoubleVar()
        self.batch_progress_bar = ttk.Progressbar(file_card, variable=self.batch_progress_var, maximum=100, length=400)
        self.batch_progress_bar.pack(fill=tk.X, padx=10, pady=(10, 0))
        self.batch_status_var = tk.StringVar()
        self.batch_status_label = tk.Label(file_card, textvariable=self.batch_status_var, font=("Segoe UI", 10), bg=self.colors['bg_card'], fg=self.colors['info'])
        self.batch_status_label.pack(anchor=tk.W, padx=10, pady=(2, 0))
        results_card = self.create_card(batch_frame, "Batch Results", padding=20)
        results_card.grid(row=1, column=0, sticky="nsew")
        batch_frame.grid_rowconfigure(1, weight=1)
        style = ttk.Style()
        style.configure("Custom.Treeview", background=self.colors['bg_secondary'], foreground=self.colors['text_primary'], fieldbackground=self.colors['bg_secondary'], font=('Segoe UI', 10))
        style.configure("Custom.Treeview.Heading", background=self.colors['accent'], foreground=self.colors['text_primary'], font=('Segoe UI', 10, 'bold'))
        columns = ('File', 'Threat Level', 'Confidence', 'Emotion', 'Duration', 'Delete')
        # --- Scrollable Treeview ---
        tree_frame = tk.Frame(results_card, bg=self.colors['bg_card'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.batch_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15, style="Custom.Treeview")
        for col in columns:
            if col == 'Delete':
                self.batch_tree.heading(col, text="\u274C")
                self.batch_tree.column(col, width=50, anchor='center')
            else:
                self.batch_tree.heading(col, text=col)
                self.batch_tree.column(col, width=150)
        self.batch_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.batch_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.batch_tree.configure(yscrollcommand=scrollbar.set)
        self.setup_batch_delete()
        self.batch_summary_var = tk.StringVar()
        self.batch_summary_label = tk.Label(results_card, textvariable=self.batch_summary_var, font=("Segoe UI", 11, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary'])
        self.batch_summary_label.pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.update_batch_summary()
        batch_btn_frame = tk.Frame(results_card, bg=self.colors['bg_card'])
        batch_btn_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        export_btn = tk.Button(batch_btn_frame, text="\U0001F4E4 Export Batch Results", command=self.export_batch_results, font=("Segoe UI", 11, "bold"), bg="white", fg="black", relief=tk.FLAT, bd=0, cursor="hand2", padx=12, pady=6)
        export_btn.pack(side=tk.LEFT, padx=(0, 10))
        clear_btn = tk.Button(batch_btn_frame, text="\U0001F5D1\uFE0F Clear Batch Results", command=self.clear_batch_results, font=("Segoe UI", 11, "bold"), bg="white", fg="black", relief=tk.FLAT, bd=0, cursor="hand2", padx=12, pady=6)
        clear_btn.pack(side=tk.LEFT)
        self.selected_batch_files = []

    def select_batch_files(self):
        from tkinter import filedialog
        filetypes = [
            ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg"),
            ("All files", "*.*")
        ]
        files = filedialog.askopenfilenames(title="Select Audio Files for Batch Processing", filetypes=filetypes)
        if files:
            self.selected_batch_files = list(files)
            self.folder_path_var.set(f"{len(files)} files selected")
            self.batch_status_var.set("")
        else:
            self.selected_batch_files = []
            self.folder_path_var.set("")
            self.batch_status_var.set("No files selected.")

    def process_batch(self):
        # Use selected files if available, else use all files in selected folder
        audio_files = self.selected_batch_files[:]
        if not audio_files:
            # Try to use folder selection fallback
            import glob
            import os
            folder = self.folder_path_var.get()
            if os.path.isdir(folder):
                audio_files = glob.glob(os.path.join(folder, '*.wav')) + \
                              glob.glob(os.path.join(folder, '*.mp3')) + \
                              glob.glob(os.path.join(folder, '*.m4a')) + \
                              glob.glob(os.path.join(folder, '*.flac')) + \
                              glob.glob(os.path.join(folder, '*.ogg'))
        if not audio_files:
            self.batch_status_var.set("No audio files selected for batch processing.")
            return
        # Clear previous results
        for row in self.batch_tree.get_children():
            self.batch_tree.delete(row)
        self.batch_status_var.set(f"Processing {len(audio_files)} files...")
        self.batch_progress_var.set(0)
        import threading
        threading.Thread(target=self._process_batch_thread, args=(audio_files,), daemon=True).start()

    def _process_batch_thread(self, audio_files):
        print(f"DEBUG: Starting batch processing for {len(audio_files)} files: {audio_files}")
        try:
            threat_count = 0
            offensive_count = 0
            safe_count = 0
            for i, file_path in enumerate(audio_files):
                try:
                    print(f"DEBUG: Processing file {i+1}/{len(audio_files)}: {file_path}")
                    # Analyze file
                    label, emoji, confidence = self.voice_classifier.predict(file_path)
                    emotion_scores = self.voice_classifier.analyze_emotion(file_path)
                    features = self.voice_classifier.extract_audio_features(file_path)
                    # Get dominant emotion
                    dominant_emotion = "Unknown"
                    if emotion_scores:
                        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
                    # Map emotion to threat level
                    threat_level = self.map_emotion_to_threat(dominant_emotion)
                    # Play beep feedback for each file
                    self.play_beep(threat_level)
                    if threat_level == "Threat":
                        threat_count += 1
                    elif threat_level == "Offensive":
                        offensive_count += 1
                    else:
                        safe_count += 1
                    # Get duration
                    duration = features.get('duration', 0) if features else 0
                    print(f"DEBUG: Inserting into batch_tree: {os.path.basename(file_path)}, {threat_level}, {confidence}, {dominant_emotion}, {duration}")
                    self.root.after(0, lambda f=file_path, l=threat_level, c=confidence, e=dominant_emotion, d=duration: 
                        self.batch_tree.insert('', 'end', values=(
                            os.path.basename(f), l, f"{c:.1%}", e, f"{d:.1f}s", "❌"
                        ))
                    )
                    print("DEBUG: Insert scheduled for batch_tree")
                    # Add to history
                    transcription = self.voice_classifier.transcribe_audio(file_path)
                    self.add_to_history(file_path, threat_level, dominant_emotion, confidence, duration, transcription, features, scan_type='batch')
                    # Update progress
                    progress = (i + 1) / len(audio_files) * 100
                    self.root.after(0, lambda p=progress: self.batch_progress_var.set(p))
                    self.root.after(0, self.update_batch_summary)
                    # Show alert if Threat or Offensive for each file
                    if threat_level in ("Threat", "Offensive"):
                        self.show_threat_alert(f"Alert: Detected {dominant_emotion} ({threat_level}) in {os.path.basename(file_path)}!")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    continue
            self.root.after(0, lambda: self.folder_path_var.set(f"Completed - {len(audio_files)} files processed"))
            self.root.after(0, self.update_batch_summary)
            self.root.after(0, lambda: self.batch_progress_var.set(0))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Batch processing failed: {str(e)}"))

    def update_batch_summary(self):
        # Count Threat, Offensive, Safe in batch table
        threat, offensive, safe = 0, 0, 0
        for row in self.batch_tree.get_children():
            values = self.batch_tree.item(row, 'values')
            if not values or len(values) < 2:
                continue
            level = values[1]
            if level == "Threat":
                threat += 1
            elif level == "Offensive":
                offensive += 1
            elif level == "Safe":
                safe += 1
        total = threat + offensive + safe
        self.batch_summary_var.set(f"Total: {total} | Threat: {threat} | Offensive: {offensive} | Safe: {safe}")

    def export_batch_results(self):
        # Export current batch table to CSV
        from tkinter import filedialog, messagebox
        import csv
        file_path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')], title="Export Batch Results")
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['File', 'Threat Level', 'Confidence', 'Emotion', 'Duration'])
                for row in self.batch_tree.get_children():
                    values = self.batch_tree.item(row, 'values')
                    writer.writerow(values[:5])
            messagebox.showinfo("Success", f"Batch results exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export batch results: {e}")

    def clear_batch_results(self):
        # Remove all rows from batch table
        for row in self.batch_tree.get_children():
            self.batch_tree.delete(row)
        self.update_batch_summary()
    
    def setup_batch_delete(self):
        # Add delete button handler for batch tree
        self.batch_tree.bind('<Button-1>', self.handle_batch_delete)

    def handle_batch_delete(self, event):
        region = self.batch_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.batch_tree.identify_column(event.x)
            item = self.batch_tree.identify_row(event.y)
            if item and column == "#6":  # Delete column
                self.delete_batch_entry(item)

    def delete_batch_entry(self, item):
        values = self.batch_tree.item(item, 'values')
        if not values:
            return
        file_name = values[0]
        # Remove from batch tree
        self.batch_tree.delete(item)
        # Remove from history as well
        for i, entry in enumerate(self.analysis_history):
            if entry['file_name'] == file_name:
                del self.analysis_history[i]
                self.save_history()
                self.refresh_history()
                break
    
    def create_history_tab(self):
        """Create the history tab with session tracking and analysis history"""
        history_frame = tk.Frame(self.notebook, bg=self.colors['bg_primary'])
        self.notebook.add(history_frame, text="📅 History")
        
        # Initialize history storage
        self.analysis_history = []
        self.session_log = []
        self.history_file = "analysis_history.json"
        self.load_history()
        
        # Layout: 2 columns
        history_frame.grid_rowconfigure(0, weight=1)
        history_frame.grid_columnconfigure(0, weight=0)
        history_frame.grid_columnconfigure(1, weight=1)
        
        # Left: Controls and filters
        left_panel = tk.Frame(history_frame, bg=self.colors['bg_card'], width=300, bd=2, relief=tk.RIDGE, highlightbackground=self.colors['border'], highlightthickness=2)
        left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 0), pady=0)
        left_panel.grid_propagate(False)
        left_panel.pack_propagate(False)
        
        # Title
        tk.Label(left_panel, text="📅 Analysis History", font=("Segoe UI", 16, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(padx=12, pady=(16, 8))
        
        # Filter controls
        filter_frame = tk.Frame(left_panel, bg=self.colors['bg_card'])
        filter_frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        
        tk.Label(filter_frame, text="Filter by Threat Level:", font=("Segoe UI", 11, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(anchor=tk.W)
        
        self.threat_filter_var = tk.StringVar(value="All")
        threat_filters = ["All", "Safe", "Offensive", "Threat"]
        for threat in threat_filters:
            tk.Radiobutton(filter_frame, text=threat, variable=self.threat_filter_var, value=threat, 
                          font=("Segoe UI", 10), bg=self.colors['bg_card'], fg=self.colors['text_primary'],
                          selectcolor=self.colors['bg_secondary'], activebackground=self.colors['bg_card'],
                          activeforeground=self.colors['text_primary'], command=self.refresh_history).pack(anchor=tk.W)
        

        
        # Action buttons
        button_frame = tk.Frame(left_panel, bg=self.colors['bg_card'])
        button_frame.pack(fill=tk.X, padx=12, pady=(16, 8))
        
        refresh_btn = tk.Button(button_frame, text="🔄 Refresh", command=self.refresh_history, 
                               font=("Segoe UI", 11, "bold"), bg=self.colors['info'], fg=self.colors['text_primary'],
                               relief=tk.FLAT, bd=0, cursor="hand2", padx=12, pady=6)
        refresh_btn.pack(fill=tk.X, pady=(0, 8))
        
        export_btn = tk.Button(button_frame, text="📤 Export CSV", command=self.export_history, 
                              font=("Segoe UI", 11, "bold"), bg=self.colors['success'], fg=self.colors['text_primary'],
                              relief=tk.FLAT, bd=0, cursor="hand2", padx=12, pady=6)
        export_btn.pack(fill=tk.X, pady=(0, 8))
        
        clear_btn = tk.Button(button_frame, text="🗑️ Clear History", command=self.clear_history, 
                             font=("Segoe UI", 11, "bold"), bg=self.colors['danger'], fg=self.colors['text_primary'],
                             relief=tk.FLAT, bd=0, cursor="hand2", padx=12, pady=6)
        clear_btn.pack(fill=tk.X)
        
        # Right: History table
        right_panel = tk.Frame(history_frame, bg=self.colors['bg_primary'])
        right_panel.grid(row=0, column=1, sticky="nsew", padx=16, pady=0)
        history_frame.grid_rowconfigure(0, weight=1)
        history_frame.grid_columnconfigure(1, weight=1)
        
        # Treeview with custom styling
        style = ttk.Style()
        style.configure("History.Treeview",
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       fieldbackground=self.colors['bg_secondary'],
                       font=('Segoe UI', 10))
        style.configure("History.Treeview.Heading",
                       background=self.colors['accent'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 10, 'bold'))
        
        columns = ('Time', 'File', 'Threat Level', 'Emotion', 'Confidence', 'Duration', 'Delete')
        self.history_tree = ttk.Treeview(right_panel, columns=columns, show='headings', height=20, style="History.Treeview")
        
        for col in columns:
            if col == 'Delete':
                self.history_tree.heading(col, text="❌")
                self.history_tree.column(col, width=50, anchor='center')
            else:
                self.history_tree.heading(col, text=col, command=lambda c=col: self.sort_history(c))
                if col == 'Time':
                    self.history_tree.column(col, width=150)
                elif col == 'File':
                    self.history_tree.column(col, width=200)
                elif col == 'Duration':
                    self.history_tree.column(col, width=80)
                else:
                    self.history_tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.history_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind double-click to view details and single click for delete
        self.history_tree.bind('<Double-1>', self.view_history_details)
        self.history_tree.bind('<Button-1>', self.handle_history_click)
        
        # Status bar
        self.history_status_label = tk.Label(right_panel, text="No history entries", font=("Segoe UI", 10), 
                                            bg=self.colors['bg_primary'], fg=self.colors['text_secondary'])
        self.history_status_label.pack(anchor=tk.W, pady=(8, 0))
    
    def add_to_history(self, file_path, threat_level, emotion, confidence, duration=None, transcription=None, features=None, scan_type='single'):
        print(f"[DEBUG] add_to_history: user_id={self.user_id}, scan_type={scan_type}, file_path={file_path}, threat_level={threat_level}")
        # Save to DB
        self.db.save_scan_result(
            self.user_id,
            scan_type,
            file_path,
            threat_level,
            confidence,
            emotion,
            duration,
            transcription
        )
        print(f"[DEBUG] add_to_history: saved to DB for user_id={self.user_id}")
        self.load_history()  # Reload from DB
        self.refresh_history()
    
    def refresh_history(self):
        """Refresh the history display with current filters"""
        # Clear current display
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Apply filters
        threat_filter = self.threat_filter_var.get()
        
        filtered_history = []
        for entry in self.analysis_history:
            # Apply threat level filter
            if threat_filter != "All" and entry['threat_level'] != threat_filter:
                continue
            
            filtered_history.append(entry)
        
        # Sort by timestamp (newest first)
        filtered_history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Add to treeview
        for entry in filtered_history:
            time_str = entry['timestamp']
            duration_str = f"{entry['duration']:.1f}s" if entry['duration'] else "N/A"
            
            self.history_tree.insert('', 'end', values=(
                time_str,
                entry['file_name'],
                entry['threat_level'],
                entry['emotion'],
                f"{entry['confidence']:.2f}" if entry['confidence'] is not None else "N/A",
                duration_str,
                "❌"
            ))
        
        # Update status
        self.history_status_label.config(text=f"Showing {len(filtered_history)} of {len(self.analysis_history)} entries")
    
    def sort_history(self, column):
        """Sort history by column"""
        # Get current items
        items = [(self.history_tree.set(item, column), item) for item in self.history_tree.get_children('')]
        
        # Sort items
        items.sort()
        
        # Rearrange items in sorted positions
        for index, (val, item) in enumerate(items):
            self.history_tree.move(item, '', index)
    
    def handle_history_click(self, event):
        """Handle clicks on history tree - delete or view details"""
        region = self.history_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.history_tree.identify_column(event.x)
            item = self.history_tree.identify_row(event.y)
            
            if item and column == "#7":  # Delete column
                self.delete_history_entry(item)
            elif item:
                # Double-click for details (handled by existing method)
                pass
    
    def delete_history_entry(self, item):
        """Delete a specific history entry"""
        values = self.history_tree.item(item, 'values')
        if not values:
            return
        
        time_str = values[0]
        file_name = values[1]
        
        # Find and remove the entry
        for i, entry in enumerate(self.analysis_history):
            if (entry['timestamp'] == time_str and 
                entry['file_name'] == file_name):
                del self.analysis_history[i]
                self.save_history()
                self.refresh_history()
                break
    
    def view_history_details(self, event):
        """View detailed information for selected history entry"""
        selection = self.history_tree.selection()
        if not selection:
            return
        
        # Get selected item
        item = selection[0]
        values = self.history_tree.item(item, 'values')
        
        # Find corresponding history entry
        time_str = values[0]
        file_name = values[1]
        
        for entry in self.analysis_history:
            if (entry['timestamp'] == time_str and 
                entry['file_name'] == file_name):
                self.show_history_details(entry)
                break
    
    def show_history_details(self, entry):
        """Show detailed view of history entry"""
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Analysis Details - {entry['file_name']}")
        details_window.geometry("600x500")
        details_window.configure(bg=self.colors['bg_primary'])
        
        # Make window modal
        details_window.transient(self.root)
        details_window.grab_set()
        
        # Content frame
        content_frame = tk.Frame(details_window, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # Title
        title_label = tk.Label(content_frame, text=f"📊 Analysis Details", 
                              font=("Segoe UI", 18, "bold"), bg=self.colors['bg_primary'], fg=self.colors['text_primary'])
        title_label.pack(anchor=tk.W, pady=(0, 16))
        
        # Details text
        details_text = scrolledtext.ScrolledText(content_frame, height=20, wrap=tk.WORD, 
                                               font=("Consolas", 11), bg=self.colors['bg_secondary'], 
                                               fg=self.colors['text_primary'], relief=tk.FLAT, bd=10)
        details_text.pack(fill=tk.BOTH, expand=True)
        
        # Format details
        details = f"""File: {entry['file_path']}
Time: {entry['timestamp']}
Duration: {entry['duration']:.2f}s (if available)

Threat Analysis:
- Level: {entry['threat_level']}
- Confidence: {entry['confidence']:.3f}

Emotion Analysis:
- Dominant Emotion: {entry['emotion']}

Transcription:
{entry.get('transcription', 'No transcription available')}

Features:
{entry.get('features', 'No features available')}
"""
        
        details_text.insert(tk.END, details)
        details_text.config(state=tk.DISABLED)
        
        # Close button
        close_btn = tk.Button(content_frame, text="Close", command=details_window.destroy,
                             font=("Segoe UI", 12, "bold"), bg=self.colors['accent'], fg=self.colors['text_primary'],
                             relief=tk.FLAT, bd=0, cursor="hand2", padx=20, pady=8)
        close_btn.pack(pady=(16, 0))
    
    def export_history(self):
        """Export history to CSV file"""
        if not self.analysis_history:
            messagebox.showinfo("Info", "No history entries to export.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
            title="Export Analysis History"
        )
        
        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    # Write header
                    writer.writerow(['Timestamp', 'File', 'Threat Level', 'Emotion', 'Confidence', 'Duration', 'Transcription'])
                    
                    # Write data
                    for entry in self.analysis_history:
                        writer.writerow([
                            entry['timestamp'],
                            entry['file_path'],
                            entry['threat_level'],
                            entry['emotion'],
                            f"{entry['confidence']:.3f}",
                            f"{entry['duration']:.2f}" if entry['duration'] else "N/A",
                            entry.get('transcription', '')
                        ])
                
                messagebox.showinfo("Success", f"History exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export history: {str(e)}")
    
    def clear_history(self):
        """Clear all history entries"""
        if not self.analysis_history:
            messagebox.showinfo("Info", "No history entries to clear.")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all history entries? This action cannot be undone."):
            self.analysis_history.clear()
            self.save_history()
            self.refresh_history()
            messagebox.showinfo("Success", "History cleared successfully.")
    
    def save_history(self):
        import json
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def load_history(self):
        # Load from DB for this user
        print(f"[DEBUG] load_history: user_id={self.user_id}")
        rows = self.db.get_user_scan_history(self.user_id, limit=100)
        print(f"[DEBUG] load_history: loaded {len(rows)} rows for user_id={self.user_id}")
        self.analysis_history = []
        for row in rows:
            scan_type, content, threat_level, confidence, emotion, duration, transcription, timestamp = row
            entry = {
                'timestamp': timestamp,
                'file_path': content,
                'file_name': os.path.basename(content) if content else "Live Recording",
                'threat_level': threat_level,
                'emotion': emotion,
                'confidence': confidence,
                'duration': duration,
                'transcription': transcription,
                'features': None
            }
            self.analysis_history.append(entry)
    
    def initialize_classifier(self):
        """Initialize the voice classifier in a background thread for responsive UI"""
        # Disable analysis controls until models are loaded
        self.set_analysis_controls_state('disabled')
        self.status_label.config(text="Loading models...", fg=self.colors['warning'])
        self.progress_var.set(10)
        self.root.update()

        def load_models():
            try:
                from model.voice_model import VoiceThreatClassifier
                classifier = VoiceThreatClassifier()
                self.root.after(0, lambda: self.on_models_loaded(classifier))
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"Error: {e}", fg=self.colors['danger']))

        threading.Thread(target=load_models, daemon=True).start()

    def on_models_loaded(self, classifier):
        """Callback after models are loaded to update UI and enable controls"""
        try:
            self.voice_classifier = classifier
            self.progress_var.set(100)
            self.status_label.config(text="Models loaded successfully", fg=self.colors['success'])
            self.set_analysis_controls_state('normal')
        except tk.TclError:
            # Widget was destroyed, ignore
            pass

    def set_analysis_controls_state(self, state):
        """Enable or disable analysis controls (buttons)"""
        # Single File Analysis tab
        try:
            for btn in [self.file_entry, getattr(self, 'analyze_file_btn', None), getattr(self, 'play_audio_btn', None), getattr(self, 'show_transcription_btn', None), getattr(self, 'show_features_btn', None)]:
                if btn:
                    btn.config(state=state)
        except Exception:
            pass
        # You may need to store button references in __init__ or create_control_panel for this to work

    # In create_control_panel, store button references for easy enabling/disabling
    def create_control_panel(self, parent):
        file_label = tk.Label(parent, text="Audio File:", font=("Segoe UI", 12, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary'])
        file_label.pack(anchor=tk.W, pady=(12, 4), padx=12)
        file_entry_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        file_entry_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(file_entry_frame, textvariable=self.file_path_var, font=("Segoe UI", 11), bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=8)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        browse_btn = tk.Button(file_entry_frame, text="📁 Browse", command=self.browse_file, font=("Segoe UI", 11, "bold"), bg=self.colors['accent'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=14)
        browse_btn.pack(side=tk.RIGHT)
        self.add_tooltip(browse_btn, "Browse for an audio file to analyze")
        # Fast Mode
        self.fast_mode_var = tk.BooleanVar(value=False)
        fast_mode_check = tk.Checkbutton(parent, text="⚡ Fast Mode (skip deep models)", variable=self.fast_mode_var, font=("Segoe UI", 10, "bold"), bg=self.colors['bg_card'], fg=self.colors['accent'], selectcolor=self.colors['bg_secondary'], activebackground=self.colors['bg_card'], activeforeground=self.colors['accent'])
        fast_mode_check.pack(anchor=tk.W, padx=12, pady=(0, 12))
        self.add_tooltip(fast_mode_check, "Enable for faster but less accurate analysis")
        # Analysis Controls
        self.analyze_file_btn = tk.Button(parent, text="🔍 Analyze File", command=self.analyze_file, font=("Segoe UI", 12, "bold"), bg=self.colors['info'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=14, pady=8, activebackground=self.colors['accent'])
        self.analyze_file_btn.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.add_tooltip(self.analyze_file_btn, "Analyze the selected audio file")
        self.play_audio_btn = tk.Button(parent, text="🎵 Play Audio", command=self.play_audio, font=("Segoe UI", 12, "bold"), bg=self.colors['success'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=14, pady=8, activebackground=self.colors['accent'])
        self.play_audio_btn.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.add_tooltip(self.play_audio_btn, "Play the selected audio file")
        self.show_transcription_btn = tk.Button(parent, text="📝 Show Transcription", command=self.show_transcription, font=("Segoe UI", 12, "bold"), bg=self.colors['warning'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=14, pady=8, activebackground=self.colors['accent'])
        self.show_transcription_btn.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.add_tooltip(self.show_transcription_btn, "Show the transcription of the audio")
        self.show_features_btn = tk.Button(parent, text="📊 Show Features", command=self.show_features, font=("Segoe UI", 12, "bold"), bg=self.colors['accent'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=0, cursor="hand2", padx=14, pady=8, activebackground=self.colors['accent'])
        self.show_features_btn.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.add_tooltip(self.show_features_btn, "Show extracted audio features")
        # Status
        self.status_label = tk.Label(parent, text="Ready", font=("Segoe UI", 13, "bold"), bg=self.colors['bg_card'], fg=self.colors['success'])
        self.status_label.pack(padx=12, pady=(16, 8))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(parent, variable=self.progress_var, maximum=100, length=300)
        self.progress_bar.pack(padx=12, pady=(0, 12))

    def browse_file(self):
        """Browse for audio file with modern dialog"""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg"),
                ("WAV files", "*.wav"),
                ("MP3 files", "*.mp3"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.audio_file_var.set(file_path)
            # Enable the analyze, transcript, and play buttons
            self.analyze_btn.config(state="normal")
            self.transcript_btn.config(state="normal")
            self.play_btn.config(state="normal")
    
    def analyze_file(self):
        file_path = self.audio_file_var.get()
        if not file_path:
            self.result_label.config(text="Result: No file selected")
            return
        # Run analysis in a background thread
        threading.Thread(target=self._analyze_file_thread, args=(file_path,), daemon=True).start()

    def play_audio_file(self):
        import os
        import soundfile as sf
        import sounddevice as sd
        file_path = self.audio_file_var.get()
        print(f"[DEBUG] Trying to play: {file_path}")
        if not file_path:
            self.status_label.config(text="No file selected", fg=self.colors['danger'])
            return
        if not os.path.exists(file_path):
            print("[DEBUG] File does not exist!")
            self.status_label.config(text="File does not exist!", fg=self.colors['danger'])
            return
        if getattr(self, 'is_playing_audio', False):
            self.stop_audio_file()
            return

        def play():
            try:
                self.is_playing_audio = True
                self.play_btn.config(text="⏹️ Stop Audio", command=self.stop_audio_file, bg="#e94560", fg="white")
                self.status_label.config(text="Playing audio...", fg=self.colors['info'])
                ext = os.path.splitext(file_path)[1].lower()
                if ext == ".wav":
                    print("[DEBUG] Using sounddevice for WAV playback.")
                    data, samplerate = sf.read(file_path)
                    sd.play(data, samplerate)
                    sd.wait()  # Wait until playback is finished
                else:
                    print("[DEBUG] Using playsound fallback.")
                    from playsound import playsound
                playsound(file_path)
            except Exception as e:
                self.status_label.config(text=f"Playback error: {e}", fg=self.colors['danger'])
                import tkinter.messagebox as messagebox
                messagebox.showerror("Playback Error", f"Could not play audio:\n{e}")
            finally:
                self.is_playing_audio = False
                self.play_btn.config(text="\U0001F3B5 Play Audio", command=self.play_audio_file, bg="#51cf66", fg="#232946")
                self.status_label.config(text="Audio stopped", fg=self.colors['info'])

        self.audio_thread = threading.Thread(target=play, daemon=True)
        self.audio_thread.start()

    def stop_audio_file(self):
        # playsound cannot actually stop playback, but we reset the button
        self.is_playing_audio = False
        self.play_btn.config(text="\U0001F3B5 Play Audio", command=self.play_audio_file, bg="#51cf66", fg="#232946")
        self.status_label.config(text="Audio stopped", fg=self.colors['info'])

    def transcribe_audio_file(self):
        file_path = self.audio_file_var.get()
        if not file_path:
            self.status_label.config(text="No file selected", fg=self.colors['danger'])
            return
        def do_transcribe():
            try:
                self.status_label.config(text="Transcribing...", fg=self.colors['warning'])
                transcript = self.voice_classifier.transcribe_audio(file_path)
                self.status_label.config(text="Transcript ready", fg=self.colors['success'])
                self.root.after(0, lambda: self.show_transcript_popup(transcript))
            except Exception as e:
                self.status_label.config(text=f"Transcription error: {e}", fg=self.colors['danger'])
        threading.Thread(target=do_transcribe, daemon=True).start()

    def show_transcript_popup(self, transcript):
        popup = tk.Toplevel(self.root)
        popup.title("Transcript")
        popup.configure(bg=self.colors['bg_primary'])
        popup.geometry("600x400")
        label = tk.Label(popup, text="Transcript", font=("Segoe UI", 16, "bold"), bg=self.colors['bg_primary'], fg=self.colors['accent'])
        label.pack(pady=10)
        text = tk.Text(popup, wrap=tk.WORD, font=("Consolas", 12), bg="#fff", fg="#232946")
        text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        text.insert(tk.END, transcript)
        text.config(state=tk.DISABLED)
        close_btn = tk.Button(popup, text="Close", command=popup.destroy, font=("Segoe UI", 12, "bold"), bg=self.colors['danger'], fg="white")
        close_btn.pack(pady=10)

    def _analyze_file_thread(self, file_path):
        """Analyze file in background thread with progress updates"""
        try:
            self.status_label.config(text="Analyzing...", fg=self.colors['warning'])
            self.progress_var.set(20)
            self.root.update()
            # Perform analysis
            label, emoji, confidence = self.voice_classifier.predict(file_path)
            self.progress_var.set(60)
            self.root.update()
            # Get detailed analysis
            voice_analysis = self.voice_classifier.analyze_voice_characteristics(file_path)
            emotion_scores = self.voice_classifier.analyze_emotion(file_path)
            transcription = self.voice_classifier.transcribe_audio(file_path)
            features = self.voice_classifier.extract_audio_features(file_path)
            self.progress_var.set(90)
            self.root.update()
            # Update GUI in main thread
            self.root.after(0, lambda: self._update_analysis_results(
                label, emoji, confidence, voice_analysis, emotion_scores, 
                transcription, features
            ))
        except Exception as e:
            self.root.after(0, lambda e=e: self._handle_analysis_error(str(e)))
    
    def _update_analysis_results(self, label, emoji, confidence, voice_analysis, emotion_scores, transcription, features):
        # Determine dominant emotion and its confidence
        dominant_emotion = label
        threat_level = self.map_emotion_to_threat(dominant_emotion)
        dominant_confidence = confidence
        # Play beep feedback only (removed .wav sound)
        self.play_beep(threat_level)
        
        # Map emotion to threat level
        threat_level = self.map_emotion_to_threat(dominant_emotion)
        
        # Add to history
        file_path = self.audio_file_var.get()
        duration = features.get('duration', None) if features else None
        self.add_to_history(file_path, threat_level, dominant_emotion, dominant_confidence, duration, transcription, features)
        
        # Show results in the right panel (update both result_label and emotion_text)
        self.result_label.config(text=f"{emoji} {threat_level}")
        self.emotion_text.config(state="normal")
        self.emotion_text.delete("1.0", tk.END)
        if emotion_scores:
            for emotion, score in emotion_scores.items():
                self.emotion_text.insert(tk.END, f"{emotion}: {score:.2f}\n")
        self.emotion_text.insert(tk.END, f"\nTranscript:\n{transcription}\n")
        self.emotion_text.insert(tk.END, f"\nAnalysis: {voice_analysis}\n")
        self.emotion_text.insert(tk.END, f"\nFeatures: {features}\n")
        self.emotion_text.config(state="disabled")
        # Show alert if Threat or Offensive
        if threat_level in ("Threat", "Offensive"):
            self.show_threat_alert(f"Alert: Detected {dominant_emotion} ({threat_level}) in voice!")
        self.status_label.config(text="Analysis completed", fg=self.colors['success'])

    def _handle_analysis_error(self, error_msg):
        """Handle analysis errors with user-friendly messages"""
        self.status_label.config(text=f"Analysis failed: {error_msg}", fg=self.colors['danger'])
        self.progress_var.set(0)
        messagebox.showerror("Analysis Error", f"Failed to analyze file: {error_msg}")
    
    def _get_color_for_label(self, label):
        """Get color for threat label"""
        if label == "Safe":
            return self.colors['success']
        elif label == "Offensive":
            return self.colors['warning']
        else:
            return self.colors['danger']
    
    def _get_emotion_color(self, emotion):
        """Get color for emotion display"""
        emotion_colors = {
            'happy': self.colors['success'],
            'sad': self.colors['info'],
            'angry': self.colors['danger'],
            'fear': self.colors['warning'],
            'disgust': self.colors['danger'],
            'surprise': self.colors['accent'],
            'neutral': self.colors['text_secondary']
        }
        return emotion_colors.get(emotion.lower(), self.colors['text_primary'])
    
    def _get_toxicity_color(self, score):
        """Get color for toxicity score"""
        if score > 0.7:
            return self.colors['danger']
        elif score > 0.4:
            return self.colors['warning']
        else:
            return self.colors['success']
    
    def _get_sentiment_color(self, sentiment):
        """Get color for sentiment display"""
        if sentiment.lower() == 'positive':
            return self.colors['success']
        elif sentiment.lower() == 'negative':
            return self.colors['danger']
        else:
            return self.colors['text_secondary']
    
    def play_audio(self):
        """Play the selected audio file with status updates"""
        file_path = self.file_path_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid audio file")
            return
        
        try:
            self.status_label.config(text="Playing audio...", fg=self.colors['info'])
            if _HAS_PYGAME:
                try:
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.play()
                    self.is_playing_audio = True
                    self.play_audio_btn.config(text="⏹️ Stop Audio", bg=self.colors['danger'])
                    self.status_label.config(text="Audio playing", fg=self.colors['info'])
                    self.root.after(100, self.check_audio_playing)
                except Exception as e:
                    print(f"[WARN] pygame playback failed: {e}")
                    messagebox.showerror("Error", f"Could not play audio with pygame: {e}")
            else:
                # Inform user that pygame is required for this playback path
                messagebox.showwarning("Audio Unavailable", "Audio playback via pygame is not available. Install 'pygame' to enable audio playback.")
        except Exception as e:
            self.status_label.config(text="Audio play failed", fg=self.colors['danger'])
            messagebox.showerror("Error", f"Could not play audio: {e}")

    def toggle_play_audio(self):
        if not self.is_playing_audio:
            self.play_audio()
        else:
            self.stop_audio()

    def stop_audio(self):
        try:
            if _HAS_PYGAME:
                try:
                    pygame.mixer.music.stop()
                except Exception as e:
                    print(f"[WARN] pygame stop failed: {e}")
            self.is_playing_audio = False
            self.play_audio_btn.config(text="🎵 Play Audio", bg=self.colors['success'])
            self.status_label.config(text="Audio stopped", fg=self.colors['warning'])
        except Exception as e:
            self.status_label.config(text="Audio stop failed", fg=self.colors['danger'])
            messagebox.showerror("Error", f"Could not stop audio: {e}")

    def check_audio_playing(self):
        try:
            if _HAS_PYGAME:
                try:
                    if self.is_playing_audio and not pygame.mixer.music.get_busy():
                        self.stop_audio()
                    elif self.is_playing_audio:
                        self.root.after(100, self.check_audio_playing)
                except Exception:
                    pass
        except Exception:
            pass
    
    def show_transcription(self):
        """Show transcription in a modern popup window"""
        file_path = self.file_path_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid audio file")
            return
        
        try:
            transcription = self.voice_classifier.transcribe_audio(file_path)
            
            # Create modern popup window
            window = tk.Toplevel(self.root)
            window.title("🎤 Speech Transcription")
            window.geometry("700x500")
            window.configure(bg=self.colors['bg_primary'])
            window.resizable(True, True)
            
            # Center the window
            window.transient(self.root)
            window.grab_set()
            
            # Header
            header = tk.Frame(window, bg=self.colors['bg_secondary'], height=60)
            header.pack(fill=tk.X)
            header.pack_propagate(False)
            
            title = tk.Label(header, text="Speech Transcription", 
                           font=("Segoe UI", 18, "bold"),
                           bg=self.colors['bg_secondary'], 
                           fg=self.colors['text_primary'])
            title.pack(expand=True)
            
            # Content
            content = tk.Frame(window, bg=self.colors['bg_primary'])
            content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            text_widget = scrolledtext.ScrolledText(
                content, 
                wrap=tk.WORD, 
                font=("Segoe UI", 12),
                bg=self.colors['bg_secondary'],
                fg=self.colors['text_primary'],
                relief=tk.FLAT,
                bd=10
            )
            text_widget.pack(fill=tk.BOTH, expand=True)
            
            if transcription:
                text_widget.insert(tk.END, transcription)
            else:
                text_widget.insert(tk.END, "⚠️ No transcription available")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to transcribe audio: {str(e)}")
    
    def show_features(self):
        """Show extracted features in a modern popup window"""
        file_path = self.file_path_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid audio file")
            return
        
        try:
            features = self.voice_classifier.extract_audio_features(file_path)
            
            # Create modern popup window
            window = tk.Toplevel(self.root)
            window.title("🔧 Extracted Audio Features")
            window.geometry("900x700")
            window.configure(bg=self.colors['bg_primary'])
            window.resizable(True, True)
            
            # Center the window
            window.transient(self.root)
            window.grab_set()
            
            # Header
            header = tk.Frame(window, bg=self.colors['bg_secondary'], height=60)
            header.pack(fill=tk.X)
            header.pack_propagate(False)
            
            title = tk.Label(header, text="Extracted Audio Features", 
                           font=("Segoe UI", 18, "bold"),
                           bg=self.colors['bg_secondary'], 
                           fg=self.colors['text_primary'])
            title.pack(expand=True)
            
            # Content
            content = tk.Frame(window, bg=self.colors['bg_primary'])
            content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            text_widget = scrolledtext.ScrolledText(
                content, 
                wrap=tk.WORD, 
                font=("Consolas", 10),
                bg=self.colors['bg_secondary'],
                fg=self.colors['text_primary'],
                relief=tk.FLAT,
                bd=10
            )
            text_widget.pack(fill=tk.BOTH, expand=True)
            
            if features:
                text_widget.insert(tk.END, "🔧 Extracted Audio Features:\n\n")
                for key, value in features.items():
                    if isinstance(value, np.ndarray):
                        text_widget.insert(tk.END, f"• {key}: Array of shape {value.shape}\n")
                        if len(value) <= 20:  # Show small arrays
                            text_widget.insert(tk.END, f"  Values: {value}\n")
                    else:
                        text_widget.insert(tk.END, f"• {key}: {value:.6f}\n")
            else:
                text_widget.insert(tk.END, "⚠️ No features extracted")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract features: {str(e)}")
    
    def toggle_recording(self):
        """Toggle recording state with visual feedback"""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording audio with visual feedback"""
        try:
            self.audio_data = []
            self.recording = True
            
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024,
                stream_callback=self._audio_callback
            )
            
            self.stream.start_stream()
            self.record_button.config(text="⏹️ Stop Recording", bg=self.colors['danger'])
            self.live_status_label.config(text="Recording...", fg=self.colors['danger'])
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start recording: {str(e)}")
    
    def stop_recording(self):
        """Stop recording audio with visual feedback"""
        try:
            self.recording = False
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            self.record_button.config(text="🎙️ Start Recording", bg=self.colors['success'])
            self.live_status_label.config(text="Recording stopped", fg=self.colors['info'])
            
            # Analyze the recording
            if self.audio_data:
                self.analyze_recording()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop recording: {str(e)}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback for recording"""
        if self.recording:
            self.audio_data.append(in_data)
        return (in_data, pyaudio.paContinue)
    
    def analyze_recording(self):
        """Analyze the recorded audio with visual feedback"""
        if not self.audio_data:
            return
        
        try:
            # Save recording to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                with wave.open(tmp_file.name, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(self.audio_data))
                
                # Analyze the recording
                label, emoji, confidence = self.voice_classifier.predict(tmp_file.name)
                voice_analysis = self.voice_classifier.analyze_voice_characteristics(tmp_file.name)
                emotion_scores = self.voice_classifier.analyze_emotion(tmp_file.name)
                
                # Update live results with color coding
                self.live_result_label.config(text=f"{emoji} {label}", fg=self._get_color_for_label(label))
                
                # Update voice characteristics
                self.live_voice_text.delete(1.0, tk.END)
                if voice_analysis:
                    self.live_voice_text.insert(tk.END, "🎵 Voice Analysis:\n\n")
                    for key, value in voice_analysis.items():
                        self.live_voice_text.insert(tk.END, f"• {key}: {value:.3f}\n")
                
                # Update emotion analysis
                self.live_emotion_text.delete(1.0, tk.END)
                if emotion_scores:
                    self.live_emotion_text.insert(tk.END, "😊 Emotion Analysis:\n\n")
                    for emotion, score in emotion_scores.items():
                        self.live_emotion_text.insert(tk.END, f"• {emotion}: {score:.3f}\n")
                
                # Clean up
                os.unlink(tmp_file.name)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze recording: {str(e)}")
    
    def play_recording(self):
        """Play the recorded audio with status updates"""
        if not self.audio_data:
            messagebox.showinfo("Info", "No recording to play")
            return
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                with wave.open(tmp_file.name, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(self.audio_data))
                
                if _HAS_PYGAME:
                    try:
                        pygame.mixer.music.load(tmp_file.name)
                        pygame.mixer.music.play()
                    except Exception as e:
                        print(f"[WARN] pygame playback failed for temp file: {e}")
                else:
                    messagebox.showwarning("Audio Unavailable", "Audio playback requires 'pygame'. Install it to enable playback.")
                
                # Clean up
                os.unlink(tmp_file.name)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play recording: {str(e)}")
    
    def save_recording(self):
        """Save the recorded audio with modern dialog"""
        if not self.audio_data:
            messagebox.showinfo("Info", "No recording to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Recording",
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with wave.open(file_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(self.audio_data))
                
                messagebox.showinfo("Success", f"Recording saved to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save recording: {str(e)}")
    
    def select_folder(self):
        """Select folder for batch processing with modern dialog"""
        folder_path = filedialog.askdirectory(title="Select Folder with Audio Files")
        if folder_path:
            self.folder_path_var.set(folder_path)
    
    def load_model_info(self):
        """Load and display model information with formatted text"""
        try:
            if self.voice_classifier:
                model_info = self.voice_classifier.get_model_info()
                
                self.model_info_text.delete(1.0, tk.END)
                self.model_info_text.insert(tk.END, "🎤 Enhanced Voice Threat Classifier\n")
                self.model_info_text.insert(tk.END, "=" * 50 + "\n\n")
                
                for key, value in model_info.items():
                    if key == 'features':
                        self.model_info_text.insert(tk.END, f"🔧 {key}:\n")
                        for feature in value:
                            self.model_info_text.insert(tk.END, f"  • {feature}\n")
                    elif key == 'pretrained_models':
                        self.model_info_text.insert(tk.END, f"🤖 {key}:\n")
                        for model in value:
                            self.model_info_text.insert(tk.END, f"  • {model}\n")
                    else:
                        self.model_info_text.insert(tk.END, f"📊 {key}: {value}\n")
                    self.model_info_text.insert(tk.END, "\n")
            else:
                self.model_info_text.insert(tk.END, "⚠️ Model not loaded")
                
        except Exception as e:
            self.model_info_text.insert(tk.END, f"❌ Error loading model info: {str(e)}")
    
    def on_back_from_text_analysis(self):
        """Handle back button from text analysis tab"""
        # If running as a sub-frame in a parent, call parent's show_main_menu or similar
        if hasattr(self.root, 'show_main_menu'):
            self.root.show_main_menu()
        else:
            # If standalone, just destroy the window
            self.root.destroy()
    
    def cleanup(self):
        """Cleanup resources with proper error handling"""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            
            if self.audio:
                self.audio.terminate()
            
            if _HAS_PYGAME:
                try:
                    pygame.mixer.quit()
                except Exception:
                    pass
            
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def add_tooltip(self, widget, text):
        def on_enter(event):
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.withdraw()
            self.tooltip.overrideredirect(True)
            label = tk.Label(self.tooltip, text=text, bg="#333", fg="#fff", font=("Segoe UI", 10), padx=6, pady=2)
            label.pack()
            x = widget.winfo_rootx() + 40
            y = widget.winfo_rooty() + 20
            self.tooltip.geometry(f"+{x}+{y}")
            self.tooltip.deiconify()
        def on_leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def start_chat_recording(self):
        self.chat_recording = True
        self.chat_audio_data = []
        # Safely update UI elements if they exist
        if hasattr(self, 'chat_status_label'):
            try:
                self.chat_status_label.config(text="Recording...", fg=self.colors['warning'])
            except Exception:
                pass
        for attr in ('chat_record_button', 'chat_stop_button', 'chat_analyze_button', 'chat_play_button', 'chat_save_button'):
            if hasattr(self, attr):
                try:
                    if attr == 'chat_record_button':
                        getattr(self, attr).config(state='disabled')
                    else:
                        getattr(self, attr).config(state='normal' if attr == 'chat_stop_button' else 'disabled')
                except Exception:
                    pass
        threading.Thread(target=self._chat_record_thread, daemon=True).start()

    def _chat_record_thread(self):
        stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=self.sample_rate, input=True, frames_per_buffer=1024)
        frames = []
        for _ in range(0, int(self.sample_rate / 1024 * 5)):
            if not self.chat_recording:
                break
            data = stream.read(1024)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        self.chat_audio_data = frames
        self.chat_recording = False
        self.root.after(0, self._on_chat_recording_done)

    def stop_chat_recording(self):
        self.chat_recording = False
        if hasattr(self, 'chat_status_label'):
            try:
                self.chat_status_label.config(text="Stopped", fg=self.colors['danger'])
            except Exception:
                pass
        for attr in ('chat_record_button', 'chat_stop_button', 'chat_analyze_button', 'chat_play_button', 'chat_save_button'):
            if hasattr(self, attr):
                try:
                    # restore sensible defaults
                    if attr == 'chat_stop_button':
                        getattr(self, attr).config(state='disabled')
                    else:
                        getattr(self, attr).config(state='normal')
                except Exception:
                    pass

    def _on_chat_recording_done(self):
        if hasattr(self, 'chat_status_label'):
            try:
                self.chat_status_label.config(text="Recording complete", fg=self.colors['success'])
            except Exception:
                pass
        for attr in ('chat_record_button', 'chat_stop_button', 'chat_analyze_button', 'chat_play_button', 'chat_save_button'):
            if hasattr(self, attr):
                try:
                    if attr == 'chat_stop_button':
                        getattr(self, attr).config(state='disabled')
                    else:
                        getattr(self, attr).config(state='normal')
                except Exception:
                    pass

    def play_chat_clip(self):
        if not self.chat_audio_data:
            return
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        wf = wave.open(temp_file.name, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(self.chat_audio_data))
        wf.close()
        pygame.mixer.music.load(temp_file.name)
        pygame.mixer.music.play()
        temp_file.close()
        # Optionally delete temp file after playback

    def save_chat_clip(self):
        if not self.chat_audio_data:
            return
        file_path = filedialog.asksaveasfilename(defaultextension='.wav', filetypes=[('WAV files', '*.wav')])
        if file_path:
            wf = wave.open(file_path, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.chat_audio_data))
            wf.close()
            self.chat_status_label.config(text=f"Saved: {os.path.basename(file_path)}", fg=self.colors['success'])

    def analyze_chat_clip(self):
        if not self.chat_audio_data:
            return
        self.chat_status_label.config(text="Analyzing...", fg=self.colors['info'])
        self.chat_analyze_button.config(state='disabled')
        threading.Thread(target=self._analyze_chat_clip_thread, daemon=True).start()

    def _analyze_chat_clip_thread(self):
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        wf = wave.open(temp_file.name, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(self.chat_audio_data))
        wf.close()
        # Use the same analysis pipeline as analyze_file
        try:
            result = self.voice_classifier.analyze(temp_file.name, fast_mode=False)
            label = result.get('label', 'Unknown')
            confidence = result.get('confidence', 0)
            emotion = result.get('emotion', 'Unknown')
            transcription = result.get('transcription', '')
            features = result.get('features', {})
            self.root.after(0, lambda: self._update_chat_analysis_results(label, confidence, emotion, transcription, features))
        except Exception as e:
            self.root.after(0, lambda: self.chat_status_label.config(text=f"Error: {e}", fg=self.colors['danger']))
        finally:
            temp_file.close()
            os.unlink(temp_file.name)

    def _update_chat_analysis_results(self, label, confidence, emotion, transcription, features):
        self.chat_result_label.config(text=f"Label: {label}")
        self.chat_confidence_label.config(text=f"Confidence: {confidence:.2f}")
        self.chat_emotion_label.config(text=f"Emotion: {emotion}")
        self.chat_transcription_text.delete('1.0', tk.END)
        self.chat_transcription_text.insert(tk.END, transcription)
        self.chat_features_text.delete('1.0', tk.END)
        self.chat_features_text.insert(tk.END, str(features))
        self.chat_status_label.config(text="Analysis complete", fg=self.colors['success'])
        self.chat_analyze_button.config(state='normal')

    def play_log_entry(self):
        selected = self.log_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a log entry to play.")
            return
        file_name = self.log_tree.item(selected[0], "values")[0]
        if not os.path.exists(file_name):
            messagebox.showerror("Error", f"File not found: {file_name}")
            return
        try:
            # Prefer pygame playback if available
            try:
                pygame.mixer.music.load(file_name)
                pygame.mixer.music.play()
                return
            except Exception:
                pass
            # Fallback to playsound
            try:
                playsound(file_name)
            except Exception as e:
                messagebox.showerror("Error", f"Could not play file: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not play file: {e}")

    def delete_log_entry(self):
        selected = self.log_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a log entry to delete.")
            return
        self.log_tree.delete(selected[0])
        idx = int(selected[0][1:], 16) if selected[0].startswith('I') else int(selected[0])
        if 0 <= idx < len(self.session_log):
            del self.session_log[idx]

    def clear_log(self):
        self.log_tree.delete(*self.log_tree.get_children())
        self.session_log.clear()

    def export_log(self):
        if not self.session_log:
            messagebox.showinfo("Info", "No log entries to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')])
        if file_path:
            import csv
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["File", "Label", "Confidence", "Time"])
                writer.writerows(self.session_log)
            messagebox.showinfo("Exported", f"Log exported to {file_path}")

    def play_audio_file(self):
        if self.is_playing_audio:
            return
        self.is_playing_audio = True
        self.play_btn.config(text="⏹️ Stop Audio", bg=self.colors['danger'])
        # Start playing audio (replace with your playback logic)
        # Example: self.audio_player.play(self.audio_file_var.get(), on_end=self.on_audio_playback_end)
        # For demonstration, simulate playback end after 3 seconds
        self.root.after(3000, self.on_audio_playback_end)

    def stop_audio_file(self):
        if not self.is_playing_audio:
            return
        self.is_playing_audio = False
        self.play_btn.config(text="🎵 Play Audio", bg=self.colors['success'])
        # Stop audio playback logic here

    def on_audio_playback_end(self):
        self.is_playing_audio = False
        self.play_btn.config(text="🎵 Play Audio", bg=self.colors['success'])
        # Ensure audio is stopped

    def show_threat_alert(self, message):
        alert = tk.Toplevel(self.root)
        alert.title("Threat Alert")
        alert.geometry("400x200")
        alert.configure(bg=self.colors['danger'])
        tk.Label(alert, text=message, font=("Segoe UI", 16, "bold"), bg=self.colors['danger'], fg="#fff").pack(pady=30)
        ok_btn = tk.Button(alert, text="OK", command=alert.destroy, font=("Segoe UI", 14, "bold"), bg=self.colors['bg_card'], fg="#fff", relief=tk.FLAT, bd=0, cursor="hand2", padx=20, pady=10)
        ok_btn.pack(pady=20)

    def toggle_live_monitoring(self):
        if not self.is_live_monitoring:
            self.start_live_monitoring()
        else:
            self.stop_live_monitoring()

    def start_live_monitoring(self):
        self.is_live_monitoring = True
        self.live_monitor_btn.config(text="⏹ Stop Monitoring", bg=self.colors['danger'])
        self.live_status_label.config(text="Listening...", fg=self.colors['info'])
        # Start a thread for real-time mic monitoring and analysis
        import threading
        threading.Thread(target=self._live_monitor_thread, daemon=True).start()

    def stop_live_monitoring(self):
        self.is_live_monitoring = False
        self.live_monitor_btn.config(text="🎙️ Start Monitoring", bg=self.colors['success'])
        self.live_status_label.config(text="Stopped", fg=self.colors['warning'])

    def _live_monitor_thread(self):
        import time
        import numpy as np
        import pyaudio
        import queue
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        
        # Get selected mic index
        try:
            selected = self.mic_var.get()
            device_index = int(selected.split(':')[0])
            print(f"DEBUG: Using microphone device index: {device_index}")
        except Exception as e:
            print(f"DEBUG: Error getting device index: {e}")
            device_index = None
        
        try:
            mic = sr.Microphone(device_index=device_index)
            print(f"DEBUG: Microphone initialized successfully")
        except OSError as e:
            print(f"DEBUG: Microphone error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Microphone Error", "No microphone detected. Please connect a microphone and try again."))
            self.root.after(0, lambda: self.live_status_label.config(text="No microphone detected", fg=self.colors['danger']))
            self.is_live_monitoring = False
            self.root.after(0, lambda: self.live_monitor_btn.config(text="🎙️ Start Monitoring", bg=self.colors['success']))
            return
        print("DEBUG: Starting live monitoring loop")
        while self.is_live_monitoring:
            try:
                print("DEBUG: Listening for audio...")
                with mic as source:
                    audio = recognizer.listen(source, phrase_time_limit=4)
                print("DEBUG: Audio captured, length:", len(audio.get_wav_data()))
                
                # Transcribe
                transcript = ""
                try:
                    transcript = recognizer.recognize_google(audio)
                    print("DEBUG: Transcript:", transcript)
                except Exception as e:
                    print(f"DEBUG: Transcription error: {e}")
                    transcript = "[Unrecognized]"
                # Analyze emotion by saving audio to temp file first
                import tempfile
                import wave
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                with wave.open(temp_file.name, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(audio.get_wav_data())
                
                try:
                    print("DEBUG: Analyzing emotion...")
                    emotion_scores = self.voice_classifier.analyze_emotion(temp_file.name)
                    print("DEBUG: Emotion scores:", emotion_scores)
                    if emotion_scores:
                        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
                        print("DEBUG: Dominant emotion:", dominant_emotion)
                    else:
                        dominant_emotion = "neutral"
                        print("DEBUG: No emotion scores, using neutral")
                except Exception as e:
                    print(f"DEBUG: Emotion analysis error: {e}")
                    dominant_emotion = "neutral"
                    emotion_scores = {"neutral": 1.0}
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
                # --- Toxicity detection integration ---
                threat_level = None
                if transcript and transcript != "[Unrecognized]":
                    text_threat, _ = self.text_threat_classifier.predict(transcript)
                    print(f"DEBUG: Text threat classifier result: {text_threat}")
                    if text_threat in ("Threat", "Offensive"):
                        # Override dominant_emotion, threat_level, and emotion_scores
                        dominant_emotion = text_threat
                        threat_level = text_threat
                        emotion_scores = {text_threat: 1.0}
                # Update GUI
                self.root.after(0, lambda t=transcript, e=dominant_emotion, s=emotion_scores, tl=threat_level: self._update_live_monitor_results(t, e, s, tl))
                # Alert if needed
                alert_emotions = ("aggression", "anger", "sad", "sadness", "fear", "Threat", "Offensive")
                if str(dominant_emotion).strip().lower() in [a.lower() for a in alert_emotions]:
                    self.root.after(0, lambda e=dominant_emotion: self.show_threat_alert(f"Alert: Detected {e} in voice!"))
                time.sleep(0.5)
            except Exception as ex:
                error_message = str(ex)
                if self.is_live_monitoring:
                    self.root.after(0, lambda msg=error_message: self.live_status_label.config(text=f"Error: {msg}", fg=self.colors['danger']))
                break

    def _update_live_monitor_results(self, transcript, dominant_emotion, emotion_scores, threat_level=None):
        import datetime
        self.live_emotion_label.config(text=f"Dominant Emotion: {dominant_emotion}")
        self.live_transcript_text.config(state=tk.NORMAL)
        self.live_transcript_text.delete(1.0, tk.END)
        self.live_transcript_text.insert(tk.END, transcript)
        self.live_transcript_text.config(state=tk.DISABLED)
        self.live_emotion_scores_text.config(state=tk.NORMAL)
        self.live_emotion_scores_text.delete(1.0, tk.END)
        self.live_emotion_scores_text.insert(tk.END, str(emotion_scores))
        self.live_emotion_scores_text.config(state=tk.DISABLED)
        # Map emotion to threat level if not overridden
        if not threat_level:
            threat_level = self.map_emotion_to_threat(dominant_emotion)
        # Play beep feedback only (removed .wav sound)
        self.play_beep(threat_level)
        # Add to session segment table
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        confidence = max(emotion_scores.values()) if emotion_scores and isinstance(emotion_scores, dict) else 0.0
        segment = {
            "Timestamp": timestamp,
            "Emotion": dominant_emotion,
            "Threat": threat_level,
            "Confidence": f"{confidence:.2f}",
            "Transcript": transcript,
            "Scores": emotion_scores
        }
        self.live_segments.append(segment)
        self.live_segment_tree.insert('', 'end', values=(timestamp, dominant_emotion, threat_level, f"{confidence:.2f}", transcript))
        # Add live monitoring results to history (only if significant emotion detected)
        if emotion_scores and isinstance(emotion_scores, dict):
            max_confidence = max(emotion_scores.values())
            if max_confidence > 0.3:
                self.add_to_history(
                    file_path=None,
                    threat_level=threat_level,
                    emotion=dominant_emotion,
                    confidence=max_confidence,
                    duration=4.0,
                    transcription=transcript,
                    features=emotion_scores,
                    scan_type='live'
                )
        # Show alert if Threat or Offensive
        if threat_level in ("Threat", "Offensive"):
            self.show_threat_alert(f"Alert: Detected {dominant_emotion} ({threat_level}) in voice!")

    def map_emotion_to_threat(self, emotion):
        emotion = str(emotion).strip().lower()
        if emotion in ("anger", "aggression", "fear", "sexual", "explicit", "threat", "violence", "terror", "harassment"):
            return "Threat"
        elif emotion in ("disgust", "sad", "sadness", "offensive", "hate", "abuse", "bullying", "toxic"):
            return "Offensive"
        else:
            return "Safe"

    def show_live_segment_details(self, event):
        selected = self.live_segment_tree.selection()
        if not selected:
            return
        item = selected[0]
        values = self.live_segment_tree.item(item, 'values')
        # Find the segment dict
        segment = None
        for seg in self.live_segments:
            if seg["Timestamp"] == values[0] and seg["Emotion"] == values[1] and seg["Transcript"] == values[4]:
                segment = seg
                break
        if not segment:
            return
        # Show popup with details
        popup = tk.Toplevel(self.root)
        popup.title(f"Segment Details - {segment['Timestamp']}")
        popup.geometry("500x400")
        popup.configure(bg=self.colors['bg_card'])
        tk.Label(popup, text=f"Timestamp: {segment['Timestamp']}", font=("Segoe UI", 12, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(anchor=tk.W, padx=16, pady=(16, 4))
        tk.Label(popup, text=f"Emotion: {segment['Emotion']}", font=("Segoe UI", 12), bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(anchor=tk.W, padx=16, pady=4)
        tk.Label(popup, text=f"Threat: {segment['Threat']}", font=("Segoe UI", 12), bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(anchor=tk.W, padx=16, pady=4)
        tk.Label(popup, text=f"Confidence: {segment['Confidence']}", font=("Segoe UI", 12), bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(anchor=tk.W, padx=16, pady=4)
        tk.Label(popup, text="Transcript:", font=("Segoe UI", 12, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(anchor=tk.W, padx=16, pady=(12, 0))
        transcript_box = scrolledtext.ScrolledText(popup, height=4, wrap=tk.WORD, font=("Consolas", 11), bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=10)
        transcript_box.pack(fill=tk.X, padx=16, pady=(0, 12))
        transcript_box.insert(tk.END, segment['Transcript'])
        transcript_box.config(state=tk.DISABLED)
        tk.Label(popup, text="All Emotion Scores:", font=("Segoe UI", 12, "bold"), bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(anchor=tk.W, padx=16, pady=(8, 0))
        scores_box = scrolledtext.ScrolledText(popup, height=4, wrap=tk.WORD, font=("Consolas", 11), bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], relief=tk.FLAT, bd=10)
        scores_box.pack(fill=tk.X, padx=16, pady=(0, 12))
        scores_box.insert(tk.END, str(segment['Scores']))
        scores_box.config(state=tk.DISABLED)

    def play_beep(self, threat_level):
        import winsound
        import time
        print(f"[DEBUG] play_beep called with threat_level: {threat_level}")
        if threat_level == "Safe":
            print("[DEBUG] Playing winsound.Beep for Safe")
            winsound.Beep(1200, 150)
        elif threat_level == "Offensive":
            print("[DEBUG] Playing winsound.Beep for Offensive (double beep)")
            winsound.Beep(800, 300)
            time.sleep(0.2)
            winsound.Beep(800, 300)
        elif threat_level == "Threat":
            print("[DEBUG] Playing winsound.Beep for Threat (double beep)")
            winsound.Beep(400, 500)
            time.sleep(0.2)
            winsound.Beep(400, 500)
        else:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

    def browse_audio_file(self):
        from tkinter import filedialog
        filetypes = [
            ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg"),
            ("All files", "*.*")
        ]
        file_path = filedialog.askopenfilename(title="Select Audio File", filetypes=filetypes)
        if file_path:
            self.audio_file_var.set(file_path)
            # Enable the analyze, transcript, and play buttons
            self.analyze_btn.config(state="normal")
            self.transcript_btn.config(state="normal")
            self.play_btn.config(state="normal")

    def on_back(self):
        """Handle Back navigation.

        If the voice analyzer was embedded into the main app frame, call the
        app's `show_main_menu()` method to navigate back in-place. If the GUI
        was opened as a standalone window, destroy the window.
        """
        print("Back button clicked.")
        try:
            # 1) If the widget root itself provides navigation, use it
            if hasattr(self.root, 'show_main_menu'):
                try:
                    self.root.show_main_menu()
                    return
                except Exception as e:
                    print(f"Error calling root.show_main_menu(): {e}")

            # 2) Check direct master (parent) for navigation
            parent = getattr(self.root, 'master', None)
            if parent is not None and hasattr(parent, 'show_main_menu'):
                try:
                    parent.show_main_menu()
                    return
                except Exception as e:
                    print(f"Error calling parent.show_main_menu(): {e}")

            # 3) Check toplevel window (could be the Tk app instance)
            toplevel = self.root.winfo_toplevel()
            if toplevel is not None:
                if hasattr(toplevel, 'show_main_menu'):
                    try:
                        toplevel.show_main_menu()
                        return
                    except Exception as e:
                        print(f"Error calling toplevel.show_main_menu(): {e}")
                # If no host navigation method exists, close just the toplevel window
                if hasattr(toplevel, 'destroy') and toplevel is not self.root:
                    try:
                        toplevel.destroy()
                        return
                    except Exception as e:
                        print(f"Error destroying toplevel: {e}")

            # 4) Last resort: destroy the provided root if it's a Toplevel or Frame
            if hasattr(self.root, 'destroy'):
                try:
                    self.root.destroy()
                except Exception as e:
                    print(f"Error destroying root: {e}")
        except Exception as e:
            print(f"on_back unexpected error: {e}")

def create_voice_analyzer_gui(root, user_id):
    """Create and return the voice analyzer GUI"""
    return VoiceAnalyzerGUI(root, user_id)


def create_legacy_voice_analyzer_gui(parent):
    """Create a compact legacy-style voice analyzer UI inside `parent`.

    This function is intentionally lightweight so it can be embedded into the
    main application frame. It will call host app methods when available
    (for example, `analyze_voice_file` on the main `CyberWatchApp`).
    """
    import tkinter as tk
    from tkinter import filedialog
    # Clear parent
    for child in parent.winfo_children():
        child.destroy()

    # Title and back
    back_frame = tk.Frame(parent, bg="#ffffff")
    back_frame.pack(fill="x", pady=(10, 0))
    def _back():
        # Prefer host navigation method if present
        host = getattr(parent, 'master', None)
        if host is not None and hasattr(host, 'show_main_menu'):
            try:
                host.show_main_menu()
                return
            except Exception:
                pass
        # fallback
        try:
            parent.winfo_toplevel().destroy()
        except Exception:
            pass

    back_btn = tk.Button(back_frame, text="⬅ Back", command=_back)
    back_btn.pack(side="left", padx=16)

    title = tk.Label(parent, text="Voice Analyzer (Legacy)", font=("Segoe UI", 20, "bold"))
    title.pack(pady=(8, 8))

    # File entry + browse
    file_frame = tk.Frame(parent)
    file_frame.pack(padx=20, pady=10, fill="x")
    file_var = tk.StringVar()
    entry = tk.Entry(file_frame, textvariable=file_var, font=("Segoe UI", 12))
    entry.pack(side="left", fill="x", expand=True)
    def browse():
        fp = filedialog.askopenfilename(title="Select audio file", filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg"), ("All files", "*.*")])
        if fp:
            file_var.set(fp)
    browse_btn = tk.Button(file_frame, text="Browse", command=browse)
    browse_btn.pack(side="left", padx=(8,0))

    # Status and result
    status_label = tk.Label(parent, text="Ready", font=("Segoe UI", 10))
    status_label.pack(pady=(4,4))
    result_label = tk.Label(parent, text="", font=("Segoe UI", 14, "bold"))
    result_label.pack(pady=(4,8))

    # Actions
    btn_frame = tk.Frame(parent)
    btn_frame.pack(pady=8)

    def analyze():
        fp = file_var.get()
        if not fp:
            status_label.config(text="No file selected")
            return
        host = getattr(parent, 'master', None)
        status_label.config(text="Analyzing...")
        # Prefer host's analyze method when available
        if host is not None and hasattr(host, 'analyze_voice_file'):
            try:
                # run in thread to avoid blocking
                import threading
                threading.Thread(target=lambda: host.analyze_voice_file(fp, result_label, status_label), daemon=True).start()
                return
            except Exception:
                pass
        # Fallback: show message
        status_label.config(text="No analyzer available in host")

    def play():
        fp = file_var.get()
        if not fp:
            status_label.config(text="No file selected")
            return
        try:
            try:
                import soundfile as sf
                import sounddevice as sd
            except Exception:
                status_label.config(text="Play requires 'soundfile' and 'sounddevice' packages")
                return
            data, sr = sf.read(fp)
            sd.play(data, sr)
        except Exception as e:
            status_label.config(text=f"Play error: {e}")

    def transcript():
        fp = file_var.get()
        if not fp:
            status_label.config(text="No file selected")
            return
        host = getattr(parent, 'master', None)
        if host is not None and hasattr(host, 'analyze_voice_file'):
            # Host analyze will show popups with transcript; call it
            import threading
            threading.Thread(target=lambda: host.analyze_voice_file(fp, result_label, status_label), daemon=True).start()
            return
        status_label.config(text="No transcription available")

    analyze_btn = tk.Button(btn_frame, text="Analyze", width=12, command=analyze)
    analyze_btn.pack(side="left", padx=6)
    play_btn = tk.Button(btn_frame, text="Play", width=12, command=play)
    play_btn.pack(side="left", padx=6)
    trans_btn = tk.Button(btn_frame, text="Transcript", width=12, command=transcript)
    trans_btn.pack(side="left", padx=6)

    return {
        'parent': parent,
        'file_var': file_var,
        'status_label': status_label,
        'result_label': result_label
    }