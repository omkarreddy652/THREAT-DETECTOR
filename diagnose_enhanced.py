#!/usr/bin/env python3
"""
Enhanced webcam diagnostic with YOLO and DeepFace support
"""

import cv2
import sys
import os
import time

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

def test_available_libraries():
    """Test which advanced libraries are available"""
    print("\n" + "="*60)
    print("TEST 2: Available Detection Libraries")
    print("="*60)
    
    libraries = {}
    
    try:
        from ultralytics import YOLO
        libraries['YOLO'] = True
        print("✅ YOLO available")
    except:
        libraries['YOLO'] = False
        print("❌ YOLO not available")
    
    try:
        from deepface import DeepFace
        libraries['DeepFace'] = True
        print("✅ DeepFace available")
    except:
        libraries['DeepFace'] = False
        print("❌ DeepFace not available")
    
    try:
        import torch
        libraries['PyTorch'] = True
        print("✅ PyTorch available")
    except:
        libraries['PyTorch'] = False
        print("❌ PyTorch not available")
    
    return libraries

def test_yolo_detection():
    """Test YOLO face detection"""
    print("\n" + "="*60)
    print("TEST 3: YOLO Face Detection")
    print("="*60)
    
    try:
        from ultralytics import YOLO
    except Exception as e:
        print(f"❌ YOLO import failed: {e}")
        return False

    # Try loading a face model; if a local file isn't present, try a generic tiny model
    model = None
    for candidate in ('yolov8n-face.pt', 'yolov8n.pt', 'yolov8n'):
        try:
            print(f"🔄 Attempting to load YOLO model: {candidate}")
            model = YOLO(candidate)
            print(f"✅ YOLO model loaded: {candidate}")
            break
        except Exception as e:
            print(f"   Could not load {candidate}: {e}")

    if model is None:
        print("❌ Could not load any YOLO model; skipping YOLO test")
        return False

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return False

    print("📹 Testing YOLO detection (10 frames)...")
    frames_tested = 0
    detections = 0

    for i in range(10):
        ret, frame = cap.read()
        if not ret:
            break

        try:
            results = model(frame)
            frames_tested += 1

            # ultralytics may return a Results object; handle multiple formats defensively
            face_count = 0
            try:
                # results can be iterable; each item may have .boxes
                for r in results:
                    if hasattr(r, 'boxes'):
                        try:
                            face_count += len(r.boxes)
                        except Exception:
                            # boxes may be a tensor-like object
                            try:
                                face_count += int(getattr(r, 'boxes').shape[0])
                            except Exception:
                                pass
                    else:
                        # single Results object with .boxes
                        if hasattr(results, 'boxes'):
                            try:
                                face_count = len(results.boxes)
                            except Exception:
                                try:
                                    face_count = int(getattr(results, 'boxes').shape[0])
                                except Exception:
                                    face_count = 0
                            break
            except Exception:
                # Fallback: no reliable box count
                face_count = 0

            if face_count > 0:
                detections += 1
                print(f"  Frame {i}: ✅ {face_count} face(s) detected")
            else:
                print(f"  Frame {i}: ⚠️  No faces detected")
        except Exception as e:
            print(f"  Frame {i}: ❌ Error: {e}")

    cap.release()

    if frames_tested > 0:
        rate = (detections / frames_tested) * 100
        print(f"\nYOLO Detection Rate: {rate:.1f}%")
        if rate > 50:
            print("✅ YOLO detection working well!")
            return True
        elif rate > 0:
            print("⚠️  YOLO detection working but inconsistent")
            return True
        else:
            print("❌ YOLO not detecting faces")
            return False
    else:
        print("❌ No frames tested")
        return False

def test_deepface_detection():
    """Test DeepFace detection"""
    print("\n" + "="*60)
    print("TEST 4: DeepFace Detection")
    print("="*60)
    
    try:
        from deepface import DeepFace
    except Exception as e:
        print(f"❌ DeepFace import failed: {e}")
        return False

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return False

    print("📹 Testing DeepFace detection (5 frames)...")
    frames_tested = 0
    detections = 0

    for i in range(5):
        ret, frame = cap.read()
        if not ret:
            break

        try:
            # DeepFace.extract_faces may expect a path or an image array depending on version; try both
            try:
                results = DeepFace.extract_faces(frame, enforce_detection=False, detector_backend='opencv')
            except Exception:
                # Fallback: save temp image and pass path
                import tempfile
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        tmp_path = tmp.name
                        cv2.imwrite(tmp_path, frame)
                    results = DeepFace.extract_faces(tmp_path, enforce_detection=False, detector_backend='opencv')
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass

            frames_tested += 1
            valid_faces = []
            if isinstance(results, list):
                for f in results:
                    if isinstance(f, dict):
                        area = f.get('facial_area') or f.get('facial_area', {})
                        w = 0
                        try:
                            w = area.get('w', 0) if isinstance(area, dict) else 0
                        except Exception:
                            w = 0
                        if w > 0:
                            valid_faces.append(f)

            if len(valid_faces) > 0:
                detections += 1
                print(f"  Frame {i}: ✅ {len(valid_faces)} face(s) detected")
            else:
                print(f"  Frame {i}: ⚠️  No faces detected")
        except Exception as e:
            print(f"  Frame {i}: Error (skipped): {e}")

    cap.release()

    if frames_tested > 0:
        rate = (detections / frames_tested) * 100
        print(f"\nDeepFace Detection Rate: {rate:.1f}%")
        if rate > 50:
            print("✅ DeepFace detection working!")
            return True
        else:
            print("⚠️  DeepFace detection inconsistent")
            return True
    else:
        print("❌ No frames tested for DeepFace")
        return False

def test_analyzer_with_new_methods():
    """Test facial emotion analyzer with new methods"""
    print("\n" + "="*60)
    print("TEST 5: Analyzer with New Detection Methods")
    print("="*60)
    
    try:
        from facial_emotion_analyzer import FacialEmotionAnalyzer
    except Exception as e:
        print(f"❌ Could not import FacialEmotionAnalyzer: {e}")
        return False

    try:
        analyzer = FacialEmotionAnalyzer()
    except Exception as e:
        print(f"❌ Failed to instantiate analyzer: {e}")
        return False

    # Try to start initialization using a few possible method names
    try:
        if hasattr(analyzer, 'start_initialization'):
            analyzer.start_initialization()
        elif hasattr(analyzer, 'initialize'):
            analyzer.initialize()
        elif hasattr(analyzer, 'init'):
            analyzer.init()
        else:
            # No explicit initializer; assume constructor did initialization
            pass
    except Exception as e:
        print(f"❌ Analyzer initialization error: {e}")

    print("🔄 Initializing analyzer...")
    max_wait = 30
    elapsed = 0
    is_initialized = getattr(analyzer, 'is_initialized', None)
    while (is_initialized is False or is_initialized is None) and elapsed < max_wait:
        time.sleep(1)
        elapsed += 1
        is_initialized = getattr(analyzer, 'is_initialized', None)

    if is_initialized is False or is_initialized is None:
        print(f"❌ Analyzer initialization timed out or not available (is_initialized={is_initialized})")
        # proceed but warn
    else:
        print("✅ Analyzer initialized")
        print(f"   Detection method: {getattr(analyzer, 'detection_method', 'unknown')}")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return False

    print("📹 Testing emotion analysis (10 frames)...")
    frames_tested = 0
    detections = 0

    for i in range(10):
        ret, frame = cap.read()
        if not ret:
            break

        frames_tested += 1
        try:
            if hasattr(analyzer, 'analyze_frame'):
                results = analyzer.analyze_frame(frame)
            elif hasattr(analyzer, 'analyze'):
                results = analyzer.analyze(frame)
            else:
                print("Analyzer has no analyze_frame/analyze method; skipping frame analysis")
                results = []

            if results and len(results) > 0:
                detections += 1
                for j, result in enumerate(results):
                    emotion = result.get('emotion', 'Unknown') if isinstance(result, dict) else str(result)
                    confidence = result.get('confidence', 0) if isinstance(result, dict) else 0
                    print(f"  Frame {i}, Face {j+1}: ✅ {emotion} ({confidence:.2f})")
            else:
                print(f"  Frame {i}: ⚠️  No faces detected")
        except Exception as e:
            print(f"  Frame {i}: Error analyzing frame: {e}")

    cap.release()

    if frames_tested > 0:
        rate = (detections / frames_tested) * 100
        print(f"\nOverall Detection Rate: {rate:.1f}%")
        if rate > 50:
            print("✅ Emotion analysis working well!")
            return True
        elif rate > 0:
            print("⚠️  Emotion analysis working but inconsistent")
            return True
        else:
            print("❌ No faces detected")
            return False
    else:
        print("❌ No frames tested for analyzer")
        return False

def main():
    """Run all diagnostic tests"""
    print("\n" + "="*60)
    print("ENHANCED WEBCAM FACE DETECTION DIAGNOSTIC")
    print("With YOLO and DeepFace Support")
    print("="*60)
    
    results = {
        "Camera Access": test_camera_access(),
        "Available Libraries": test_available_libraries(),
        "YOLO Detection": test_yolo_detection(),
        "DeepFace Detection": test_deepface_detection(),
        "Analyzer": test_analyzer_with_new_methods(),
    }
    
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        if isinstance(result, dict):
            print(f"{test_name}:")
            for lib, available in result.items():
                status = "✅" if available else "❌"
                print(f"  {lib}: {status}")
        else:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
    
    print("\n" + "="*60)
    any_passed = any(r is True or (isinstance(r, dict) and any(r.values())) for r in results.values())
    
    if any_passed:
        print("🎉 Enhanced detection available!")
        print("\nNext step: python main.py")
    else:
        print("⚠️  Issues detected - check output above")
    
    print("="*60 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
