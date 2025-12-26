#!/usr/bin/env python3
"""
Alternative face detection implementations
Provides multiple methods to detect faces when Haar Cascade fails
"""

import cv2
from typing import List, Tuple

try:
    import dlib
    DLIB_AVAILABLE = True
except ImportError:
    DLIB_AVAILABLE = False
    print("⚠️  dlib not installed - using Haar Cascade fallback")

try:
    from mediapipe.python.solutions import face_detection as mp_face_detection
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("⚠️  MediaPipe not installed - using Haar Cascade fallback")


class FaceDetector:
    """Multi-method face detector with fallbacks"""
    
    def __init__(self):
        """Initialize all available face detection methods"""
        self.haar_cascade = None
        self.dlib_detector = None
        self.mediapipe_detector = None

        self._init_haar_cascade()
        self._init_dlib()
        self._init_mediapipe()
    
    def _init_haar_cascade(self):
        """Initialize OpenCV Haar Cascade"""
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.haar_cascade = cv2.CascadeClassifier(cascade_path)
            if self.haar_cascade.empty():
                print("❌ Failed to load Haar Cascade")
                self.haar_cascade = None
            else:
                print("✅ Haar Cascade loaded")
        except Exception as e:
            print(f"❌ Error loading Haar Cascade: {e}")
    
    def _init_dlib(self):
        """Initialize dlib HOG face detector"""
        if not DLIB_AVAILABLE:
            return
        try:
            self.dlib_detector = dlib.get_frontal_face_detector()
            print("✅ dlib HOG detector loaded")
        except Exception as e:
            print(f"❌ Error initializing dlib: {e}")
    
    def _init_mediapipe(self):
        """Initialize MediaPipe face detection"""
        if not MEDIAPIPE_AVAILABLE:
            return
        try:
            self.mediapipe_detector = mp_face_detection.FaceDetection(
                model_selection=1,  # 1 = full range
                min_detection_confidence=0.3
            )
            print("✅ MediaPipe face detection loaded")
        except Exception as e:
            print(f"❌ Error initializing MediaPipe: {e}")
    
    def detect_faces_haar(self, frame) -> List[Tuple[int, int, int, int]]:
        """Detect faces using Haar Cascade"""
        if self.haar_cascade is None:
            return []
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Preprocess for better detection
        gray_equalized = cv2.equalizeHist(gray)
        gray_blurred = cv2.GaussianBlur(gray_equalized, (5, 5), 0)
        
        for detection_image in [gray, gray_equalized, gray_blurred]:
            # Try multiple parameter sets
            for scale_factor, min_neighbors, min_size in [
                (1.02, 2, (15, 15)),   # Ultra-sensitive
                (1.05, 3, (20, 20)),   # Very sensitive
                (1.1, 4, (25, 25)),    # Balanced
                (1.15, 5, (30, 30)),   # Standard
            ]:
                faces = self.haar_cascade.detectMultiScale(
                    detection_image,
                    scaleFactor=scale_factor,
                    minNeighbors=min_neighbors,
                    minSize=min_size,
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                if len(faces) > 0:
                    return [(x, y, w, h) for (x, y, w, h) in faces]
        
        return []
    
    def detect_faces_dlib(self, frame) -> List[Tuple[int, int, int, int]]:
        """Detect faces using dlib HOG detector"""
        if self.dlib_detector is None:
            return []
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # dlib returns dlib rectangles, convert to OpenCV format
            dlib_faces = self.dlib_detector(gray, 1)  # 1 = upsample once for better accuracy
            
            faces = []
            for face in dlib_faces:
                x, y = face.left(), face.top()
                w, h = face.width(), face.height()
                faces.append((x, y, w, h))
            
            return faces
        except Exception as e:
            print(f"Error in dlib detection: {e}")
            return []
    
    def detect_faces_mediapipe(self, frame) -> List[Tuple[int, int, int, int]]:
        """Detect faces using MediaPipe"""
        if self.mediapipe_detector is None:
            return []
        
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.mediapipe_detector.process(frame_rgb)
            
            faces = []
            if results.detections:
                height, width = frame.shape[:2]
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    x = int(bbox.xmin * width)
                    y = int(bbox.ymin * height)
                    w = int(bbox.width * width)
                    h = int(bbox.height * height)
                    faces.append((x, y, w, h))
            
            return faces
        except Exception as e:
            print(f"Error in MediaPipe detection: {e}")
            return []
    
    def detect_faces(self, frame) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using best available method
        Tries in order: MediaPipe → dlib → Haar Cascade
        """
        # Try MediaPipe first (most accurate)
        if self.mediapipe_detector is not None:
            faces = self.detect_faces_mediapipe(frame)
            if len(faces) > 0:
                return faces
        
        # Try dlib second (good balance)
        if self.dlib_detector is not None:
            faces = self.detect_faces_dlib(frame)
            if len(faces) > 0:
                return faces
        
        # Fall back to Haar Cascade
        if self.haar_cascade is not None:
            faces = self.detect_faces_haar(frame)
            if len(faces) > 0:
                return faces
        
        return []
    
    def get_available_methods(self) -> dict:
        """Get information about available detection methods"""
        return {
            'Haar Cascade': self.haar_cascade is not None,
            'dlib HOG': self.dlib_detector is not None,
            'MediaPipe': self.mediapipe_detector is not None,
        }


def main():
    """Test the multi-method face detector"""
    print("\nInitializing multi-method face detector...")
    print("=" * 60)
    
    detector = FaceDetector()
    
    print("\nAvailable detection methods:")
    for method, available in detector.get_available_methods().items():
        status = "✅ Available" if available else "❌ Not available"
        print(f"  {method}: {status}")
    
    print("\n" + "=" * 60)
    print("Testing on live camera (30 frames)...")
    print("=" * 60 + "\n")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return
    
    detections_count = 0
    frames_tested = 0
    
    for i in range(30):
        ret, frame = cap.read()
        if not ret:
            break
        
        faces = detector.detect_faces(frame)
        frames_tested += 1
        
        if len(faces) > 0:
            detections_count += 1
            print(f"Frame {i}: ✅ Detected {len(faces)} face(s)")
        else:
            print(f"Frame {i}: ⚠️  No faces detected")
    
    cap.release()
    
    print("\n" + "=" * 60)
    print("Results:")
    print(f"  Frames tested: {frames_tested}")
    print(f"  Frames with detections: {detections_count}")
    detection_rate = (detections_count / frames_tested * 100) if frames_tested > 0 else 0
    print(f"  Detection rate: {detection_rate:.1f}%")
    print("=" * 60 + "\n")
    
    if detection_rate > 50:
        print("✅ Face detection working well!")
    elif detection_rate > 0:
        print("⚠️  Face detection working but inconsistent")
    else:
        print("❌ Face detection still not working")
        print("\nTroubleshooting:")
        print("  1. Check camera is working and face is visible")
        print("  2. Try installing MediaPipe: pip install mediapipe")
        print("  3. Try installing dlib: pip install dlib")
        print("  4. Ensure good lighting and clear face view")


if __name__ == "__main__":
    main()
