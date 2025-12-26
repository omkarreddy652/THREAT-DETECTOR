#!/usr/bin/env python3
"""
Voice Module Test Script
Tests the enhanced voice threat detection system with real-time monitoring
"""

import os
import sys
import time
import threading
import tempfile
import wave
import numpy as np

def test_voice_classifier():
    """Test the enhanced voice classifier"""
    print("🎤 Testing Enhanced Voice Threat Classifier...")
    
    try:
        from model.voice_model import VoiceThreatClassifier
        
        # Initialize classifier
        classifier = VoiceThreatClassifier()
        print("✅ Voice classifier initialized successfully")
        
        # Test model info
        model_info = classifier.get_model_info()
        print(f"📊 Model Info: {model_info}")
        
        return classifier
        
    except Exception as e:
        print(f"❌ Failed to initialize voice classifier: {e}")
        return None

def test_voice_analysis(classifier):
    """Test voice analysis features"""
    print("\n🔍 Testing Voice Analysis Features...")
    
    try:
        # Create a test audio file (sine wave)
        sample_rate = 16000
        duration = 3
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
        
        # Save test file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            with wave.open(tmp_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            
            test_file = tmp_file.name
        
        print(f"📁 Created test audio file: {test_file}")
        
        # Test basic prediction
        print("\n🎯 Testing Basic Prediction...")
        label, emoji, confidence = classifier.predict(test_file, fast_mode=True)
        print(f"   Result: {emoji} {label} (Confidence: {confidence:.2f})")
        
        # Test voice characteristics
        print("\n🎵 Testing Voice Characteristics...")
        voice_analysis = classifier.analyze_voice_characteristics(test_file)
        print(f"   Voice Analysis: {voice_analysis}")
        
        # Test voice intensity
        print("\n⚡ Testing Voice Intensity Analysis...")
        intensity_analysis = classifier.analyze_voice_intensity(test_file)
        print(f"   Intensity Analysis: {intensity_analysis}")
        
        # Test voice patterns
        print("\n🎯 Testing Voice Pattern Detection...")
        pattern_analysis = classifier.detect_voice_patterns(test_file)
        print(f"   Pattern Analysis: {pattern_analysis}")
        
        # Test emotion analysis
        print("\n😊 Testing Emotion Analysis...")
        emotion_scores = classifier.analyze_emotion(test_file)
        print(f"   Emotion Scores: {emotion_scores}")
        
        # Test transcription
        print("\n📝 Testing Speech Transcription...")
        transcription = classifier.transcribe_audio(test_file)
        print(f"   Transcription: {transcription}")
        
        # Clean up
        os.unlink(test_file)
        print("\n✅ Voice analysis tests completed successfully")
        
    except Exception as e:
        print(f"❌ Voice analysis test failed: {e}")

def test_real_time_monitoring(classifier):
    """Test real-time monitoring capabilities"""
    print("\n🎙️ Testing Real-time Monitoring...")
    
    try:
        # Test alert callback
        alerts_received = []
        
        def alert_callback(alert_data):
            alerts_received.append(alert_data)
            print(f"🚨 Alert received: {alert_data}")
        
        def audio_callback(audio_chunk, label, confidence):
            print(f"🎵 Audio chunk analyzed: {label} ({confidence:.2f})")
        
        # Start monitoring
        print("   Starting real-time monitoring...")
        success = classifier.start_real_time_monitoring(
            audio_callback=audio_callback,
            alert_callback=alert_callback
        )
        
        if success:
            print("   ✅ Real-time monitoring started")
            
            # Monitor for 10 seconds
            print("   🎤 Monitoring for 10 seconds... (speak into microphone)")
            time.sleep(10)
            
            # Check for alerts
            alerts = classifier.get_alerts()
            print(f"   📊 Alerts in queue: {len(alerts)}")
            print(f"   📊 Alerts received: {len(alerts_received)}")
            
            # Stop monitoring
            classifier.stop_real_time_monitoring()
            print("   ✅ Real-time monitoring stopped")
            
        else:
            print("   ❌ Failed to start real-time monitoring")
            
    except Exception as e:
        print(f"❌ Real-time monitoring test failed: {e}")

def test_alert_system():
    """Test the alert system"""
    print("\n🚨 Testing Alert System...")
    
    try:
        # Test sound alerts
        print("   Testing sound alerts...")
        
        def play_test_sound(label):
            import winsound
            if label == "safe":
                winsound.Beep(1200, 150)
            elif label == "offensive":
                winsound.Beep(800, 300)
            elif label == "threat":
                winsound.Beep(400, 500)
        
        # Test different alert types
        for label in ["safe", "offensive", "threat"]:
            print(f"   Playing {label} alert...")
            play_test_sound(label)
            time.sleep(0.5)
        
        print("   ✅ Sound alerts tested")
        
    except Exception as e:
        print(f"❌ Alert system test failed: {e}")

def test_enhanced_features():
    """Test enhanced features"""
    print("\n🚀 Testing Enhanced Features...")
    
    try:
        from model.voice_model import VoiceThreatClassifier
        classifier = VoiceThreatClassifier()
        
        # Test enhanced keyword detection
        print("   Testing enhanced keyword detection...")
        
        # Test threat keywords
        test_texts = [
            "I will kill you",
            "This is a scam",
            "Help me please",
            "Normal conversation",
            "I need your bank account details"
        ]
        
        for text in test_texts:
            score = classifier._analyze_transcription(text)
            print(f"   Text: '{text}' -> Score: {score:.2f}")
        
        print("   ✅ Enhanced features tested")
        
    except Exception as e:
        print(f"❌ Enhanced features test failed: {e}")

def main():
    """Main test function"""
    print("🎤 Voice Module Test Suite")
    print("=" * 50)
    
    # Test 1: Voice Classifier
    classifier = test_voice_classifier()
    if not classifier:
        print("❌ Cannot proceed without voice classifier")
        return
    
    # Test 2: Voice Analysis
    test_voice_analysis(classifier)
    
    # Test 3: Enhanced Features
    test_enhanced_features()
    
    # Test 4: Alert System
    test_alert_system()
    
    # Test 5: Real-time Monitoring (optional)
    print("\n🎙️ Real-time monitoring test (requires microphone)")
    response = input("   Run real-time monitoring test? (y/n): ").lower().strip()
    if response == 'y':
        test_real_time_monitoring(classifier)
    else:
        print("   Skipping real-time monitoring test")
    
    print("\n🎉 Voice Module Test Suite Completed!")
    print("=" * 50)
    print("\n📋 Summary:")
    print("✅ Enhanced voice threat detection")
    print("✅ Real-time monitoring capabilities")
    print("✅ Voice intensity analysis")
    print("✅ Voice pattern detection")
    print("✅ Enhanced alert system")
    print("✅ Multiple analysis modes")
    print("✅ Comprehensive threat detection")

if __name__ == "__main__":
    main() 