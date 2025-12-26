import librosa
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import (
    Wav2Vec2ForSequenceClassification, 
    Wav2Vec2FeatureExtractor,
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline
)
import soundfile as sf
import os
import re
from typing import Tuple, Dict, List
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import requests
from huggingface_hub import hf_hub_download
import threading
import time
import queue
from model.text_model import TextThreatClassifier

class VoiceThreatClassifier:
    def __init__(self, model_path: str = None):
        """
        Initialize the Voice Threat Classifier with multiple pre-trained models
        
        Args:
            model_path: Path to pre-trained model (optional)
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.sample_rate = 16000
        self.max_length = 30  # seconds
        
        # Initialize models
        self.feature_extractor = None
        self.wav2vec_model = None
        self.rf_classifier = None
        self.scaler = StandardScaler()
        
        # Pre-trained models for different tasks
        self.emotion_classifier = None
        self.speech_recognizer = None
        self.toxicity_classifier = None
        self.sentiment_analyzer = None
        
        # Real-time monitoring
        self.is_monitoring = False
        self.alert_queue = queue.Queue()
        self.monitoring_thread = None
        
        # Load pre-trained models
        self._load_pretrained_models(model_path)
        
        # Enhanced threat keywords for audio transcription analysis
        self.threat_keywords = [
            r'\bkill\b', r'\battack\b', r'\bbomb\b', r'\bshoot\b', r'\bdie\b',
            r'\bmurder\b', r'\bthreat\b', r'\bharm\b', r'\bscam\b', r'\bfraud\b',
            r'\bsteal\b', r'\bblackmail\b', r'\bkidnap\b', r'\bexplode\b',
            r'\bweapon\b', r'\bgun\b', r'\bknife\b', r'\bpoison\b', r'\bassault\b',
            r'\bterror\b', r'\bviolence\b', r'\bhostage\b', r'\bexplosive\b',
            r'\bdetonate\b', r'\bassassinate\b', r'\bexecute\b', r'\bmaim\b',
            r'\btorture\b', r'\bterrorize\b', r'\bintimidate\b', r'\bbeat\b',
            r'\bstab\b', r'\bstrangle\b', r'\bsuffocate\b', r'\bpoison\b',
            r'\barson\b', r'\briot\b', r'\bgang\b', r'\bcartel\b', r'\bmafia\b'
        ]
        
        # Enhanced emotional distress indicators
        self.distress_indicators = [
            r'\bhelp\b', r'\bsave\b', r'\bdanger\b', r'\bemergency\b', r'\bpolice\b',
            r'\bambulance\b', r'\bhospital\b', r'\baccident\b', r'\binjury\b',
            r'\bpanic\b', r'\bscared\b', r'\bafraid\b', r'\bterrified\b', r'\bdesperate\b',
            r'\btrapped\b', r'\bstuck\b', r'\bchoking\b', r'\bbleeding\b', r'\bunconscious\b',
            r'\bheart\s*attack\b', r'\bstroke\b', r'\bseizure\b', r'\boverdose\b',
            r'\bsuicide\b', r'\bself\s*harm\b', r'\bcutting\b', r'\bhanging\b',
            r'\boverdose\b', r'\bpoisoning\b', r'\bdrowning\b', r'\bfire\b',
            r'\bexplosion\b', r'\bcrash\b', r'\bwreck\b', r'\bdisaster\b',
            r'\bcatastrophe\b', r'\bcrisis\b', r'\bbreakdown\b', r'\bmental\s*health\b'
        ]
        
        # Enhanced scam indicators
        self.scam_indicators = [
            r'\bprize\b', r'\bwinner\b', r'\blottery\b', r'\binheritance\b',
            r'\baccount\b', r'\bpassword\b', r'\bcredit\b', r'\bcard\b',
            r'\bsocial\s*security\b', r'\btax\b', r'\birs\b', r'\bgovernment\b',
            r'\bverify\b', r'\bconfirm\b', r'\bupdate\b', r'\bsecure\b',
            r'\bimmediate\b', r'\burgent\b', r'\bnow\b', r'\bquick\b', r'\bwire\b',
            r'\btransfer\b', r'\bpayment\b', r'\bpaypal\b', r'\bvenmo\b', r'\bcash\s*app\b',
            r'\bgift\s*card\b', r'\bprepaid\b', r'\bcryptocurrency\b', r'\bbitcoin\b',
            r'\bwallet\b', r'\bprivate\s*key\b', r'\bseed\s*phrase\b', r'\bbackup\b',
            r'\bverify\s*identity\b', r'\bconfirm\s*details\b', r'\bupdate\s*information\b',
            r'\bsecurity\s*breach\b', r'\bunauthorized\s*access\b', r'\bsuspicious\s*activity\b',
            r'\bnigerian\s*prince\b', r'\broyal\s*family\b', r'\bdiamond\b', r'\bgold\b',
            r'\boil\b', r'\bcontract\b', r'\bdeal\b', r'\boffer\b', r'\blimited\s*time\b',
            r'\bexclusive\b', r'\bsecret\b', r'\bconfidential\b', r'\bprivate\b',
            r'\bpersonal\s*information\b', r'\bbank\s*account\b', r'\brouting\s*number\b',
            r'\bssn\b', r'\bsocial\s*security\s*number\b', r'\bdriver\s*license\b',
            r'\bpassport\b', r'\bdate\s*of\s*birth\b', r'\bmother\s*maiden\s*name\b'
        ]

        self.text_threat_classifier = TextThreatClassifier()

    def _load_pretrained_models(self, model_path: str = None):
        """Load multiple pre-trained models for comprehensive analysis"""
        print("Loading pre-trained models...")
        
        try:
            # 1. Wav2Vec2 for audio feature extraction
            model_name = "facebook/wav2vec2-base"
            self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
            self.wav2vec_model = Wav2Vec2ForSequenceClassification.from_pretrained(
                model_name, num_labels=3
            )
            self.wav2vec_model.to(self.device)
            print("✓ Wav2Vec2 model loaded successfully")
        except Exception as e:
            print(f"⚠ Could not load Wav2Vec2 model: {e}")
            self.wav2vec_model = None

        try:
            # 2. Emotion classification model
            emotion_model = "harshit345/xlsr-wav2vec-speech-emotion-recognition"
            self.emotion_classifier = pipeline(
                "audio-classification",
                model=emotion_model,
                device=0 if torch.cuda.is_available() else -1
            )
            print("✓ Emotion classification model loaded successfully")
        except Exception as e:
            print(f"⚠ Could not load emotion model: {e}")
            self.emotion_classifier = None

        try:
            # 3. Speech recognition for transcription
            self.speech_recognizer = pipeline(
                "automatic-speech-recognition",
                model="facebook/wav2vec2-base-960h",
                device=0 if torch.cuda.is_available() else -1
            )
            print("✓ Speech recognition model loaded successfully")
        except Exception as e:
            print(f"⚠ Could not load speech recognition model: {e}")
            self.speech_recognizer = None

        try:
            # 4. Text toxicity classification
            self.toxicity_classifier = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                device=0 if torch.cuda.is_available() else -1
            )
            print("✓ Toxicity classification model loaded successfully")
        except Exception as e:
            print(f"⚠ Could not load toxicity model: {e}")
            self.toxicity_classifier = None

        try:
            # 5. Sentiment analysis
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if torch.cuda.is_available() else -1
            )
            print("✓ Sentiment analysis model loaded successfully")
        except Exception as e:
            print(f"⚠ Could not load sentiment model: {e}")
            self.sentiment_analyzer = None

        # Load or initialize Random Forest classifier
        if model_path and os.path.exists(f"{model_path}_rf.pkl"):
            try:
                self.rf_classifier = joblib.load(f"{model_path}_rf.pkl")
                self.scaler = joblib.load(f"{model_path}_scaler.pkl")
                print("✓ Random Forest model loaded successfully")
            except Exception as e:
                print(f"⚠ Could not load RF model: {e}")
                self._initialize_rf_classifier()
        else:
            self._initialize_rf_classifier()

    def _initialize_rf_classifier(self):
        self.rf_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        print("✓ Random Forest classifier initialized")
        # Train with dummy data to avoid the 'estimators_' attribute error
        try:
            dummy_features = np.random.rand(10, 60)  # 10 samples, 60 features (match real feature vector)
            dummy_labels = np.random.randint(0, 3, 10)  # 3 classes
            self.scaler.fit(dummy_features)  # Fit the scaler so it's always ready
            self.rf_classifier.fit(self.scaler.transform(dummy_features), dummy_labels)
            print("✓ Random Forest classifier trained with dummy data and scaler fitted (60 features)")
        except Exception as e:
            print(f"⚠ Random Forest training failed: {e}")

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio to text using pre-trained speech recognition"""
        try:
            if self.speech_recognizer:
                # Load audio
                audio, sr = librosa.load(audio_path, sr=16000)
                
                # Transcribe
                result = self.speech_recognizer(audio)
                transcription = result["text"]
                
                return transcription
            else:
                return ""
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

    def is_speech(self, audio_path: str) -> bool:
        """Detect if audio contains speech vs music/noise"""
        try:
            y, sr = librosa.load(audio_path, sr=16000)
            
            # 1. Check voice activity ratio
            frame_length = 2048
            hop_length = 512
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            threshold = 0.02 * np.max(rms)
            voiced_frames = rms > threshold
            voice_activity_ratio = np.mean(voiced_frames)
            
            # 2. Check spectral features typical of speech
            stft = librosa.stft(y)
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(S=np.abs(stft)))
            spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(S=np.abs(stft)))
            
            # 3. Check pitch characteristics (speech has specific pitch range)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = pitches[magnitudes > 0.1]
            
            if len(pitch_values) > 0:
                pitch_mean = np.mean(pitch_values)
                pitch_std = np.std(pitch_values)
            else:
                pitch_mean = 0
                pitch_std = 0
            
            # 4. Check MFCC features (speech has characteristic patterns)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_std = np.std(mfccs)
            
            # Speech detection criteria
            is_speech_audio = (
                voice_activity_ratio > 0.3 and  # Good voice activity
                spectral_centroid > 500 and spectral_centroid < 3000 and  # Speech frequency range
                spectral_bandwidth > 500 and spectral_bandwidth < 2000 and  # Speech bandwidth
                pitch_mean > 80 and pitch_mean < 400 and  # Human speech pitch range
                pitch_std > 20 and  # Some pitch variation
                mfcc_std > 0.5  # Characteristic speech patterns
            )
            
            print(f"DEBUG: Speech detection - Voice activity: {voice_activity_ratio:.3f}, "
                  f"Spectral centroid: {spectral_centroid:.1f}, "
                  f"Pitch mean: {pitch_mean:.1f}, "
                  f"MFCC std: {mfcc_std:.3f}, "
                  f"Is speech: {is_speech_audio}")
            
            return is_speech_audio
            
        except Exception as e:
            print(f"Speech detection error: {e}")
            return False

    def analyze_emotion(self, audio_path: str) -> Dict[str, float]:
        """Analyze emotion in audio using pre-trained emotion model"""
        try:
            if self.emotion_classifier:
                # First check if this is actually speech
                if not self.is_speech(audio_path):
                    print("DEBUG: Audio is not speech, returning neutral emotion")
                    return {"neutral": 1.0}
                
                # Load audio
                audio, sr = librosa.load(audio_path, sr=16000)
                
                # Analyze emotion
                results = self.emotion_classifier(audio)
                
                # Convert to dictionary
                emotion_scores = {}
                for result in results:
                    emotion_scores[result['label']] = result['score']
                
                return emotion_scores
            else:
                return {}
        except Exception as e:
            print(f"Emotion analysis error: {e}")
            return {}

    def analyze_text_toxicity(self, text: str) -> Dict[str, float]:
        """Analyze text toxicity using pre-trained toxicity model"""
        try:
            if self.toxicity_classifier and text.strip():
                # Analyze toxicity
                results = self.toxicity_classifier(text)
                
                # Convert to dictionary
                toxicity_scores = {}
                for result in results:
                    toxicity_scores[result['label']] = result['score']
                
                return toxicity_scores
            else:
                return {}
        except Exception as e:
            print(f"Toxicity analysis error: {e}")
            return {}

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using pre-trained sentiment model"""
        try:
            if self.sentiment_analyzer and text.strip():
                # Analyze sentiment
                results = self.sentiment_analyzer(text)
                
                # Convert to dictionary
                sentiment_scores = {}
                for result in results:
                    sentiment_scores[result['label']] = result['score']
                
                return sentiment_scores
            else:
                return {}
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return {}

    def extract_audio_features(self, audio_path: str) -> Dict[str, np.ndarray]:
        """Extract audio features for threat analysis"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Ensure audio is not too long
            if len(y) > self.sample_rate * self.max_length:
                y = y[:self.sample_rate * self.max_length]
            
            # Ensure audio is real-valued
            y = np.real(y)
            
            features = {}
            
            # 1. Basic audio features
            features['duration'] = len(y) / sr
            features['rms_energy'] = np.sqrt(np.mean(y**2))
            features['zero_crossing_rate'] = np.mean(librosa.feature.zero_crossing_rate(y))
            
            # 2. Spectral features with error handling
            try:
                stft = librosa.stft(y)
                # Ensure STFT is real-valued for spectral features
                stft_magnitude = np.abs(stft)
                
                features['spectral_centroid'] = np.mean(librosa.feature.spectral_centroid(S=stft_magnitude))
                features['spectral_bandwidth'] = np.mean(librosa.feature.spectral_bandwidth(S=stft_magnitude))
                features['spectral_rolloff'] = np.mean(librosa.feature.spectral_rolloff(S=stft_magnitude))
                features['spectral_contrast'] = np.mean(librosa.feature.spectral_contrast(S=stft_magnitude))
            except Exception as e:
                print(f"Spectral features error: {e}")
                features['spectral_centroid'] = 0.0
                features['spectral_bandwidth'] = 0.0
                features['spectral_rolloff'] = 0.0
                features['spectral_contrast'] = 0.0
            
            # 3. MFCC features
            try:
                mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
                features['mfcc_mean'] = np.mean(mfccs, axis=1)
                features['mfcc_std'] = np.std(mfccs, axis=1)
            except Exception as e:
                print(f"MFCC features error: {e}")
                features['mfcc_mean'] = np.zeros(13)
                features['mfcc_std'] = np.zeros(13)
            
            # 4. Pitch features with error handling
            try:
                pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
                pitch_values = pitches[magnitudes > 0.1]
                
                if len(pitch_values) > 0:
                    features['pitch_mean'] = np.mean(pitch_values)
                    features['pitch_std'] = np.std(pitch_values)
                else:
                    features['pitch_mean'] = 0.0
                    features['pitch_std'] = 0.0
            except Exception as e:
                print(f"Pitch features error: {e}")
                features['pitch_mean'] = 0.0
                features['pitch_std'] = 0.0
            
            # 5. Tempo and rhythm features
            try:
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                features['tempo'] = tempo
            except Exception as e:
                print(f"Tempo features error: {e}")
                features['tempo'] = 120.0  # Default tempo
            
            # 6. Harmonic and percussive features
            try:
                y_harmonic, y_percussive = librosa.effects.hpss(y)
                features['harmonic_ratio'] = np.sum(y_harmonic**2) / np.sum(y**2)
                features['percussive_ratio'] = np.sum(y_percussive**2) / np.sum(y**2)
            except Exception as e:
                print(f"Harmonic features error: {e}")
                features['harmonic_ratio'] = 0.5
                features['percussive_ratio'] = 0.5
            
            # 7. Voice activity detection (energy-based VAD)
            try:
                frame_length = 2048
                hop_length = 512
                rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
                threshold = 0.02 * np.max(rms)
                voiced_frames = rms > threshold
                features['voice_activity_ratio'] = np.mean(voiced_frames)
            except Exception as e:
                print(f"Voice activity error: {e}")
                features['voice_activity_ratio'] = 0.5
            
            # 8. Loudness features
            try:
                rms_features = librosa.feature.rms(y=y)
                features['loudness'] = np.mean(rms_features)
                features['loudness_std'] = np.std(rms_features)
            except Exception as e:
                print(f"Loudness features error: {e}")
                features['loudness'] = 0.0
                features['loudness_std'] = 0.0
            
            # 9. Jitter and shimmer (voice quality measures)
            features['jitter'] = self._calculate_jitter(y, sr)
            features['shimmer'] = self._calculate_shimmer(y, sr)
            
            # 10. Emotional features
            features['emotional_features'] = self._extract_emotional_features(y, sr)
            
            return features
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            # Return default features if extraction fails
            return self._get_default_features()

    def _get_default_features(self) -> Dict[str, np.ndarray]:
        """Return default features when extraction fails"""
        return {
            'duration': 0.0,
            'rms_energy': 0.0,
            'zero_crossing_rate': 0.0,
            'spectral_centroid': 0.0,
            'spectral_bandwidth': 0.0,
            'spectral_rolloff': 0.0,
            'spectral_contrast': 0.0,
            'mfcc_mean': np.zeros(13),
            'mfcc_std': np.zeros(13),
            'pitch_mean': 0.0,
            'pitch_std': 0.0,
            'tempo': 120.0,
            'harmonic_ratio': 0.5,
            'percussive_ratio': 0.5,
            'voice_activity_ratio': 0.5,
            'loudness': 0.0,
            'loudness_std': 0.0,
            'jitter': 0.0,
            'shimmer': 0.0,
            'emotional_features': np.zeros(13)
        }

    def _calculate_jitter(self, y: np.ndarray, sr: int) -> float:
        """Calculate jitter (frequency perturbation)"""
        try:
            # Extract pitch periods
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = pitches[magnitudes > 0.1]
            
            if len(pitch_values) < 2:
                return 0.0
            
            # Calculate jitter as relative average perturbation
            jitter = np.mean(np.abs(np.diff(pitch_values))) / np.mean(pitch_values)
            return jitter
        except:
            return 0.0

    def _calculate_shimmer(self, y: np.ndarray, sr: int) -> float:
        """Calculate shimmer (amplitude perturbation)"""
        try:
            # Extract amplitude envelope
            rms = librosa.feature.rms(y=y)
            rms_values = rms.flatten()
            
            if len(rms_values) < 2:
                return 0.0
            
            # Calculate shimmer as relative average perturbation
            shimmer = np.mean(np.abs(np.diff(rms_values))) / np.mean(rms_values)
            return shimmer
        except:
            return 0.0

    def _extract_emotional_features(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Extract features related to emotional expression"""
        try:
            # Spectral features for emotion detection
            stft = librosa.stft(y)
            
            # Spectral flux (sudden changes)
            spectral_flux = np.mean(librosa.onset.onset_strength(y=y, sr=sr))
            
            # Spectral flatness (noise vs harmonic content)
            spectral_flatness = np.mean(librosa.feature.spectral_flatness(S=stft))
            
            # Spectral rolloff (brightness)
            spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(S=stft))
            
            # Mel-frequency features
            mel_spec = librosa.feature.melspectrogram(y=y, sr=sr)
            mel_features = np.mean(mel_spec, axis=1)
            
            # Combine features
            emotional_features = np.concatenate([
                [spectral_flux, spectral_flatness, spectral_rolloff],
                mel_features[:10]  # First 10 mel bands
            ])
            
            return emotional_features
        except:
            return np.zeros(13)

    def analyze_voice_characteristics(self, audio_path: str) -> Dict[str, float]:
        """
        Analyze voice characteristics for threat detection
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with voice analysis results
        """
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            analysis = {}
            
            # 1. Speaking rate analysis
            analysis['speaking_rate'] = self._analyze_speaking_rate(y, sr)
            
            # 2. Volume analysis
            analysis['volume_variation'] = self._analyze_volume_variation(y)
            
            # 3. Pitch analysis
            analysis['pitch_variation'] = self._analyze_pitch_variation(y, sr)
            
            # 4. Stress indicators
            analysis['stress_indicators'] = self._analyze_stress_indicators(y, sr)
            
            # 5. Aggression indicators
            analysis['aggression_indicators'] = self._analyze_aggression_indicators(y, sr)
            
            return analysis
            
        except Exception as e:
            print(f"Error in voice analysis: {e}")
            return {}

    def _analyze_speaking_rate(self, y: np.ndarray, sr: int) -> float:
        """Analyze speaking rate (words per minute estimate)"""
        try:
            # Use onset detection to estimate speaking rate
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
            onset_times = librosa.frames_to_time(onset_frames, sr=sr)
            
            if len(onset_times) < 2:
                return 0.0
            
            # Estimate words per minute (rough approximation)
            duration = len(y) / sr
            word_estimate = len(onset_times) * 0.7  # Rough conversion
            wpm = (word_estimate / duration) * 60
            
            return wpm
        except:
            return 0.0

    def _analyze_volume_variation(self, y: np.ndarray) -> float:
        """Analyze volume variation (indicator of emotional state)"""
        try:
            rms = librosa.feature.rms(y=y)
            volume_std = np.std(rms)
            volume_mean = np.mean(rms)
            
            if volume_mean > 0:
                return volume_std / volume_mean
            return 0.0
        except:
            return 0.0

    def _analyze_pitch_variation(self, y: np.ndarray, sr: int) -> float:
        """Analyze pitch variation (indicator of emotional state)"""
        try:
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = pitches[magnitudes > 0.1]
            
            if len(pitch_values) < 2:
                return 0.0
            
            pitch_std = np.std(pitch_values)
            pitch_mean = np.mean(pitch_values)
            
            if pitch_mean > 0:
                return pitch_std / pitch_mean
            return 0.0
        except:
            return 0.0

    def _analyze_stress_indicators(self, y: np.ndarray, sr: int) -> float:
        """Analyze stress indicators in voice"""
        try:
            # Higher jitter and shimmer indicate stress
            jitter = self._calculate_jitter(y, sr)
            shimmer = self._calculate_shimmer(y, sr)
            
            # Spectral features for stress detection
            stft = librosa.stft(y)
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(S=stft))
            
            # Combine indicators
            stress_score = (jitter * 0.4 + shimmer * 0.4 + spectral_centroid * 0.2) / 1000
            return min(stress_score, 1.0)
        except:
            return 0.0

    def _analyze_aggression_indicators(self, y: np.ndarray, sr: int) -> float:
        """Analyze aggression indicators in voice"""
        try:
            # Loudness
            rms = librosa.feature.rms(y=y)
            loudness = np.mean(rms)
            
            # Spectral features
            stft = librosa.stft(y)
            spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(S=stft))
            
            # Tempo (faster speech can indicate aggression)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            
            # Combine indicators
            aggression_score = (loudness * 0.4 + spectral_bandwidth * 0.3 + tempo * 0.3) / 1000
            return min(aggression_score, 1.0)
        except:
            return 0.0

    def predict(self, audio_path: str, transcription: str = None, fast_mode: bool = False) -> Tuple[str, str, float]:
        """
        Predict threat level from audio file using multiple pre-trained models
        If fast_mode is True, only use classical features and Random Forest (skip deep models).
        """
        try:
            if not os.path.exists(audio_path):
                return "Safe", "✅", 0.5
            # Fast mode: only use classical features and Random Forest
            if fast_mode:
                features = self.extract_audio_features(audio_path)
                voice_analysis = self.analyze_voice_characteristics(audio_path)
                if features:
                    feature_vector = self._create_feature_vector(features, voice_analysis)
                    if self.rf_classifier:
                        try:
                            feature_vector_scaled = self.scaler.transform([feature_vector])
                            prediction = self.rf_classifier.predict(feature_vector_scaled)[0]
                            audio_score = np.max(self.rf_classifier.predict_proba(feature_vector_scaled))
                        except Exception as e:
                            print(f"RF prediction failed: {e}")
                            prediction, audio_score = self._rule_based_prediction(features, voice_analysis)
                    else:
                        prediction, audio_score = self._rule_based_prediction(features, voice_analysis)
                else:
                    prediction, audio_score = self._rule_based_prediction(features, voice_analysis)
                label, emoji = self._map_prediction_to_label(prediction)
                return label, emoji, audio_score
            # Full mode: use all models
            # Get transcription if not provided (only if speech recognizer is available)
            if not transcription and self.speech_recognizer:
                try:
                    transcription = self.transcribe_audio(audio_path)
                except Exception as e:
                    print(f"Transcription failed: {e}")
                    transcription = ""
            # --- Integrate improved text classifier ---
            text_label, text_emoji = "Safe", "✅"
            if transcription:
                try:
                    text_label, text_emoji = self.text_threat_classifier.predict(transcription)
                    text_scores = self.text_threat_classifier.predict_scores(transcription)
                except Exception as e:
                    print(f"TextThreatClassifier failed: {e}")
                    text_scores = {}
            else:
                text_scores = {}
            audio_score = 0.0
            text_score = 0.0
            emotion_score = 0.0
            toxicity_score = 0.0
            sentiment_score = 0.0
            try:
                features = self.extract_audio_features(audio_path)
                voice_analysis = self.analyze_voice_characteristics(audio_path)
                if features:
                    feature_vector = self._create_feature_vector(features, voice_analysis)
                    if self.rf_classifier:
                        try:
                            feature_vector_scaled = self.scaler.transform([feature_vector])
                            prediction = self.rf_classifier.predict(feature_vector_scaled)[0]
                            audio_score = np.max(self.rf_classifier.predict_proba(feature_vector_scaled))
                        except Exception as e:
                            print(f"RF prediction failed: {e}")
                            prediction, audio_score = self._rule_based_prediction(features, voice_analysis)
                    else:
                        prediction, audio_score = self._rule_based_prediction(features, voice_analysis)
            except Exception as e:
                print(f"Audio analysis failed: {e}")
                audio_score = 0.0
            if self.emotion_classifier:
                try:
                    emotion_scores = self.analyze_emotion(audio_path)
                    if emotion_scores:
                        negative_emotions = ['angry', 'fear', 'disgust', 'sad']
                        emotion_score = sum(emotion_scores.get(emotion, 0) for emotion in negative_emotions)
                except Exception as e:
                    print(f"Emotion analysis failed: {e}")
                    emotion_score = 0.0
            if transcription:
                keyword_score = self._analyze_transcription(transcription)
                text_score += keyword_score * 0.4
                if self.toxicity_classifier:
                    try:
                        toxicity_scores = self.analyze_text_toxicity(transcription)
                        if toxicity_scores:
                            toxicity_score = max(toxicity_scores.values())
                            text_score += toxicity_score * 0.3
                    except Exception as e:
                        print(f"Toxicity analysis failed: {e}")
                if self.sentiment_analyzer:
                    try:
                        sentiment_scores = self.analyze_sentiment(transcription)
                        if sentiment_scores:
                            negative_sentiment = sentiment_scores.get('negative', 0)
                            sentiment_score = negative_sentiment
                            text_score += sentiment_score * 0.3
                    except Exception as e:
                        print(f"Sentiment analysis failed: {e}")
            # Combine results: if text classifier says Threat/Offensive, override
            if text_label == "Threat":
                return "Threat", text_emoji, 1.0
            elif text_label == "Offensive":
                return "Offensive", text_emoji, 0.8
            # Otherwise, use the original logic
            final_score = (
                audio_score * 0.3 +
                text_score * 0.3 +
                emotion_score * 0.2 +
                toxicity_score * 0.1 +
                sentiment_score * 0.1
            )
            prediction = self._get_prediction_from_score(final_score)
            label, emoji = self._map_prediction_to_label(prediction)
            return label, emoji, final_score
        except Exception as e:
            print(f"Error in prediction: {e}")
            return "Safe", "✅", 0.5

    def _create_feature_vector(self, features: Dict, voice_analysis: Dict) -> np.ndarray:
        """Create a fixed-length 1D feature vector for the classifier"""
        feature_vector = []
        
        # Basic features
        feature_vector.extend([
            features.get('duration', 0),
            features.get('rms_energy', 0),
            features.get('zero_crossing_rate', 0),
            features.get('spectral_centroid', 0),
            features.get('spectral_bandwidth', 0),
            features.get('spectral_rolloff', 0),
            features.get('spectral_contrast', 0),
            features.get('harmonic_ratio', 0),
            features.get('percussive_ratio', 0),
            features.get('voice_activity_ratio', 0),
            features.get('loudness', 0),
            features.get('loudness_std', 0),
            features.get('jitter', 0),
            features.get('shimmer', 0)
        ])
        
        # MFCC features (pad/crop to 13)
        mfcc_mean = features.get('mfcc_mean', np.zeros(13))
        mfcc_std = features.get('mfcc_std', np.zeros(13))
        mfcc_mean = np.pad(mfcc_mean, (0, max(0, 13 - len(mfcc_mean))))[:13]
        mfcc_std = np.pad(mfcc_std, (0, max(0, 13 - len(mfcc_std))))[:13]
        feature_vector.extend(mfcc_mean)
        feature_vector.extend(mfcc_std)
        
        # Pitch features
        feature_vector.extend([
            features.get('pitch_mean', 0),
            features.get('pitch_std', 0)
        ])
        
        # Emotional features (pad/crop to 13)
        emotional_features = features.get('emotional_features', np.zeros(13))
        emotional_features = np.pad(emotional_features, (0, max(0, 13 - len(emotional_features))))[:13]
        feature_vector.extend(emotional_features)
        
        # Voice analysis features
        voice_keys = ['speaking_rate', 'volume_variation', 'pitch_variation', 'stress_indicators', 'aggression_indicators']
        for key in voice_keys:
            feature_vector.append(voice_analysis.get(key, 0))
        
        # Ensure output is a 1D numpy array of fixed length
        feature_vector = np.array(feature_vector, dtype=np.float32).flatten()
        return feature_vector

    def _rule_based_prediction(self, features: Dict, voice_analysis: Dict) -> Tuple[int, float]:
        """Rule-based prediction as fallback"""
        score = 0.0
        
        # High stress indicators
        if voice_analysis.get('stress_indicators', 0) > 0.7:
            score += 0.3
        
        # High aggression indicators
        if voice_analysis.get('aggression_indicators', 0) > 0.7:
            score += 0.4
        
        # High volume variation (emotional instability)
        if voice_analysis.get('volume_variation', 0) > 0.5:
            score += 0.2
        
        # High pitch variation (emotional state)
        if voice_analysis.get('pitch_variation', 0) > 0.5:
            score += 0.1
        
        # Determine prediction
        if score > 0.7:
            return 2, score  # Threat
        elif score > 0.4:
            return 1, score  # Offensive
        else:
            return 0, score  # Safe

    def _analyze_transcription(self, transcription: str) -> float:
        """Analyze transcription text for threat indicators"""
        if not transcription:
            return 0.0
        
        score = 0.0
        text_lower = transcription.lower()
        
        # Check threat keywords
        threat_count = sum(1 for pattern in self.threat_keywords 
                          if re.search(pattern, text_lower))
        if threat_count > 0:
            score += min(threat_count * 0.3, 0.6)
        
        # Check distress indicators
        distress_count = sum(1 for pattern in self.distress_indicators 
                           if re.search(pattern, text_lower))
        if distress_count > 0:
            score += min(distress_count * 0.2, 0.4)
        
        # Check scam indicators
        scam_count = sum(1 for pattern in self.scam_indicators 
                        if re.search(pattern, text_lower))
        if scam_count > 0:
            score += min(scam_count * 0.25, 0.5)
        
        return min(score, 1.0)

    def _get_prediction_from_score(self, score: float) -> int:
        """Convert score to prediction class"""
        if score > 0.7:
            return 2  # Threat
        elif score > 0.4:
            return 1  # Offensive
        else:
            return 0  # Safe

    def _map_prediction_to_label(self, prediction: int) -> Tuple[str, str]:
        """Map prediction to label and emoji"""
        if prediction == 0:
            return "Safe", "✅"
        elif prediction == 1:
            return "Offensive", "❗"
        else:
            return "Threat", "⚠"

    def save_model(self, model_path: str):
        """Save trained models"""
        try:
            if self.rf_classifier:
                joblib.dump(self.rf_classifier, f"{model_path}_rf.pkl")
                joblib.dump(self.scaler, f"{model_path}_scaler.pkl")
                print("✓ Models saved successfully")
        except Exception as e:
            print(f"Error saving models: {e}")

    def train(self, training_data: List[Tuple[str, int]]):
        """
        Train the model with labeled audio data
        
        Args:
            training_data: List of (audio_path, label) tuples
                          labels: 0=Safe, 1=Offensive, 2=Threat
        """
        try:
            print("Training voice threat classifier...")
            
            features_list = []
            labels = []
            
            for audio_path, label in training_data:
                # Extract features
                features = self.extract_audio_features(audio_path)
                voice_analysis = self.analyze_voice_characteristics(audio_path)
                
                if features:
                    feature_vector = self._create_feature_vector(features, voice_analysis)
                    features_list.append(feature_vector)
                    labels.append(label)
            
            if len(features_list) < 10:
                print("⚠ Insufficient training data")
                return
            
            # Convert to numpy arrays
            X = np.array(features_list)
            y = np.array(labels)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Random Forest
            self.rf_classifier.fit(X_scaled, y)
            
            # Evaluate model
            train_score = self.rf_classifier.score(X_scaled, y)
            print(f"✓ Training completed. Accuracy: {train_score:.3f}")
            
        except Exception as e:
            print(f"Error during training: {e}")

    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        info = {
            'model_type': 'Enhanced Voice Threat Classifier',
            'features': [
                'Audio duration', 'RMS energy', 'Zero crossing rate',
                'Spectral features', 'MFCC features', 'Pitch analysis',
                'Tempo analysis', 'Voice activity detection',
                'Jitter and shimmer', 'Emotional features',
                'Speaking rate', 'Volume variation', 'Stress indicators',
                'Aggression indicators', 'Pre-trained emotion detection',
                'Speech recognition', 'Toxicity analysis', 'Sentiment analysis'
            ],
            'classes': ['Safe', 'Offensive', 'Threat'],
            'sample_rate': self.sample_rate,
            'max_length': self.max_length,
            'device': str(self.device),
            'pretrained_models': []
        }
        # Add pre-trained model status
        if self.emotion_classifier:
            info['pretrained_models'].append('Emotion Classification')
        if self.speech_recognizer:
            info['pretrained_models'].append('Speech Recognition')
        if self.toxicity_classifier:
            info['pretrained_models'].append('Toxicity Detection')
        if self.sentiment_analyzer:
            info['pretrained_models'].append('Sentiment Analysis')
        if self.wav2vec_model:
            info['pretrained_models'].append('Wav2Vec2 Audio Features')
        # Add RandomForest info safely
        if self.rf_classifier:
            info['rf_n_estimators'] = getattr(self.rf_classifier, 'n_estimators', None)
            info['rf_max_depth'] = getattr(self.rf_classifier, 'max_depth', None)
            if hasattr(self.rf_classifier, 'estimators_'):
                info['rf_status'] = f"Fitted with {len(self.rf_classifier.estimators_)} trees"
            else:
                info['rf_status'] = "RandomForestClassifier (not fitted)"
        else:
            info['rf_status'] = "RandomForestClassifier (not initialized)"
        return info 

    def start_real_time_monitoring(self, audio_callback=None, alert_callback=None):
        """
        Start real-time voice monitoring with enhanced threat detection
        
        Args:
            audio_callback: Function to call with audio chunks
            alert_callback: Function to call when threats are detected
        """
        self.is_monitoring = True
        self.alert_queue = queue.Queue()
        
        def monitoring_worker():
            try:
                import sounddevice as sd
                import tempfile
                import wave
                
                chunk_duration = 3  # 3-second chunks for real-time analysis
                samplerate = 16000
                
                with sd.InputStream(samplerate=samplerate, channels=1, dtype=np.float32) as stream:
                    while self.is_monitoring:
                        # Record chunk
                        audio_chunk, _ = stream.read(int(samplerate * chunk_duration))
                        
                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                            with wave.open(tmp_file.name, 'wb') as wf:
                                wf.setnchannels(1)
                                wf.setsampwidth(2)
                                wf.setframerate(samplerate)
                                wf.writeframes((audio_chunk * 32767).astype(np.int16).tobytes())
                            
                            # Analyze chunk
                            try:
                                label, emoji, confidence = self.predict(tmp_file.name, fast_mode=True)
                                
                                # Check for threats
                                if label in ["Threat", "Offensive"] and confidence > 0.6:
                                    alert_data = {
                                        'type': 'voice_threat',
                                        'label': label,
                                        'confidence': confidence,
                                        'timestamp': time.time(),
                                        'audio_file': tmp_file.name,
                                        'emoji': emoji
                                    }
                                    
                                    # Add to alert queue
                                    self.alert_queue.put(alert_data)
                                    
                                    # Call alert callback if provided
                                    if alert_callback:
                                        alert_callback(alert_data)
                                
                                # Call audio callback if provided
                                if audio_callback:
                                    audio_callback(audio_chunk, label, confidence)
                                
                            except Exception as e:
                                print(f"Real-time analysis error: {e}")
                            
                            # Clean up temp file
                            try:
                                os.unlink(tmp_file.name)
                            except:
                                pass
                        
                        # Small delay to prevent excessive CPU usage
                        time.sleep(0.1)
                        
            except Exception as e:
                print(f"Real-time monitoring error: {e}")
                self.is_monitoring = False
        
        # Start monitoring in separate thread
        self.monitoring_thread = threading.Thread(target=monitoring_worker, daemon=True)
        self.monitoring_thread.start()
        
        return True

    def stop_real_time_monitoring(self):
        """Stop real-time voice monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        return True

    def get_alerts(self):
        """Get pending alerts from the monitoring queue"""
        alerts = []
        while not self.alert_queue.empty():
            try:
                alerts.append(self.alert_queue.get_nowait())
            except queue.Empty:
                break
        return alerts

    def analyze_voice_intensity(self, audio_path: str) -> Dict[str, float]:
        """
        Analyze voice intensity patterns for threat detection
        """
        try:
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Calculate RMS energy over time
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)    # 10ms hop
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            
            # Calculate intensity metrics
            intensity_mean = np.mean(rms)
            intensity_std = np.std(rms)
            intensity_max = np.max(rms)
            intensity_min = np.min(rms)
            intensity_range = intensity_max - intensity_min
            
            # Calculate sudden intensity changes (potential threats)
            intensity_diff = np.diff(rms)
            sudden_changes = np.sum(np.abs(intensity_diff) > np.std(intensity_diff) * 2)
            sudden_change_ratio = sudden_changes / len(intensity_diff)
            
            # Calculate voice activity ratio
            voice_activity = np.sum(rms > np.mean(rms) * 0.5) / len(rms)
            
            return {
                'intensity_mean': float(intensity_mean),
                'intensity_std': float(intensity_std),
                'intensity_max': float(intensity_max),
                'intensity_min': float(intensity_min),
                'intensity_range': float(intensity_range),
                'sudden_changes': float(sudden_change_ratio),
                'voice_activity': float(voice_activity),
                'threat_score': float(sudden_change_ratio * 0.4 + (1 - voice_activity) * 0.3 + (intensity_std / intensity_mean) * 0.3)
            }
        except Exception as e:
            print(f"Voice intensity analysis error: {e}")
            return {}

    def detect_voice_patterns(self, audio_path: str) -> Dict[str, float]:
        """
        Detect specific voice patterns associated with threats
        """
        try:
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Extract pitch
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = pitches[magnitudes > np.percentile(magnitudes, 85)]
            
            if len(pitch_values) == 0:
                return {'pattern_score': 0.0}
            
            # Analyze pitch patterns
            pitch_mean = np.mean(pitch_values)
            pitch_std = np.std(pitch_values)
            pitch_range = np.max(pitch_values) - np.min(pitch_values)
            
            # Detect aggressive patterns (high pitch variation, rapid changes)
            pitch_changes = np.diff(pitch_values)
            rapid_changes = np.sum(np.abs(pitch_changes) > np.std(pitch_changes) * 1.5)
            rapid_change_ratio = rapid_changes / len(pitch_changes) if len(pitch_changes) > 0 else 0
            
            # Detect monotone threats (low pitch variation)
            monotone_score = 1.0 - (pitch_std / pitch_mean) if pitch_mean > 0 else 0
            
            # Calculate pattern threat score
            pattern_score = (
                rapid_change_ratio * 0.4 +
                monotone_score * 0.3 +
                (pitch_range / pitch_mean) * 0.3 if pitch_mean > 0 else 0
            )
            
            return {
                'pitch_mean': float(pitch_mean),
                'pitch_std': float(pitch_std),
                'pitch_range': float(pitch_range),
                'rapid_changes': float(rapid_change_ratio),
                'monotone_score': float(monotone_score),
                'pattern_score': float(pattern_score)
            }
        except Exception as e:
            print(f"Voice pattern detection error: {e}")
            return {'pattern_score': 0.0} 