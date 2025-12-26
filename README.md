# 🛡️ Cyber Watch - Emotion-Aware Cybersecurity

A comprehensive cybersecurity application that combines text, voice, and facial analysis for threat detection using advanced AI models.

## 🚀 Quick Start

### Start the whole app (single entry)

```bash
python start.py
```

### Direct Access (No Authentication)

```bash
python main.py
```

### Voice Analyzer Only

```bash
python app.py
```

## 📁 Project Structure

### Core Application Files

```
├── launcher.py                    # Main launcher with authentication
├── main.py                        # Main application (text, voice, face)
├── app.py                         # Voice analyzer (standalone)
├── auth_gui.py                    # Authentication system
├── facial_emotion_analyzer.py     # Facial emotion detection
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── AUTHENTICATION_README.md       # Detailed auth documentation
```

### Essential Directories

```
├── auth/                          # Authentication system
│   ├── auth_manager.py           # OAuth and user management
│   └── oauth_config.json         # OAuth configuration
├── database/                      # Database operations
│   └── database.py               # User and session management
├── model/                         # AI models
│   └── voice_model.py            # Voice analysis models
├── gui/                          # GUI components
│   └── voice_gui.py              # Voice analyzer interface
├── utils/                        # Utility functions
├── sounds/                       # Audio files
└── models/                       # Model files
```

## 🎯 Features

### 🔐 Authentication System

- **Traditional Sign Up/Sign In**: Username/email and password
- **OAuth Integration**: Google and GitHub login
- **Session Management**: Secure token-based sessions
- **Module Redirection**: Automatic navigation to selected modules

### 📝 Text Analyzer

- **Text Threat Detection**: Analyze text for threats and offensive content
- **File Scanner**: Scan documents and files for threats
- **Gmail Integration**: Scan Gmail messages for threats
- **Chat Monitor**: Real-time chat message analysis
- **Money Detection**: Identify financial scam patterns

### 🎤 Voice Analyzer

- **Voice Chat Monitor**: Analyze short voice clips (WhatsApp, Telegram)
- **Voice Call Scanner**: Scan recorded call files (MP3/WAV)
- **Voice File Scanner**: Upload and analyze audio files
- **Live Mic Monitor**: Real-time threat detection from microphone
- **Pre-trained Models**: Wav2Vec2, Emotion, Speech, Toxicity detection
- **Audio Transcription**: Convert speech to text for analysis
- **Fast Mode**: Quick analysis option

### 😊 Face Analyzer

- **Real-time Emotion Detection**: Detect facial emotions using webcam
- **Threat Assessment**: Analyze facial expressions for threat indicators
- **Multiple Models**: ResNet50, Vision Transformer, ResNet18 fallback
- **Live Video Feed**: Real-time analysis with visual feedback

## 🔧 Installation

### Prerequisites

- Python 3.8+
- Webcam (for face analyzer)
- Microphone (for voice analyzer)

### Setup

1. **Clone the repository**
2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure OAuth** (optional):
   - Update `auth/oauth_config.json` with your OAuth credentials
4. **Start the application**:

   ```bash
   python launcher.py
   ```

## 🎮 Usage

### 1. Authentication Flow

```
Launch → Sign In/Sign Up → Choose Module → Start Analysis
```

### 2. Module Selection

After authentication, choose from:
- **📝 Text Analyzer**: Text, files, Gmail, chat monitoring
- **🎤 Voice Analyzer**: 4 comprehensive voice analysis modes
- **😊 Face Analyzer**: Real-time facial emotion detection

### 3. Analysis Features

#### Text Analysis

- Enter text directly or upload files
- Gmail integration for email scanning
- Chat monitoring for real-time analysis
- Threat classification (Safe/Offensive/Threat)

#### Voice Analysis

- **Chat Monitor**: Record 10-second voice clips
- **Call Scanner**: Upload recorded call files
- **File Scanner**: Analyze any audio file with fast mode option
- **Live Monitor**: Real-time microphone monitoring
- Comprehensive threat and emotion detection

#### Face Analysis

- Real-time webcam feed
- Emotion detection (Happy, Sad, Angry, Neutral, Surprise)
- Threat assessment based on facial expressions
- Visual feedback with analysis results

## 🔒 Security Features

### Authentication Security

- Secure password hashing
- OAuth 2.0 integration
- Session token management
- Automatic logout functionality

### Analysis Security

- Local processing (no data sent to external servers)
- Secure file handling
- Privacy-focused design
- No data retention

## 🎨 User Interface

### Modern Design

- Dark theme with accent colors
- Professional styling
- Intuitive navigation
- Responsive layout

### User Experience

- Clear error messages
- Loading indicators
- Status updates
- Tooltips for guidance

## 🛠️ Configuration

### OAuth Setup

To enable OAuth providers, update `auth/oauth_config.json`:

```json
{
  "google": {
    "client_id": "YOUR_GOOGLE_CLIENT_ID",
    "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
    "redirect_uri": "http://localhost:8080/oauth/callback"
  },
  "github": {
    "client_id": "YOUR_GITHUB_CLIENT_ID",
    "client_secret": "YOUR_GITHUB_CLIENT_SECRET",
    "redirect_uri": "http://localhost:8080/oauth/callback"
  }
}
```

### Database

- SQLite database (`cyberwatch.db`)
- Automatic user and session management
- No manual configuration required

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Problems**
   - Check OAuth configuration
   - Verify database permissions
   - Ensure all dependencies are installed

2. **Voice Analysis Issues**
   - Check microphone permissions
   - Verify audio file formats (WAV, MP3, M4A)
   - Ensure PyAudio is properly installed

3. **Face Analysis Issues**
   - Check webcam permissions
   - Verify OpenCV installation
   - Ensure webcam is not in use by other applications

4. **Model Loading Issues**
   - Check internet connection for model downloads
   - Verify sufficient disk space
   - Ensure all dependencies are installed

### Error Messages

- **"Module not available"**: Missing dependencies
- **"Authentication failed"**: Check credentials or OAuth setup
- **"Device not accessible"**: Check permissions for camera/microphone

## 📊 Technical Details

### AI Models Used

- **Text Analysis**: Custom threat classification models
- **Voice Analysis**: Wav2Vec2, Emotion classification, Speech recognition
- **Face Analysis**: ResNet50, Vision Transformer, ResNet18

### Performance

- **Text Analysis**: Real-time processing
- **Voice Analysis**: 5-30 seconds depending on file size
- **Face Analysis**: Real-time with 30 FPS capability

### System Requirements

- **CPU**: Multi-core processor recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space for models
- **OS**: Windows 10+, macOS 10.14+, Linux

## 🔄 Updates

### Recent Features

- Complete authentication system
- Enhanced voice analysis with pre-trained models
- Real-time face emotion detection
- Modern UI/UX improvements
- Comprehensive threat detection

### Future Enhancements

- Additional OAuth providers
- Advanced security features (2FA)
- User profiles and settings
- Analytics and reporting
- Mobile application

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Verify all dependencies are installed
3. Ensure proper configuration
4. Check file permissions

## 📄 License

This project is for educational and research purposes.

---

**Cyber Watch** - Emotion-Aware Cybersecurity with Advanced AI Analysis
