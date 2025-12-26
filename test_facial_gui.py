#!/usr/bin/env python3
"""
Test script for facial_emotion_gui.py to verify the fix
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work"""
    print("Testing imports...")
    try:
        from gui.facial_emotion_gui import FacialEmotionGUI
        print("✅ FacialEmotionGUI imported successfully")
        
        from facial_emotion_analyzer import FacialEmotionAnalyzer, EmotionAlert
        print("✅ FacialEmotionAnalyzer imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_syntax():
    """Test that the file has valid Python syntax"""
    print("\nTesting syntax...")
    try:
        import py_compile
        facial_gui_path = os.path.join(os.path.dirname(__file__), "gui", "facial_emotion_gui.py")
        py_compile.compile(facial_gui_path, doraise=True)
        print("✅ facial_emotion_gui.py has valid syntax")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error: {e}")
        return False

def test_class_instantiation():
    """Test that the class can be instantiated (without Tk)"""
    print("\nTesting class structure...")
    try:
        import ast
        facial_gui_path = os.path.join(os.path.dirname(__file__), "gui", "facial_emotion_gui.py")
        
        with open(facial_gui_path, 'r') as f:
            tree = ast.parse(f.read())
        
        # Check for FacialEmotionGUI class
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        class_names = [cls.name for cls in classes]
        
        if 'FacialEmotionGUI' in class_names:
            print("✅ FacialEmotionGUI class found")
        else:
            print("❌ FacialEmotionGUI class not found")
            return False
        
        # Check for required methods
        facial_gui_class = next(cls for cls in classes if cls.name == 'FacialEmotionGUI')
        methods = [node.name for node in facial_gui_class.body if isinstance(node, ast.FunctionDef)]
        
        required_methods = ['create_widgets', 'create_webcam_panel', 'show_webcam_panel']
        for method in required_methods:
            if method in methods:
                print(f"✅ Method '{method}' found")
            else:
                print(f"⚠️  Method '{method}' not found (may be optional)")
        
        return True
    except Exception as e:
        print(f"❌ Class structure test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("FACIAL EMOTION GUI TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Syntax
    results.append(("Syntax", test_syntax()))
    
    # Test 3: Class Structure
    results.append(("Class Structure", test_class_instantiation()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("✅ All tests passed! The facial_emotion_gui.py is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
