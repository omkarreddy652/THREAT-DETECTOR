#!/usr/bin/env python3
"""
Diagnostic script to debug webcam face detection issues
"""

import cv2
import sys
import os

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_camera_access():
    """Test if camera can be accessed"""
    print("\n" + "="*60)
    print("TEST 1: Camera Access")
    print("="*60)
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                height, width = frame.shape[:2]
                print(f"✅ Camera opened successfully")
                print(f"   Resolution: {width}x{height}")
                cap.release()
                return True
            else:
                print("❌ Camera opened but cannot read frame")
                return False
        else:
            print("❌ Cannot open camera")
            return False
    except Exception as e:
        print(f"❌ Error accessing camera: {e}")
        return False

def test_haar_cascade():
    """Test if Haar cascade loads properly"""
    print("\n" + "="*60)
    print("TEST 2: Haar Cascade Loading")
    print("="*60)
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if face_cascade.empty():
            print(f"❌ Failed to load Haar cascade from: {cascade_path}")
            return False
        else:
            print(f"✅ Haar cascade loaded successfully")
            print(f"   Path: {cascade_path}")
            return True
    except Exception as e:
        print(f"❌ Error loading Haar cascade: {e}")
        return False

def test_face_detection():
    """Test if face detection works"""
    print("\n" + "="*60)
    print("TEST 3: Face Detection on Live Camera")
    print("="*60)
    try:
        cap = cv2.VideoCapture(0)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if not cap.isOpened():
            print("❌ Cannot open camera")
            return False
        
        if face_cascade.empty():
            print("❌ Cannot load Haar cascade")
            return False
        
        print("📹 Capturing frames... (will test 30 frames)")
        frames_tested = 0
        faces_detected = 0
        
        for i in range(30):
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            frames_tested += 1
            if len(faces) > 0:
                faces_detected += 1
                print(f"   Frame {i}: ✅ {len(faces)} face(s) detected")
        
        cap.release()
        
        print(f"\nSummary:")
        print(f"  Frames tested: {frames_tested}")
        print(f"  Frames with faces: {faces_detected}")
        detection_rate = (faces_detected / frames_tested * 100) if frames_tested > 0 else 0
        print(f"  Detection rate: {detection_rate:.1f}%")
        
        if detection_rate > 50:
            print(f"✅ Face detection working well")
            return True
        elif detection_rate > 0:
            print(f"⚠️  Face detection working but inconsistent - may need parameter tuning")
            print(f"   Try: scaleFactor=1.05, minNeighbors=3, or increase face size")
            return True
        else:
            print(f"❌ Face detection not working - no faces detected in any frame")
            print(f"   Tips:")
            print(f"   - Ensure your face is clearly visible")
            print(f"   - Try different lighting conditions")
            print(f"   - Adjust Haar cascade parameters:")
            print(f"     * Lower scaleFactor (1.05 instead of 1.1)")
            print(f"     * Lower minNeighbors (3 instead of 5)")
            print(f"     * Try minSize=(20, 20) instead of (30, 30)")
            return False
        
    except Exception as e:
        print(f"❌ Error during face detection test: {e}")
        return False

def test_analyzer_initialization():
    """Test if analyzer initializes properly"""
    print("\n" + "="*60)
    print("TEST 4: Analyzer Initialization")
    print("="*60)
    try:
        from facial_emotion_analyzer import FacialEmotionAnalyzer
        
        analyzer = FacialEmotionAnalyzer()
        print("✅ FacialEmotionAnalyzer imported successfully")
        
        # Start initialization
        analyzer.start_initialization()
        print("🔄 Started model initialization in background thread...")
        
        # Wait for initialization
        import time
        max_wait = 30  # seconds
        elapsed = 0
        
        while not analyzer.is_initialized and elapsed < max_wait:
            time.sleep(1)
            elapsed += 1
            print(f"   Waiting... {elapsed}s")
        
        if analyzer.is_initialized:
            model_type = "Pre-trained" if analyzer.use_pre_trained else "Custom CNN"
            print(f"✅ Analyzer initialized successfully")
            print(f"   Model type: {model_type}")
            return True
        else:
            print(f"❌ Analyzer initialization timed out after {max_wait} seconds")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing analyzer: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frame_analysis():
    """Test if analyzer can analyze a frame"""
    print("\n" + "="*60)
    print("TEST 5: Frame Analysis with Analyzer")
    print("="*60)
    try:
        from facial_emotion_analyzer import FacialEmotionAnalyzer
        import time
        
        analyzer = FacialEmotionAnalyzer()
        analyzer.start_initialization()
        
        # Wait for initialization
        print("🔄 Waiting for analyzer initialization...")
        max_wait = 30
        elapsed = 0
        
        while not analyzer.is_initialized and elapsed < max_wait:
            time.sleep(1)
            elapsed += 1
        
        if not analyzer.is_initialized:
            print(f"❌ Analyzer not initialized after {max_wait} seconds")
            return False
        
        print("✅ Analyzer initialized")
        
        # Capture frame and analyze
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open camera")
            return False
        
        print("📹 Capturing and analyzing frames...")
        frames_tested = 0
        results_received = 0
        
        for i in range(30):
            ret, frame = cap.read()
            if not ret:
                break
            
            results = analyzer.analyze_frame(frame)
            frames_tested += 1
            
            if results:
                results_received += 1
                print(f"   Frame {i}: ✅ Analysis returned {len(results)} result(s)")
                for j, result in enumerate(results):
                    emotion = result.get('emotion', 'Unknown')
                    confidence = result.get('confidence', 0)
                    print(f"      Face {j+1}: {emotion} (confidence: {confidence:.2f})")
            else:
                print(f"   Frame {i}: ⚠️  No results (face not detected or confidence too low)")
        
        cap.release()
        
        print(f"\nSummary:")
        print(f"  Frames tested: {frames_tested}")
        print(f"  Frames with results: {results_received}")
        rate = (results_received / frames_tested * 100) if frames_tested > 0 else 0
        print(f"  Success rate: {rate:.1f}%")
        
        if rate > 50:
            print(f"✅ Frame analysis working well")
            return True
        elif rate > 0:
            print(f"⚠️  Frame analysis working but inconsistent")
            print(f"   Tips: Check lighting, face positioning, or confidence threshold")
            return True
        else:
            print(f"❌ Frame analysis not returning results")
            print(f"   Possible issues:")
            print(f"   - Face detection failing (test #3 above)")
            print(f"   - Model not initialized properly")
            print(f"   - Confidence threshold too high (currently 0.3)")
            return False
            
    except Exception as e:
        print(f"❌ Error during frame analysis test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests"""
    print("\n" + "="*60)
    print("WEBCAM FACE DETECTION DIAGNOSTIC")
    print("="*60)
    
    results = {
        "Camera Access": test_camera_access(),
        "Haar Cascade": test_haar_cascade(),
        "Face Detection": test_face_detection(),
        "Analyzer Init": test_analyzer_initialization(),
        "Frame Analysis": test_frame_analysis(),
    }
    
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print("\n" + "="*60)
    all_passed = all(results.values())
    
    if all_passed:
        print("🎉 All diagnostics passed! System should work correctly.")
    else:
        print("⚠️  Some diagnostics failed. Check the details above.")
        print("\nCommon fixes:")
        print("1. Ensure good lighting conditions")
        print("2. Position face clearly in front of camera")
        print("3. Check camera permissions")
        print("4. Try different camera angle")
        print("5. Restart the application")
    
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
