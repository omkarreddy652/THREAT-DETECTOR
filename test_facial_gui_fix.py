#!/usr/bin/env python3
"""
Test script to verify facial_emotion_gui.py fixes
Tests the missing method issue
"""

import sys
import os

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that the GUI can be imported"""
    try:
        from gui.facial_emotion_gui import FacialEmotionGUI
        print("✅ FacialEmotionGUI imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import FacialEmotionGUI: {e}")
        return False

def test_syntax():
    """Test Python syntax"""
    try:
        import py_compile
        py_compile.compile('gui/facial_emotion_gui.py', doraise=True)
        print("✅ gui/facial_emotion_gui.py has valid syntax")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error in gui/facial_emotion_gui.py: {e}")
        return False

def test_methods_exist():
    """Test that required methods exist"""
    try:
        from gui.facial_emotion_gui import FacialEmotionGUI
        
        # Check if methods exist
        methods_to_check = [
            'browse_video_file',
            'browse_image_file',
            'start_video_analysis',
            'start_image_analysis',
            'browse_video',
            'browse_image'
        ]
        
        missing = []
        for method_name in methods_to_check:
            if not hasattr(FacialEmotionGUI, method_name):
                missing.append(method_name)
        
        if missing:
            print(f"❌ Missing methods: {', '.join(missing)}")
            return False
        else:
            print(f"✅ All required methods exist: {', '.join(methods_to_check)}")
            return True
            
    except Exception as e:
        print(f"❌ Error checking methods: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Facial Emotion GUI Fixes")
    print("=" * 60)
    print()
    
    results = {
        "Imports": test_imports(),
        "Syntax": test_syntax(),
        "Methods": test_methods_exist()
    }
    
    print()
    print("=" * 60)
    print("Test Results:")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print()
    all_passed = all(results.values())
    if all_passed:
        print("🎉 All tests passed! The facial emotion GUI is fixed.")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
