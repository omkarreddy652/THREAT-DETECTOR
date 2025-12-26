import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import threading
import time
import os
from PIL import Image, ImageTk
import numpy as np
from typing import Optional, Dict, Any
import json
from datetime import datetime
import platform
if platform.system() == 'Windows':
    import winsound

# Import our facial emotion analyzer
import sys
sys.path.append('..')
from facial_emotion_analyzer import FacialEmotionAnalyzer, EmotionAlert

# Modern color scheme
COLORS = {
    'primary': '#2c3e50',      # Dark blue-gray
    'secondary': '#34495e',    # Lighter blue-gray
    'accent': '#3498db',       # Blue
    'success': '#27ae60',      # Green
    'warning': '#f39c12',      # Orange
    'danger': '#e74c3c',       # Red
    'light': '#ecf0f1',        # Light gray
    'dark': '#2c3e50',         # Dark
    'white': '#ffffff',        # White
    'text': '#2c3e50',         # Text color
    'text_light': '#7f8c8d'    # Light text
}

# Custom styles
def setup_styles():
    """Setup modern ttk styles"""
    style = ttk.Style()
    
    # Configure modern theme
    style.theme_use('clam')
    
    # Configure colors
    style.configure('Title.TLabel', 
                   font=('Segoe UI', 18, 'bold'), 
                   foreground=COLORS['primary'],
                   background=COLORS['white'])
    
    style.configure('Subtitle.TLabel', 
                   font=('Segoe UI', 12), 
                   foreground=COLORS['text_light'],
                   background=COLORS['white'])
    
    style.configure('Status.TLabel', 
                   font=('Segoe UI', 10), 
                   foreground=COLORS['text_light'],
                   background=COLORS['light'])
    
    style.configure('Modern.TButton', 
                   font=('Segoe UI', 10, 'bold'),
                   padding=(15, 8))
    
    style.configure('Success.TButton', 
                   font=('Segoe UI', 10, 'bold'),
                   padding=(15, 8))
    
    style.configure('Warning.TButton', 
                   font=('Segoe UI', 10, 'bold'),
                   padding=(15, 8))
    
    style.configure('Danger.TButton', 
                   font=('Segoe UI', 10, 'bold'),
                   padding=(15, 8))
    
    style.configure('Modern.TFrame', 
                   background=COLORS['white'])
    
    style.configure('Card.TFrame', 
                   background=COLORS['light'],
                   relief='flat',
                   borderwidth=1)
    
    style.configure('Modern.TNotebook', 
                   background=COLORS['white'])
    
    style.configure('Modern.TNotebook.Tab', 
                   font=('Segoe UI', 10, 'bold'),
                   padding=(20, 10))

class FacialEmotionGUI:
    """GUI for facial emotion detection system"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Facial Emotion Detection System")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Configure window
        self.root.configure(bg=COLORS['white'])
        
        # Setup modern styles
        setup_styles()
        
        # Initialize components
        self.analyzer = FacialEmotionAnalyzer()
        self.alert_system = EmotionAlert()
        
        # GUI state
        self.is_webcam_active = False
        self.is_analyzing_video = False
        self.webcam_thread = None
        self.video_thread = None
        self.cap = None
        
        # Analysis results
        self.current_results = []
        self.video_results = None
        
        # Create GUI
        self.create_widgets()
        self.setup_layout()
        
        # Start model initialization
        self.analyzer.start_initialization()
        
        # Update initialization status
        self.root.after(100, self.check_initialization)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Header
        self.create_header()
        
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.root, style='Modern.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create Face Analyzer tab (single tab for all modes)
        self.face_analyzer_tab = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(self.face_analyzer_tab, text="🧑‍🦰 Face Analyzer")

        # Mode selection frame (shown by default)
        self.mode_select_frame = ttk.Frame(self.face_analyzer_tab, style='Modern.TFrame')
        self.mode_select_frame.pack(fill=tk.BOTH, expand=True)
        self.create_mode_selection()

        # Create the three analysis panels (hidden by default)
        self.webcam_panel = ttk.Frame(self.face_analyzer_tab, style='Modern.TFrame')
        self.video_panel = ttk.Frame(self.face_analyzer_tab, style='Modern.TFrame')
        self.snapshot_panel = ttk.Frame(self.face_analyzer_tab, style='Modern.TFrame')
        self.create_webcam_panel()
        self.create_video_panel()
        self.create_snapshot_panel()
        self.webcam_panel.pack_forget()
        self.video_panel.pack_forget()
        self.snapshot_panel.pack_forget()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Initializing models...")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, style='Status.TLabel', relief=tk.FLAT)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def create_header(self):
        """Create modern header"""
        header_frame = ttk.Frame(self.root, style='Modern.TFrame')
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        # Title
        title_label = ttk.Label(header_frame, text="Facial Emotion Detection", 
                               style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, 
                                  text="Advanced AI-powered emotion recognition system", 
                                  style='Subtitle.TLabel')
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0), pady=(5, 0))
        
        # Model status indicator
        self.model_status_frame = ttk.Frame(header_frame, style='Card.TFrame')
        self.model_status_frame.pack(side=tk.RIGHT, padx=(0, 20))
        
        self.model_status_label = ttk.Label(self.model_status_frame, 
                                           text="🔄 Initializing", 
                                           style='Status.TLabel')
        self.model_status_label.pack(padx=10, pady=5)
    
    def create_mode_selection(self):
        """Create the mode selection menu with three large buttons"""
        label = ttk.Label(self.mode_select_frame, text="Select Face Analysis Mode", style='Title.TLabel')
        label.pack(pady=(60, 30))
        btn_style = 'Modern.TButton'
        webcam_btn = ttk.Button(self.mode_select_frame, text="🎥 Live Webcam Monitoring", style=btn_style, command=self.show_webcam_panel)
        webcam_btn.pack(pady=20, ipadx=30, ipady=10)
        video_btn = ttk.Button(self.mode_select_frame, text="🎬 Video File Analyzer", style=btn_style, command=self.show_video_panel)
        video_btn.pack(pady=20, ipadx=30, ipady=10)
        snapshot_btn = ttk.Button(self.mode_select_frame, text="🖼️ Snapshot (Image) Analyzer", style=btn_style, command=self.show_snapshot_panel)
        snapshot_btn.pack(pady=20, ipadx=30, ipady=10)

    def show_mode_selection(self):
        self.webcam_panel.pack_forget()
        self.video_panel.pack_forget()
        self.snapshot_panel.pack_forget()
        self.mode_select_frame.pack(fill=tk.BOTH, expand=True)

    def show_webcam_panel(self):
        self.mode_select_frame.pack_forget()
        self.video_panel.pack_forget()
        self.snapshot_panel.pack_forget()
        self.webcam_panel.pack(fill=tk.BOTH, expand=True)

    def show_video_panel(self):
        self.mode_select_frame.pack_forget()
        self.webcam_panel.pack_forget()
        self.snapshot_panel.pack_forget()
        self.video_panel.pack(fill=tk.BOTH, expand=True)

    def show_snapshot_panel(self):
        self.mode_select_frame.pack_forget()
        self.webcam_panel.pack_forget()
        self.video_panel.pack_forget()
        self.snapshot_panel.pack(fill=tk.BOTH, expand=True)

    def create_webcam_panel(self):
        # Back button
        back_btn = ttk.Button(self.webcam_panel, text="⬅ Back", style='Modern.TButton', command=self.show_mode_selection)
        back_btn.pack(anchor=tk.NW, padx=20, pady=20)

        # Video display area
        self.webcam_video_label = ttk.Label(self.webcam_panel, text="Webcam feed will appear here", background=COLORS['light'], anchor="center")
        self.webcam_video_label.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Controls
        controls_frame = ttk.Frame(self.webcam_panel)
        controls_frame.pack(pady=10)
        self.start_webcam_btn = ttk.Button(controls_frame, text="Start Webcam", style='Modern.TButton', command=self.start_webcam)
        self.start_webcam_btn.pack(side=tk.LEFT, padx=10)
        self.stop_webcam_btn = ttk.Button(controls_frame, text="Stop Webcam", style='Modern.TButton', command=self.stop_webcam, state=tk.DISABLED)
        self.stop_webcam_btn.pack(side=tk.LEFT, padx=10)
        self.capture_btn = ttk.Button(controls_frame, text="Capture & Analyze", style='Modern.TButton', command=self.capture_and_analyze_frame, state=tk.DISABLED)
        self.capture_btn.pack(side=tk.LEFT, padx=10)

        # Results area
        self.webcam_results_text = tk.Text(self.webcam_panel, height=8, font=("Consolas", 11), bg=COLORS['light'], fg=COLORS['text'], relief=tk.FLAT)
        self.webcam_results_text.pack(fill=tk.X, padx=20, pady=10)
        self.webcam_results_text.config(state=tk.DISABLED)

    def create_video_panel(self):
        back_btn = ttk.Button(self.video_panel, text="⬅ Back", style='Modern.TButton', command=self.show_mode_selection)
        back_btn.pack(anchor=tk.NW, padx=20, pady=20)

        # Video file selection
        file_frame = ttk.Frame(self.video_panel)
        file_frame.pack(pady=10)
        self.video_file_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.video_file_var, width=60)
        file_entry.pack(side=tk.LEFT, padx=5)
        browse_btn = ttk.Button(file_frame, text="Browse Video", style='Modern.TButton', command=self.browse_video_file)
        browse_btn.pack(side=tk.LEFT, padx=5)
        analyze_btn = ttk.Button(file_frame, text="Start Analysis", style='Modern.TButton', command=self.start_video_analysis)
        analyze_btn.pack(side=tk.LEFT, padx=5)

        # Video display area
        self.video_display_label = ttk.Label(self.video_panel, text="Video frame will appear here", background=COLORS['light'], anchor="center")
        self.video_display_label.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Results area
        self.video_results_text = tk.Text(self.video_panel, height=8, font=("Consolas", 11), bg=COLORS['light'], fg=COLORS['text'], relief=tk.FLAT)
        self.video_results_text.pack(fill=tk.X, padx=20, pady=10)
        self.video_results_text.config(state=tk.DISABLED)

    def create_snapshot_panel(self):
        back_btn = ttk.Button(self.snapshot_panel, text="⬅ Back", style='Modern.TButton', command=self.show_mode_selection)
        back_btn.pack(anchor=tk.NW, padx=20, pady=20)

        # Image file selection
        file_frame = ttk.Frame(self.snapshot_panel)
        file_frame.pack(pady=10)
        self.image_file_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.image_file_var, width=60)
        file_entry.pack(side=tk.LEFT, padx=5)
        browse_btn = ttk.Button(file_frame, text="Browse Image", style='Modern.TButton', command=self.browse_image_file)
        browse_btn.pack(side=tk.LEFT, padx=5)
        analyze_btn = ttk.Button(file_frame, text="Analyze Image", style='Modern.TButton', command=self.start_image_analysis)
        analyze_btn.pack(side=tk.LEFT, padx=5)

        # Image display area
        self.image_display_label = ttk.Label(self.snapshot_panel, text="Image will appear here", background=COLORS['light'], anchor="center")
        self.image_display_label.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Results area
        self.image_results_text = tk.Text(self.snapshot_panel, height=8, font=("Consolas", 11), bg=COLORS['light'], fg=COLORS['text'], relief=tk.FLAT)
        self.image_results_text.pack(fill=tk.X, padx=20, pady=10)
        self.image_results_text.config(state=tk.DISABLED)
    
    def setup_layout(self):
        """Setup main layout"""
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def check_initialization(self):
        """Check if models are initialized"""
        if self.analyzer.is_initialized:
            model_type = "Pre-trained" if self.analyzer.use_pre_trained else "Custom CNN"
            self.status_var.set(f"Ready - {model_type} models loaded successfully")
            
            # Update model status indicator
            if self.analyzer.use_pre_trained:
                self.model_status_label.config(text="✅ Pre-trained Models", 
                                              foreground=COLORS['success'])
            else:
                self.model_status_label.config(text="✅ Custom CNN Models", 
                                              foreground=COLORS['warning'])
            
            self.enable_controls()
        else:
            self.status_var.set("Initializing models... Please wait")
            self.model_status_label.config(text="🔄 Initializing", 
                                          foreground=COLORS['text_light'])
            self.root.after(1000, self.check_initialization)
    
    def enable_controls(self):
        """Enable all controls after initialization"""
        # The controls are now managed by the panels, not a single button
        pass
    
    def toggle_webcam(self):
        """Toggle webcam on/off"""
        if not self.is_webcam_active:
            self.start_webcam()
        else:
            self.stop_webcam()
    
    def start_webcam(self):
        if not self.analyzer.is_initialized:
            messagebox.showwarning("Warning", "Models not yet initialized. Please wait.")
            return
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Error", "Could not open webcam")
                return
            self.is_webcam_active = True
            self.start_webcam_btn.config(state=tk.DISABLED)
            self.stop_webcam_btn.config(state=tk.NORMAL)
            self.capture_btn.config(state=tk.NORMAL)
            self.webcam_thread = threading.Thread(target=self.webcam_loop, daemon=True)
            self.webcam_thread.start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start webcam: {e}")
    
    def stop_webcam(self):
        self.is_webcam_active = False
        self.start_webcam_btn.config(state=tk.NORMAL)
        self.stop_webcam_btn.config(state=tk.DISABLED)
        self.capture_btn.config(state=tk.DISABLED)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.webcam_video_label.config(image='', text="Webcam feed will appear here")
    
    def webcam_loop(self):
        while self.is_webcam_active:
            if self.cap is None:
                break
            ret, frame = self.cap.read()
            if not ret:
                break
            results = self.analyzer.analyze_frame(frame)
            self.current_results = results
            annotated_frame = self.draw_results_on_frame(frame, results)
            self.display_webcam_frame(annotated_frame)
            self.update_webcam_results(results)
            time.sleep(0.1)

    def display_webcam_frame(self, frame):
        try:
            height, width = frame.shape[:2]
            max_size = 400
            if width > max_size or height > max_size:
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            self.webcam_video_label.config(image=photo, text='')
            self.webcam_video_label.image = photo
        except Exception as e:
            print(f"Error displaying webcam frame: {e}")

    def capture_and_analyze_frame(self):
        if self.cap is None or not self.is_webcam_active:
            messagebox.showwarning("Warning", "Webcam is not active.")
            return
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture frame.")
            return
        results = self.analyzer.analyze_frame(frame)
        # Here, you would also call your real/fake (liveness) detection if available
        # For now, we'll just display emotion and threat
        self.webcam_results_text.config(state=tk.NORMAL)
        self.webcam_results_text.delete(1.0, tk.END)
        if not results:
            self.webcam_results_text.insert(tk.END, "No faces detected.\n")
        else:
            for i, result in enumerate(results, 1):
                emotion = result.get('emotion', 'Unknown')
                threat = self.map_emotion_to_threat(emotion)
                fake_real = 'Real'  # Placeholder
                self.webcam_results_text.insert(tk.END, f"Face {i}: Emotion: {emotion}, Threat: {threat}, Real/Fake: {fake_real}\n")
                self.play_beep(threat)
                if threat in ['Threat', 'Offensive']:
                    self.show_alert(threat, f"Face {i}: {emotion} detected as {threat}!")
        self.webcam_results_text.config(state=tk.DISABLED)
    
    def draw_results_on_frame(self, frame, results):
        """Draw detection results on frame"""
        annotated_frame = frame.copy()
        
        for result in results:
            x, y, w, h = result['bbox']
            category = result['category']
            emotion = result['emotion']
            confidence = result['confidence']
            emoji = result['emoji']
            
            # Draw bounding box
            color = self.analyzer.colors[category]
            cv2.rectangle(annotated_frame, (x, y), (x+w, y+h), color, 2)
            
            # Draw label
            label = f"{emoji} {emotion} ({confidence:.2f})"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(annotated_frame, (x, y-label_size[1]-10), (x+label_size[0], y), color, -1)
            cv2.putText(annotated_frame, label, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated_frame
    
    def display_frame(self, frame):
        """Display frame in GUI"""
        try:
            # Resize frame for display
            height, width = frame.shape[:2]
            max_size = 400
            if width > max_size or height > max_size:
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            
            # Convert to PIL
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update label
            # The video label is now managed by the panel, not a single button
            # self.video_label.config(image=photo, text="")
            # self.video_label.image = photo  # Keep reference
            
        except Exception as e:
            print(f"Error displaying frame: {e}")
    
    def update_webcam_results(self, results):
        """Update real-time results display"""
        try:
            self.webcam_results_text.config(state=tk.NORMAL)
            self.webcam_results_text.delete(1.0, tk.END)
            
            if not results:
                self.webcam_results_text.insert(tk.END, "No faces detected\n")
                self.webcam_results_text.config(state=tk.DISABLED)
                return
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.webcam_results_text.insert(tk.END, f"Analysis at {timestamp}:\n\n")
            
            for i, result in enumerate(results, 1):
                emotion = result.get('emotion', 'Unknown')
                category = result.get('category', 'Unknown')
                confidence = result.get('confidence', 0)
                emoji = result.get('emoji', '😐')
                
                self.webcam_results_text.insert(tk.END, f"Face {i}:\n")
                self.webcam_results_text.insert(tk.END, f"  Emotion: {emoji} {emotion}\n")
                self.webcam_results_text.insert(tk.END, f"  Category: {category}\n")
                self.webcam_results_text.insert(tk.END, f"  Confidence: {confidence:.2f}\n\n")
                
                # Play audio alert and threat assessment
                threat_level = self.map_emotion_to_threat(emotion)
                self.play_beep(threat_level)
                if threat_level in ['Threat', 'Offensive']:
                    self.show_alert(threat_level, f"Face {i}: {emotion} detected as {threat_level}!")
            
            self.webcam_results_text.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"Error updating results: {e}")
    
    def browse_video(self):
        """Browse for video file"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.video_path_var.set(file_path)
    
    def browse_video_file(self):
        """Browse for video file (alias for video panel)"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.video_file_var.set(file_path)
    
    def browse_image(self):
        """Browse for image file"""
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.image_path_var.set(file_path)
            self.display_image(file_path)
    
    def browse_image_file(self):
        """Browse for image file (alias for snapshot panel)"""
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.image_file_var.set(file_path)
            self.display_image(file_path)
    
    def display_image(self, image_path):
        """Display selected image"""
        try:
            # Load and resize image
            image = Image.open(image_path)
            image.thumbnail((400, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # The image_label is now managed by the panel, not a single button
            # self.image_label.config(image=photo, text="")
            # self.image_label.image = photo
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image: {e}")
    
    def start_video_analysis(self):
        """Start video file analysis"""
        video_path = self.video_file_var.get()
        if not video_path:
            messagebox.showwarning("Warning", "Please select a video file first.")
            return
        if not os.path.exists(video_path):
            messagebox.showerror("Error", "Video file not found.")
            return
        try:
            self.analyze_video_file(video_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze video: {e}")
    
    def start_image_analysis(self):
        """Start image file analysis"""
        image_path = self.image_file_var.get()
        if not image_path:
            messagebox.showwarning("Warning", "Please select an image file first.")
            return
        if not os.path.exists(image_path):
            messagebox.showerror("Error", "Image file not found.")
            return
        try:
            results = self.analyzer.analyze_frame(cv2.imread(image_path))
            self.image_results_text.config(state=tk.NORMAL)
            self.image_results_text.delete(1.0, tk.END)
            if not results:
                self.image_results_text.insert(tk.END, "No faces detected.\n")
            else:
                for i, result in enumerate(results, 1):
                    emotion = result.get('emotion', 'Unknown')
                    threat = self.map_emotion_to_threat(emotion)
                    fake_real = 'Real'  # Placeholder
                    self.image_results_text.insert(tk.END, f"Face {i}: Emotion: {emotion}, Threat: {threat}, Real/Fake: {fake_real}\n")
                    self.play_beep(threat)
                    if threat in ['Threat', 'Offensive']:
                        self.show_alert(threat, f"Face {i}: {emotion} detected as {threat}!")
            self.image_results_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze image: {e}")
    
    def analyze_video_file(self, video_path):
        """Analyze video file"""
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        processed = 0
        self.video_results_text.config(state=tk.NORMAL)
        self.video_results_text.delete(1.0, tk.END)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            results = self.analyzer.analyze_frame(frame)
            annotated_frame = self.draw_results_on_frame(frame, results)
            self.display_video_frame(annotated_frame)
            # Show results for this frame
            self.video_results_text.insert(tk.END, f"Frame {processed+1}/{frame_count}:\n")
            if not results:
                self.video_results_text.insert(tk.END, "  No faces detected.\n")
            else:
                for i, result in enumerate(results, 1):
                    emotion = result.get('emotion', 'Unknown')
                    threat = self.map_emotion_to_threat(emotion)
                    fake_real = 'Real'  # Placeholder
                    self.video_results_text.insert(tk.END, f"  Face {i}: Emotion: {emotion}, Threat: {threat}, Real/Fake: {fake_real}\n")
                    self.play_beep(threat)
                    if threat in ['Threat', 'Offensive']:
                        self.show_alert(threat, f"Frame {processed+1}, Face {i}: {emotion} detected as {threat}!")
            self.video_results_text.insert(tk.END, "\n")
            self.video_results_text.see(tk.END)
            processed += 1
            # Slow down for UI update
            self.video_panel.update_idletasks()
            time.sleep(0.05)
        cap.release()
        self.video_results_text.insert(tk.END, "Analysis complete.\n")
        self.video_results_text.config(state=tk.DISABLED)
    
    def _analyze_video_worker(self, video_path):
        """Worker thread for video analysis"""
        try:
            frame_interval = self.frame_interval_var.get()
            results = self.analyzer.analyze_video_file(video_path, frame_interval)
            
            # Update GUI in main thread
            self.root.after(0, lambda: self._video_analysis_complete(results))
            
        except Exception as e:
            self.root.after(0, lambda: self._video_analysis_error(str(e)))
    
    def _video_analysis_complete(self, results):
        """Handle video analysis completion"""
        self.is_analyzing_video = False
        self.analyze_video_btn.config(state='normal')
        self.video_progress.stop()
        
        if results:
            self.video_results = results
            self.display_video_results(results)
            self.add_to_history("Video Analysis", results['summary']['threat_level'], results)
        else:
            messagebox.showerror("Error", "Video analysis failed")
    
    def _video_analysis_error(self, error_msg):
        """Handle video analysis error"""
        self.is_analyzing_video = False
        self.analyze_video_btn.config(state='normal')
        self.video_progress.stop()
        messagebox.showerror("Error", f"Video analysis failed: {error_msg}")
    
    def display_video_results(self, results):
        """Display video analysis results"""
        # Update summary
        self.video_summary_text.delete(1.0, tk.END)
        summary = results['summary']
        
        summary_text = f"Video Analysis Summary\n"
        summary_text += f"=" * 50 + "\n\n"
        summary_text += f"File: {results['video_path']}\n"
        summary_text += f"Duration: {results['duration']:.2f} seconds\n"
        summary_text += f"Total Frames: {results['total_frames']}\n"
        summary_text += f"Analyzed Frames: {results['analyzed_frames']}\n"
        summary_text += f"FPS: {results['fps']:.2f}\n\n"
        summary_text += f"Threat Level: {summary['threat_level']}\n"
        summary_text += f"Total Detections: {summary['total_detections']}\n"
        summary_text += f"Most Common Emotion: {summary['most_common_emotion']}\n"
        summary_text += f"Most Common Category: {summary['most_common_category']}\n\n"
        
        summary_text += "Emotion Distribution:\n"
        for emotion, count in summary['emotion_distribution'].items():
            summary_text += f"  {emotion}: {count}\n"
        
        summary_text += "\nCategory Distribution:\n"
        for category, count in summary['category_distribution'].items():
            summary_text += f"  {category}: {count}\n"
        
        self.video_summary_text.insert(tk.END, summary_text)
        
        # Update details
        self.video_details_text.delete(1.0, tk.END)
        details_text = "Frame-by-Frame Analysis\n"
        details_text += "=" * 50 + "\n\n"
        
        for frame_data in results['frame_analysis'][:50]:  # Show first 50 frames
            details_text += f"Frame {frame_data['frame']} (Time: {frame_data['time']:.2f}s):\n"
            if frame_data['emotions']:
                for emotion_data in frame_data['emotions']:
                    details_text += f"  {emotion_data['emoji']} {emotion_data['emotion']} ({emotion_data['confidence']:.2f})\n"
            else:
                details_text += "  No faces detected\n"
            details_text += "\n"
        
        if len(results['frame_analysis']) > 50:
            details_text += f"... and {len(results['frame_analysis']) - 50} more frames\n"
        
        self.video_details_text.insert(tk.END, details_text)

        for frame_result in results:
            for face in frame_result.get('faces', []):
                emotion = face.get('emotion', 'Unknown')
                threat_level = self.map_emotion_to_threat(emotion)
                face['threat_level'] = threat_level
                self.play_threat_alert(threat_level)
    
    def analyze_image_file(self):
        """Analyze image file"""
        image_path = self.image_path_var.get()
        if not image_path:
            messagebox.showwarning("Warning", "Please select an image file")
            return
        
        if not os.path.exists(image_path):
            messagebox.showerror("Error", "Image file not found")
            return
        
        try:
            results = self.analyzer.analyze_image(image_path)
            if results:
                self.display_image_results(results)
                self.add_to_history("Image Analysis", results['summary']['threat_level'], results)
            else:
                messagebox.showerror("Error", "Image analysis failed")
                
        except Exception as e:
            messagebox.showerror("Error", f"Image analysis failed: {e}")
    
    def display_image_results(self, results):
        """Display image analysis results"""
        self.snapshot_results_text.delete(1.0, tk.END)
        
        summary = results['summary']
        results_text = f"Image Analysis Results\n"
        results_text += f"=" * 50 + "\n\n"
        results_text += f"File: {results['image_path']}\n"
        results_text += f"Total Faces: {summary['total_faces']}\n"
        results_text += f"Threat Level: {summary['threat_level']}\n"
        results_text += f"Primary Emotion: {summary['primary_emotion']}\n\n"
        
        if results['detections']:
            results_text += "Detected Emotions:\n"
            for i, detection in enumerate(results['detections'], 1):
                results_text += f"\nFace {i}:\n"
                results_text += f"  {detection['emoji']} {detection['emotion']}\n"
                results_text += f"  Category: {detection['category']}\n"
                results_text += f"  Confidence: {detection['confidence']:.2f}\n"
        else:
            results_text += "No faces detected in the image.\n"
        
        self.snapshot_results_text.insert(tk.END, results_text)

        for face in results:
            emotion = face.get('emotion', 'Unknown')
            threat_level = self.map_emotion_to_threat(emotion)
            face['threat_level'] = threat_level
            self.play_threat_alert(threat_level)
    
    def add_to_history(self, analysis_type, threat_level, results):
        """Add analysis result to history"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if analysis_type == "Video Analysis":
            emotions = list(results['summary']['emotion_distribution'].keys())
            details = f"{results['summary']['total_detections']} detections"
        elif analysis_type == "Image Analysis":
            emotions = results['summary']['emotions_found']
            details = f"{results['summary']['total_faces']} faces"
        else:
            emotions = []
            details = "N/A"
        
        emotions_str = ", ".join(emotions[:3]) + ("..." if len(emotions) > 3 else "")
        
        self.results_tree.insert('', 'end', values=(
            timestamp,
            analysis_type,
            threat_level,
            emotions_str,
            details
        ))
    
    def on_result_select(self, event):
        """Handle result selection"""
        selection = self.results_tree.selection()
        if selection:
            # Could implement detailed view here
            pass
    
    def save_results(self):
        """Save analysis results"""
        if not self.video_results:
            messagebox.showwarning("Warning", "No results to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.video_results, f, indent=2, default=str)
                messagebox.showinfo("Success", "Results saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save results: {e}")
    
    def load_results(self):
        """Load analysis results"""
        file_path = filedialog.askopenfilename(
            title="Load Results",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    results = json.load(f)
                self.video_results = results
                self.display_video_results(results)
                messagebox.showinfo("Success", "Results loaded successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load results: {e}")
    
    def clear_results(self):
        """Clear all results"""
        if messagebox.askyesno("Confirm", "Clear all results?"):
            self.video_results = None
            self.video_summary_text.delete(1.0, tk.END)
            self.video_details_text.delete(1.0, tk.END)
            self.snapshot_results_text.delete(1.0, tk.END)
            # The webcam_results_text is now managed by the panel, not a single button
            # self.webcam_results_text.delete(1.0, tk.END)
            
            # Clear treeview
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
    
    def export_report(self):
        """Export analysis report"""
        if not self.video_results:
            messagebox.showwarning("Warning", "No results to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write("Facial Emotion Analysis Report\n")
                    f.write("=" * 50 + "\n\n")
                    
                    results = self.video_results
                    summary = results['summary']
                    
                    f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Video File: {results['video_path']}\n")
                    f.write(f"Duration: {results['duration']:.2f} seconds\n")
                    f.write(f"Threat Level: {summary['threat_level']}\n\n")
                    
                    f.write("Summary Statistics:\n")
                    f.write(f"  Total Detections: {summary['total_detections']}\n")
                    f.write(f"  Most Common Emotion: {summary['most_common_emotion']}\n")
                    f.write(f"  Most Common Category: {summary['most_common_category']}\n\n")
                    
                    f.write("Emotion Distribution:\n")
                    for emotion, count in summary['emotion_distribution'].items():
                        f.write(f"  {emotion}: {count}\n")
                
                messagebox.showinfo("Success", "Report exported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export report: {e}")
    
    def on_closing(self):
        """Handle window closing"""
        self.stop_webcam()
        self.root.destroy()

    def map_emotion_to_threat(self, emotion):
        # Map emotion to threat level
        if emotion.lower() in ["angry", "fear", "disgust"]:
            return "Threat"
        elif emotion.lower() in ["sad", "surprise"]:
            return "Offensive"
        else:
            return "Safe"

    def play_threat_alert(self, threat_level):
        # Play a sound or show a popup for Threat/Offensive
        if threat_level == "Threat":
            self.status_var.set("⚠️ Threat detected!")
            self.root.bell()  # Simple beep
        elif threat_level == "Offensive":
            self.status_var.set("⚠️ Offensive detected!")
            self.root.bell()
        else:
            self.status_var.set("✔️ Safe detected.")

    def play_beep(self, threat_level):
        # Play a single beep for Safe, double beep for Threat/Offensive
        if platform.system() == 'Windows':
            if threat_level == 'Safe':
                winsound.Beep(800, 200)
            elif threat_level in ['Threat', 'Offensive']:
                winsound.Beep(400, 200)
                winsound.Beep(400, 200)
        else:
            # Cross-platform fallback: use bell
            if threat_level == 'Safe':
                self.root.bell()
            elif threat_level in ['Threat', 'Offensive']:
                self.root.bell()
                self.root.after(200, self.root.bell)

    def show_alert(self, threat_level, message):
        if threat_level in ['Threat', 'Offensive']:
            messagebox.showwarning(f"{threat_level} Alert", message)

def main():
    """Main function to run the facial emotion GUI"""
    root = tk.Tk()
    app = FacialEmotionGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main() 