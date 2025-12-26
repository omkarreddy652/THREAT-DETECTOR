#!/usr/bin/env python3
"""
Voice Test Sample Recorder
Record your own test voice samples for the voice threat detection application
"""

import os
import time
import wave
import numpy as np
import sounddevice as sd
import threading
from datetime import datetime

class VoiceSampleRecorder:
    def __init__(self, output_dir="test_samples/voice_samples"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.sample_rate = 16000
        self.is_recording = False
        self.recording_data = []
        
        # Test scenarios
        self.test_scenarios = {
            "1": {
                "name": "normal_conversation",
                "description": "Normal, calm conversation",
                "example": "Hello, how are you today? The weather is nice."
            },
            "2": {
                "name": "aggressive_speech",
                "description": "Angry or threatening speech",
                "example": "I'm going to hurt you! You better watch out!"
            },
            "3": {
                "name": "scam_content",
                "description": "Scam or fraudulent content",
                "example": "You've won a prize! Send me your bank details immediately!"
            },
            "4": {
                "name": "distress_call",
                "description": "Distress or emergency call",
                "example": "Help! I need help! There's an emergency!"
            },
            "5": {
                "name": "background_noise",
                "description": "Speech with background noise",
                "example": "Hello, can you hear me? (with TV/music in background)"
            }
        }
    
    def print_menu(self):
        """Print the main menu"""
        print("\n🎤 Voice Test Sample Recorder")
        print("=" * 50)
        print("Choose an option:")
        print("1. Record test samples")
        print("2. List existing samples")
        print("3. Play existing samples")
        print("4. Delete samples")
        print("5. Exit")
        print("=" * 50)
    
    def print_scenarios(self):
        """Print available test scenarios"""
        print("\n📝 Available Test Scenarios:")
        print("-" * 40)
        for key, scenario in self.test_scenarios.items():
            print(f"{key}. {scenario['name'].replace('_', ' ').title()}")
            print(f"   Description: {scenario['description']}")
            print(f"   Example: \"{scenario['example']}\"")
            print()
    
    def record_sample(self, scenario_key):
        """Record a voice sample for the given scenario"""
        if scenario_key not in self.test_scenarios:
            print("❌ Invalid scenario key")
            return
        
        scenario = self.test_scenarios[scenario_key]
        
        print(f"\n🎙️ Recording: {scenario['name'].replace('_', ' ').title()}")
        print(f"Description: {scenario['description']}")
        print(f"Example: \"{scenario['example']}\"")
        print("\nPress Enter when ready to record (5 seconds)...")
        input()
        
        # Countdown
        for i in range(5, 0, -1):
            print(f"Recording in {i}...")
            time.sleep(1)
        
        print("🎙️ RECORDING NOW! Speak clearly...")
        
        # Record audio
        duration = 5  # 5 seconds
        recording = sd.rec(int(self.sample_rate * duration), 
                          samplerate=self.sample_rate, 
                          channels=1, 
                          dtype=np.float32)
        sd.wait()
        
        print("✅ Recording complete!")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{scenario['name']}_{timestamp}.wav"
        filepath = os.path.join(self.output_dir, filename)
        
        # Save recording
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes((recording * 32767).astype(np.int16).tobytes())
        
        print(f"💾 Saved: {filename}")
        
        # Ask if user wants to play it back
        response = input("🔊 Play back the recording? (y/n): ").lower().strip()
        if response == 'y':
            self.play_sample(filepath)
    
    def play_sample(self, filepath):
        """Play a voice sample"""
        try:
            print(f"🔊 Playing: {os.path.basename(filepath)}")
            
            # Load and play audio
            data, samplerate = sd.read(filepath)
            sd.play(data, samplerate)
            sd.wait()
            
            print("✅ Playback complete!")
            
        except Exception as e:
            print(f"❌ Failed to play sample: {e}")
    
    def list_samples(self):
        """List all existing samples"""
        print("\n📁 Existing Voice Samples:")
        print("-" * 40)
        
        if not os.path.exists(self.output_dir):
            print("No samples directory found.")
            return
        
        files = [f for f in os.listdir(self.output_dir) if f.endswith('.wav')]
        
        if not files:
            print("No voice samples found.")
            return
        
        for i, filename in enumerate(sorted(files), 1):
            filepath = os.path.join(self.output_dir, filename)
            file_size = os.path.getsize(filepath)
            file_size_kb = file_size / 1024
            
            # Determine category
            category = "Unknown"
            for scenario in self.test_scenarios.values():
                if scenario['name'] in filename:
                    category = scenario['name'].replace('_', ' ').title()
                    break
            
            print(f"{i:2d}. {filename}")
            print(f"    Category: {category}")
            print(f"    Size: {file_size_kb:.1f} KB")
            print()
    
    def delete_samples(self):
        """Delete voice samples"""
        print("\n🗑️ Delete Voice Samples:")
        print("-" * 40)
        
        if not os.path.exists(self.output_dir):
            print("No samples directory found.")
            return
        
        files = [f for f in os.listdir(self.output_dir) if f.endswith('.wav')]
        
        if not files:
            print("No voice samples found.")
            return
        
        print("Existing samples:")
        for i, filename in enumerate(sorted(files), 1):
            print(f"{i}. {filename}")
        
        print("\nOptions:")
        print("1. Delete specific sample")
        print("2. Delete all samples")
        print("3. Cancel")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            try:
                index = int(input("Enter sample number to delete: ")) - 1
                if 0 <= index < len(files):
                    filename = sorted(files)[index]
                    filepath = os.path.join(self.output_dir, filename)
                    
                    confirm = input(f"Delete {filename}? (y/n): ").lower().strip()
                    if confirm == 'y':
                        os.remove(filepath)
                        print(f"✅ Deleted: {filename}")
                    else:
                        print("❌ Deletion cancelled.")
                else:
                    print("❌ Invalid sample number.")
            except ValueError:
                print("❌ Invalid input.")
        
        elif choice == "2":
            confirm = input("Delete ALL samples? (y/n): ").lower().strip()
            if confirm == 'y':
                for filename in files:
                    filepath = os.path.join(self.output_dir, filename)
                    os.remove(filepath)
                print("✅ All samples deleted.")
            else:
                print("❌ Deletion cancelled.")
        
        elif choice == "3":
            print("❌ Operation cancelled.")
        
        else:
            print("❌ Invalid choice.")
    
    def record_multiple_samples(self):
        """Record multiple test samples"""
        print("\n🎙️ Record Multiple Test Samples")
        print("-" * 40)
        
        self.print_scenarios()
        
        print("Options:")
        print("1. Record all scenarios")
        print("2. Record specific scenario")
        print("3. Back to main menu")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            print("\n🎙️ Recording all scenarios...")
            for key in self.test_scenarios.keys():
                self.record_sample(key)
                time.sleep(1)  # Brief pause between recordings
        
        elif choice == "2":
            scenario_key = input("Enter scenario number (1-5): ").strip()
            if scenario_key in self.test_scenarios:
                self.record_sample(scenario_key)
            else:
                print("❌ Invalid scenario number.")
        
        elif choice == "3":
            return
        
        else:
            print("❌ Invalid choice.")
    
    def run(self):
        """Run the voice sample recorder"""
        while True:
            self.print_menu()
            choice = input("Enter choice (1-5): ").strip()
            
            if choice == "1":
                self.record_multiple_samples()
            
            elif choice == "2":
                self.list_samples()
            
            elif choice == "3":
                self.list_samples()
                if os.path.exists(self.output_dir):
                    files = [f for f in os.listdir(self.output_dir) if f.endswith('.wav')]
                    if files:
                        try:
                            index = int(input("Enter sample number to play: ")) - 1
                            if 0 <= index < len(files):
                                filename = sorted(files)[index]
                                filepath = os.path.join(self.output_dir, filename)
                                self.play_sample(filepath)
                            else:
                                print("❌ Invalid sample number.")
                        except ValueError:
                            print("❌ Invalid input.")
            
            elif choice == "4":
                self.delete_samples()
            
            elif choice == "5":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice.")
            
            input("\nPress Enter to continue...")

def main():
    """Main function"""
    print("🎤 Voice Test Sample Recorder")
    print("=" * 50)
    print("This tool helps you record test voice samples for your")
    print("voice threat detection application.")
    print("=" * 50)
    
    recorder = VoiceSampleRecorder()
    recorder.run()

if __name__ == "__main__":
    main() 