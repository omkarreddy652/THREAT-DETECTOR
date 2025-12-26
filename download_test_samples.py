#!/usr/bin/env python3
"""
Voice Test Sample Downloader
Downloads and prepares test voice samples for the voice threat detection application
"""

import os
import requests
import tempfile
import wave
import numpy as np
from urllib.parse import urlparse
import zipfile
import json

class VoiceSampleDownloader:
    def __init__(self, output_dir="test_samples"):
        self.output_dir = output_dir
        self.samples_dir = os.path.join(output_dir, "voice_samples")
        os.makedirs(self.samples_dir, exist_ok=True)
        
        # Sample URLs (you can add more)
        self.sample_urls = {
            "normal_conversation": [
                "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",  # Example
            ],
            "aggressive_speech": [
                # Add URLs for aggressive speech samples
            ],
            "scam_content": [
                # Add URLs for scam-like content
            ],
            "distress_calls": [
                # Add URLs for distress samples
            ]
        }
    
    def create_synthetic_samples(self):
        """Create synthetic voice samples for testing"""
        print("🎤 Creating synthetic voice samples...")
        
        sample_rate = 16000
        
        # 1. Normal conversation (sine wave with modulation)
        print("   Creating normal conversation sample...")
        duration = 5
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Modulated sine wave to simulate speech
        base_freq = 200
        modulation = 0.5 * np.sin(2 * np.pi * 2 * t)  # Slow modulation
        audio_normal = np.sin(2 * np.pi * (base_freq + modulation * 50) * t) * 0.3
        
        self.save_audio(audio_normal, sample_rate, "normal_conversation.wav")
        
        # 2. Aggressive speech (higher frequency, more variation)
        print("   Creating aggressive speech sample...")
        aggressive_freq = 300
        aggressive_modulation = 1.0 * np.sin(2 * np.pi * 5 * t)  # Faster, stronger modulation
        audio_aggressive = np.sin(2 * np.pi * (aggressive_freq + aggressive_modulation * 100) * t) * 0.5
        
        self.save_audio(audio_aggressive, sample_rate, "aggressive_speech.wav")
        
        # 3. Scam content (monotone, repetitive)
        print("   Creating scam content sample...")
        scam_freq = 150
        scam_audio = np.sin(2 * np.pi * scam_freq * t) * 0.4
        # Add some variation to make it more realistic
        scam_audio += 0.1 * np.sin(2 * np.pi * 50 * t)
        
        self.save_audio(scam_audio, sample_rate, "scam_content.wav")
        
        # 4. Distress call (irregular, emotional)
        print("   Creating distress call sample...")
        distress_freq = 250
        # Irregular modulation to simulate emotional speech
        distress_modulation = 0.8 * np.sin(2 * np.pi * 3 * t) + 0.3 * np.sin(2 * np.pi * 7 * t)
        audio_distress = np.sin(2 * np.pi * (distress_freq + distress_modulation * 80) * t) * 0.4
        
        self.save_audio(audio_distress, sample_rate, "distress_call.wav")
        
        # 5. Background noise with speech
        print("   Creating background noise sample...")
        # Add some background noise
        noise = np.random.normal(0, 0.1, len(t))
        speech_with_noise = audio_normal + noise
        self.save_audio(speech_with_noise, sample_rate, "background_noise.wav")
        
        print("✅ Synthetic samples created successfully!")
    
    def save_audio(self, audio_data, sample_rate, filename):
        """Save audio data to WAV file"""
        filepath = os.path.join(self.samples_dir, filename)
        
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
        
        print(f"   Saved: {filename}")
    
    def download_from_url(self, url, filename):
        """Download audio file from URL"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            filepath = os.path.join(self.samples_dir, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"   Downloaded: {filename}")
            return True
            
        except Exception as e:
            print(f"   Failed to download {filename}: {e}")
            return False
    
    def create_test_manifest(self):
        """Create a manifest file with sample information"""
        manifest = {
            "samples": [],
            "categories": {
                "normal": "Safe, normal conversation",
                "aggressive": "Threatening or aggressive speech",
                "scam": "Scam or fraudulent content",
                "distress": "Distress or emergency calls",
                "noise": "Background noise with speech"
            }
        }
        
        # Scan samples directory
        for filename in os.listdir(self.samples_dir):
            if filename.endswith(('.wav', '.mp3')):
                category = "normal"  # Default
                if "aggressive" in filename.lower():
                    category = "aggressive"
                elif "scam" in filename.lower():
                    category = "scam"
                elif "distress" in filename.lower():
                    category = "distress"
                elif "noise" in filename.lower():
                    category = "noise"
                
                filepath = os.path.join(self.samples_dir, filename)
                file_size = os.path.getsize(filepath)
                
                manifest["samples"].append({
                    "filename": filename,
                    "category": category,
                    "size_bytes": file_size,
                    "path": filepath
                })
        
        # Save manifest
        manifest_path = os.path.join(self.output_dir, "test_manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"📋 Test manifest created: {manifest_path}")
        return manifest
    
    def run_quick_test(self):
        """Run a quick test on all samples"""
        print("\n🧪 Running quick test on all samples...")
        
        try:
            from model.voice_model import VoiceThreatClassifier
            classifier = VoiceThreatClassifier()
            
            manifest = self.create_test_manifest()
            
            for sample in manifest["samples"]:
                filepath = sample["path"]
                print(f"\n🎯 Testing: {sample['filename']} ({sample['category']})")
                
                try:
                    label, emoji, confidence = classifier.predict(filepath, fast_mode=True)
                    print(f"   Result: {emoji} {label} (Confidence: {confidence:.2f})")
                    
                    # Test additional features
                    intensity = classifier.analyze_voice_intensity(filepath)
                    pattern = classifier.detect_voice_patterns(filepath)
                    
                    if intensity:
                        threat_score = intensity.get('threat_score', 0)
                        print(f"   Intensity Threat Score: {threat_score:.2f}")
                    
                    if pattern:
                        pattern_score = pattern.get('pattern_score', 0)
                        print(f"   Pattern Score: {pattern_score:.2f}")
                    
                except Exception as e:
                    print(f"   ❌ Test failed: {e}")
            
            print("\n✅ Quick test completed!")
            
        except ImportError:
            print("❌ Voice classifier not available for testing")
    
    def print_usage_instructions(self):
        """Print instructions for using the test samples"""
        print("\n📖 Usage Instructions:")
        print("=" * 50)
        print("1. Test samples are saved in: test_samples/voice_samples/")
        print("2. Use these files to test your voice threat detection application")
        print("3. Categories:")
        print("   - normal_conversation.wav: Safe speech")
        print("   - aggressive_speech.wav: Threatening speech")
        print("   - scam_content.wav: Scam-like content")
        print("   - distress_call.wav: Distress indicators")
        print("   - background_noise.wav: Noisy environment")
        print("\n4. To test in your application:")
        print("   - Go to Voice Analyzer → Voice File Scanner")
        print("   - Browse and select any test file")
        print("   - Click 'Analyze Audio File'")
        print("\n5. For real-time testing:")
        print("   - Use Voice Analyzer → Live Mic Monitor")
        print("   - Play the test files through speakers")
        print("   - Or record your own test samples")

def main():
    """Main function"""
    print("🎤 Voice Test Sample Downloader")
    print("=" * 50)
    
    downloader = VoiceSampleDownloader()
    
    # Create synthetic samples
    downloader.create_synthetic_samples()
    
    # Create manifest
    downloader.create_test_manifest()
    
    # Print usage instructions
    downloader.print_usage_instructions()
    
    # Ask if user wants to run quick test
    response = input("\n🧪 Run quick test on samples? (y/n): ").lower().strip()
    if response == 'y':
        downloader.run_quick_test()
    
    print("\n🎉 Voice test samples ready!")
    print("=" * 50)

if __name__ == "__main__":
    main() 