"""
Facial Emotion Analyzer using DeepFace
Pure DeepFace implementation for both face detection and emotion recognition
"""

import cv2
import numpy as np
import os
import threading
import time
# pygame is optional for sound playback
try:
    import pygame
    _HAS_PYGAME = True
except Exception:
    pygame = None
    _HAS_PYGAME = False
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path

# DeepFace for emotion recognition and face detection
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
    print("✅ DeepFace available - using for emotion recognition and face detection")
except ImportError as e:
    DEEPFACE_AVAILABLE = False
    print(f"❌ DeepFace import error: {e}")

# Optional: YOLO for faster face detection
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    print("✅ YOLO available - using for fast face detection")
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️  YOLO not available - using DeepFace only")


class FacialEmotionAnalyzer:
    """Comprehensive facial emotion detection system using DeepFace"""
    
    def __init__(self):
        self.face_cascade = None
        self.yolo_model = None
        
        # Emotion mapping
        self.emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        
        # Category mapping
        self.emotion_categories = {
            'Safe': ['Happy', 'Neutral'],
            'Offensive': ['Disgust', 'Angry'],
            'Threat': ['Fear', 'Sad', 'Surprise']
        }
        
        # Colors for visualization
        self.colors = {
            'Safe': (0, 255, 0),        # Green
            'Offensive': (0, 165, 255),  # Orange
            'Threat': (0, 0, 255)        # Red
        }
        
        # Emojis for emotions
        self.emojis = {
            'Happy': '😊', 
            'Neutral': '😐', 
            'Disgust': '🤢', 
            'Angry': '😠', 
            'Fear': '😨', 
            'Sad': '😢', 
            'Surprise': '😲'
        }
        
        self.is_initialized = False
        self.initialization_thread = None
        self.detection_method = "auto"  # auto, yolo, deepface, haar
        
    def initialize_models(self):
        """Initialize models in background thread"""
        try:
            print("🔄 Initializing DeepFace Emotion Analyzer...")
            
            # Load Haar Cascade as fallback
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            print("✅ Haar Cascade loaded (fallback)")
            
            # Initialize YOLO if available
            if YOLO_AVAILABLE:
                try:
                    print("🔄 Loading YOLO model for face detection...")
                    # Try to download model - this will download on first run
                    self.yolo_model = YOLO('yolov8n-face.pt')
                    print("✅ YOLO face detection model loaded")
                    self.detection_method = "yolo"
                except Exception as e:
                    print(f"⚠️ YOLO initialization failed: {e}")
                    self.detection_method = "deepface"
            else:
                self.detection_method = "deepface"
            
            self.is_initialized = True
            print("✅ Facial emotion analyzer initialized successfully")
            print(f"   Detection method: {self.detection_method}")
            print(f"   Emotion recognition: DeepFace")
            
        except Exception as e:
            print(f"❌ Error initializing analyzer: {e}")
            self.is_initialized = False
    
    def start_initialization(self):
        """Start model initialization in background thread"""
        if not self.is_initialized and self.initialization_thread is None:
            self.initialization_thread = threading.Thread(target=self.initialize_models, daemon=True)
            self.initialization_thread.start()
    
    def detect_faces_yolo(self, frame) -> List[Tuple[int, int, int, int]]:
        """Detect faces using YOLO"""
        if self.yolo_model is None or not YOLO_AVAILABLE:
            return []
        
        try:
            results = self.yolo_model(frame, verbose=False)
            
            faces = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    w = x2 - x1
                    h = y2 - y1
                    faces.append((x1, y1, w, h))
            
            return faces
        except Exception as e:
            print(f"⚠️ YOLO detection error: {e}")
            return []
    
    def detect_faces_deepface(self, frame) -> List[Tuple[int, int, int, int]]:
        """Detect faces using DeepFace"""
        if not DEEPFACE_AVAILABLE:
            return []
        
        try:
            # Use DeepFace for face detection
            faces_info = DeepFace.extract_faces(
                img_path=frame,
                detector_backend='opencv',
                enforce_detection=False
            )
            
            detected = []
            for face_info in faces_info:
                facial_area = face_info.get('facial_area', {})
                x = facial_area.get('x', 0)
                y = facial_area.get('y', 0)
                w = facial_area.get('w', 0)
                h = facial_area.get('h', 0)
                if w > 0 and h > 0:
                    detected.append((x, y, w, h))
            
            return detected
        except Exception as e:
            # DeepFace may throw exceptions - that's ok
            return []
    
    def detect_faces_haar(self, frame) -> List[Tuple[int, int, int, int]]:
        """Detect faces using Haar Cascade with aggressive parameters"""
        if self.face_cascade is None:
            return []
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Image preprocessing
            gray_equalized = cv2.equalizeHist(gray)
            gray_blurred = cv2.GaussianBlur(gray_equalized, (5, 5), 0)
            
            # Try detection on multiple versions
            for detection_image in [gray, gray_equalized, gray_blurred]:
                # Ultra-aggressive: Very sensitive
                faces = self.face_cascade.detectMultiScale(
                    detection_image, 
                    scaleFactor=1.02,
                    minNeighbors=2,
                    minSize=(15, 15),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                if len(faces) > 0:
                    return list(faces)
                
                # Highly sensitive
                faces = self.face_cascade.detectMultiScale(
                    detection_image, 
                    scaleFactor=1.05,
                    minNeighbors=3,
                    minSize=(20, 20),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                if len(faces) > 0:
                    return list(faces)
                
                # Balanced
                faces = self.face_cascade.detectMultiScale(
                    detection_image, 
                    scaleFactor=1.1,
                    minNeighbors=4,
                    minSize=(25, 25),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                if len(faces) > 0:
                    return list(faces)
                
                # Standard
                faces = self.face_cascade.detectMultiScale(
                    detection_image, 
                    scaleFactor=1.15,
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                if len(faces) > 0:
                    return list(faces)
            
            return []
        except Exception as e:
            print(f"⚠️ Haar Cascade detection error: {e}")
            return []
    
    def detect_faces(self, frame):
        """
        Detect faces using priority order:
        1. YOLO (fastest, best accuracy)
        2. DeepFace (good accuracy)
        3. Haar Cascade (fallback)
        """
        faces = []
        
        # Try YOLO first
        if self.yolo_model is not None and YOLO_AVAILABLE:
            try:
                faces = self.detect_faces_yolo(frame)
                if len(faces) > 0:
                    return faces
            except:
                pass
        
        # Try DeepFace
        if DEEPFACE_AVAILABLE:
            try:
                faces = self.detect_faces_deepface(frame)
                if len(faces) > 0:
                    return faces
            except:
                pass
        
        # Fallback to Haar Cascade
        faces = self.detect_faces_haar(frame)
        return faces
    
    def analyze_emotions_deepface(self, frame, faces: List[Tuple[int, int, int, int]]) -> List[Dict]:
        """Analyze emotions for detected faces using DeepFace"""
        if not DEEPFACE_AVAILABLE:
            return []
        
        results = []
        
        try:
            # Analyze emotions using DeepFace
            analysis = DeepFace.analyze(
                img_path=frame,
                actions=['emotion'],
                enforce_detection=False,
                silent=True
            )
            
            # Process results
            if isinstance(analysis, list):
                for face_analysis in analysis:
                    emotions = face_analysis.get('emotion', {})
                    
                    # Get dominant emotion
                    if emotions:
                        dominant_emotion = max(emotions, key=emotions.get)
                        confidence = emotions[dominant_emotion] / 100.0  # Convert to 0-1 range
                        
                        # Categorize emotion
                        category = self.categorize_emotion(dominant_emotion)
                        
                        if confidence > 0.2:  # Confidence threshold
                            results.append({
                                'emotion': dominant_emotion,
                                'category': category,
                                'confidence': confidence,
                                'emoji': self.emojis.get(dominant_emotion, '😐'),
                                'all_emotions': emotions
                            })
        except Exception as e:
            print(f"⚠️ DeepFace emotion analysis error: {e}")
        
        return results
    
    def analyze_frame(self, frame):
        """Analyze single frame for facial emotions"""
        results = []
        
        if not self.is_initialized:
            return results
        
        try:
            # Detect faces
            faces = self.detect_faces(frame)
            
            if len(faces) == 0:
                return results
            # Add bounding boxes to detection results
            deepface_results = self.analyze_emotions_deepface(frame, faces)

            # If DeepFace returned results, combine with face bounding boxes
            if deepface_results and len(deepface_results) > 0:
                for i, detection in enumerate(deepface_results):
                    if i < len(faces):
                        x, y, w, h = faces[i]
                        detection['bbox'] = (x, y, w, h)
                        results.append(detection)
                return results

            # Fallback: if no DeepFace results (e.g., DeepFace not installed) but faces were detected,
            # return neutral placeholder detections so the UI can still visualize bounding boxes.
            for (x, y, w, h) in faces:
                results.append({
                    'emotion': 'Neutral',
                    'category': 'Safe',
                    'confidence': 0.5,
                    'emoji': self.emojis.get('Neutral', '😐'),
                    'bbox': (x, y, w, h)
                })

            return results
            
        except Exception as e:
            print(f"Error analyzing frame: {e}")
            return results
    
    def categorize_emotion(self, emotion):
        """Categorize emotion into Safe/Offensive/Threat"""
        for category, emotions in self.emotion_categories.items():
            if emotion in emotions:
                return category
        return 'Safe'
    
    def analyze_image(self, image_path):
        """Analyze single image for facial emotions"""
        if not os.path.exists(image_path):
            return None
        
        try:
            frame = cv2.imread(image_path)
            if frame is None:
                return None
            
            results = self.analyze_frame(frame)
            
            return {
                'image_path': image_path,
                'detections': results,
                'summary': self.generate_image_summary(results)
            }
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return None
    
    def generate_image_summary(self, detections):
        """Generate summary for single image analysis"""
        if not detections:
            return {
                'total_faces': 0,
                'emotions_found': [],
                'threat_level': 'Low',
                'primary_emotion': 'None'
            }
        
        emotions = [d['emotion'] for d in detections]
        categories = [d['category'] for d in detections]
        
        # Count categories
        category_counts = {}
        for category in categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Determine threat level
        threat_count = category_counts.get('Threat', 0)
        offensive_count = category_counts.get('Offensive', 0)
        total_faces = len(detections)
        
        threat_ratio = (threat_count + offensive_count) / total_faces if total_faces > 0 else 0
        
        if threat_ratio > 0.5:
            threat_level = 'High'
        elif threat_ratio > 0.2:
            threat_level = 'Medium'
        else:
            threat_level = 'Low'
        
        return {
            'total_faces': total_faces,
            'emotions_found': emotions,
            'threat_level': threat_level,
            'primary_emotion': max(set(emotions), key=emotions.count) if emotions else 'None',
            'category_distribution': category_counts
        }
    
    def analyze_video_file(self, video_path, frame_interval=30):
        """Analyze video file frame by frame"""
        if not os.path.exists(video_path):
            return None
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        results = {
            'video_path': video_path,
            'total_frames': total_frames,
            'fps': fps,
            'duration': duration,
            'frame_analysis': [],
            'summary': {}
        }
        
        frame_count = 0
        analyzed_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Analyze every N frames
            if frame_count % frame_interval == 0:
                frame_results = self.analyze_frame(frame)
                results['frame_analysis'].append({
                    'frame': frame_count,
                    'time': frame_count / fps if fps > 0 else 0,
                    'emotions': frame_results
                })
                analyzed_frames += 1
            
            frame_count += 1
        
        cap.release()
        
        # Generate summary
        results['summary'] = self.generate_video_summary(results['frame_analysis'])
        results['analyzed_frames'] = analyzed_frames
        
        return results
    
    def generate_video_summary(self, frame_analysis):
        """Generate summary statistics from video analysis"""
        all_emotions = []
        all_categories = []
        
        for frame_data in frame_analysis:
            for emotion_data in frame_data['emotions']:
                all_emotions.append(emotion_data['emotion'])
                all_categories.append(emotion_data['category'])
        
        if not all_emotions:
            return {
                'total_detections': 0,
                'most_common_emotion': 'None',
                'most_common_category': 'Safe',
                'emotion_distribution': {},
                'category_distribution': {},
                'threat_level': 'Low'
            }
        
        # Count emotions and categories
        emotion_counts = {}
        category_counts = {}
        
        for emotion in all_emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        for category in all_categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Determine threat level
        threat_count = category_counts.get('Threat', 0)
        offensive_count = category_counts.get('Offensive', 0)
        total_detections = len(all_emotions)
        
        threat_ratio = (threat_count + offensive_count) / total_detections if total_detections > 0 else 0
        
        if threat_ratio > 0.5:
            threat_level = 'High'
        elif threat_ratio > 0.2:
            threat_level = 'Medium'
        else:
            threat_level = 'Low'
        
        return {
            'total_detections': total_detections,
            'most_common_emotion': max(emotion_counts, key=emotion_counts.get) if emotion_counts else 'None',
            'most_common_category': max(category_counts, key=category_counts.get) if category_counts else 'Safe',
            'emotion_distribution': emotion_counts,
            'category_distribution': category_counts,
            'threat_level': threat_level
        }


class EmotionAlert:
    """Handles alerts and notifications for emotion detection"""
    
    def __init__(self):
        self.alert_sounds = {
            'Threat': 'sounds/threat_alert.wav',
            'Offensive': 'sounds/warning_alert.wav',
            'Safe': 'sounds/safe_alert.wav'
        }
        self.initialize_sounds()
    
    def initialize_sounds(self):
        """Initialize pygame for sound playback"""
        try:
            pygame.mixer.init()
        except:
            pass
    
    def play_alert(self, category):
        """Play alert sound for emotion category"""
        try:
            sound_file = self.alert_sounds.get(category)
            if sound_file and os.path.exists(sound_file):
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
        except:
            pass
    
    def create_alert_popup(self, emotion_data):
        """Create alert popup for detected emotions"""
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            category = emotion_data['category']
            emotion = emotion_data['emotion']
            emoji = emotion_data['emoji']
            
            if category == 'Threat':
                messagebox.showwarning(
                    "⚠️ Threat Detected",
                    f"{emoji} {emotion} detected!\n\nThreat level: HIGH\nImmediate attention required."
                )
            elif category == 'Offensive':
                messagebox.showwarning(
                    "⚠️ Offensive Behavior",
                    f"{emoji} {emotion} detected!\n\nOffensive behavior observed.\nMonitor closely."
                )
            else:
                messagebox.showinfo(
                    "✅ Safe Behavior",
                    f"{emoji} {emotion} detected!\n\nSafe behavior observed.\nNo action required."
                )
        except:
            pass


# Utility functions
def save_analysis_results(results, output_path):
    """Save analysis results to file"""
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"Error saving results: {e}")
        return False


def load_analysis_results(input_path):
    """Load analysis results from file"""
    try:
        with open(input_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading results: {e}")
        return None


if __name__ == "__main__":
    # Test the analyzer
    analyzer = FacialEmotionAnalyzer()
    analyzer.start_initialization()
    
    print("Analyzer initialized. Test with:")
    print("  analyzer.analyze_image('path/to/image.jpg')")
    print("  analyzer.analyze_video_file('path/to/video.mp4')")
