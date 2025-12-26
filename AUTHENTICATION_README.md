# 🔐 Cyber Watch Authentication System

## Overview

The Cyber Watch application now includes a comprehensive authentication system that provides secure access to all analysis modules (Text, Voice, and Face). Users can sign up and sign in using traditional credentials or OAuth providers (Google, GitHub).

## 🚀 Quick Start

### Starting the Application

To start the application with authentication:

```bash
python launcher.py
```

This will open the authentication window where users can sign in or create an account.

### Alternative Start Methods

- **Direct to main app (no auth)**: `python main.py`
- **Voice analyzer only**: `python app.py`
- **Test authentication**: `python test_auth_system.py`

## 🔧 Features

### Authentication Methods

1. **Traditional Sign Up/Sign In**
   - Username/Email and password
   - Secure password validation
   - Session management

2. **OAuth Providers**
   - Google Sign In/Sign Up
   - GitHub Sign In/Sign Up
   - Automatic account creation for new users

### Module Navigation

After successful authentication, users are redirected to a module selection screen with three options:

1. **📝 Text Analyzer** - Analyze text, files, and chats for threats
2. **🎤 Voice Analyzer** - Analyze voice for threats and emotions
3. **😊 Face Analyzer** - Detect facial emotions and threats

## 📁 File Structure

```
├── auth_gui.py              # Authentication GUI
├── launcher.py              # Main launcher with auth
├── main.py                  # Main application (updated with auth integration)
├── app.py                   # Voice analyzer (standalone)
├── auth/
│   ├── auth_manager.py      # Authentication logic
│   ├── oauth_config.json    # OAuth configuration
│   └── __init__.py
├── database/
│   └── database.py          # Database operations
├── model/
│   └── voice_model.py       # Voice analysis models
├── gui/
│   └── voice_gui.py         # Voice analyzer GUI
└── facial_emotion_analyzer.py # Face analysis
```

## 🎯 User Flow

### 1. Authentication Flow

```
User opens launcher.py
    ↓
Authentication Window
    ↓
[Sign In] or [Sign Up]
    ↓
[Traditional] or [OAuth]
    ↓
Module Selection Screen
    ↓
[Text] [Voice] [Face]
    ↓
Selected Module Opens
```

### 2. Module Access

- **Text Analyzer**: Full text analysis with Gmail integration
- **Voice Analyzer**: Comprehensive voice analysis with 4 tabs:
  - 💬 Voice Chat Monitor
  - 📞 Voice Call Scanner  
  - 📁 Voice File Scanner
  - 🎙️ Live Mic Monitor
- **Face Analyzer**: Real-time facial emotion detection

### 3. Navigation

- **Back to Auth**: Users can return to authentication from any module
- **Logout**: Secure session termination
- **Module Switching**: Easy navigation between modules

## 🔒 Security Features

### Password Security
- Minimum 6 characters required
- Secure hashing and salting
- Session token management

### OAuth Security
- Secure OAuth 2.0 flow
- Token validation
- Automatic session creation

### Session Management
- Secure session tokens
- Automatic session validation
- Proper logout functionality

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

### Database Configuration

The system uses SQLite by default. Database file: `cyberwatch.db`

## 🎨 UI Features

### Modern Design
- Dark theme with accent colors
- Responsive layout
- Professional styling
- Intuitive navigation

### User Experience
- Clear error messages
- Loading indicators
- Status updates
- Tooltips for guidance

## 🧪 Testing

### Run Tests

```bash
# Test authentication system
python test_auth_system.py

# Test voice module
python test_voice_module.py

# Test facial module
python test_facial_emotion.py
```

### Test Scenarios

1. **User Registration**: Create new accounts
2. **User Authentication**: Sign in with credentials
3. **OAuth Flow**: Test Google/GitHub integration
4. **Module Access**: Verify module redirection
5. **Session Management**: Test logout and session validation

## 🚨 Troubleshooting

### Common Issues

1. **OAuth Not Working**
   - Check OAuth configuration
   - Verify client IDs and secrets
   - Ensure redirect URIs match

2. **Database Errors**
   - Check file permissions
   - Verify database file exists
   - Run database tests

3. **Module Loading Issues**
   - Check Python dependencies
   - Verify model files
   - Run module-specific tests

### Error Messages

- **"Authentication failed"**: Check credentials or OAuth setup
- **"Module not available"**: Missing dependencies or model files
- **"Database error"**: File permission or corruption issues

## 📊 Voice Module Features

### Enhanced Voice Analysis

The voice analyzer includes:

1. **Pre-trained Models**
   - Wav2Vec2 for audio processing
   - Emotion classification
   - Speech recognition
   - Toxicity detection
   - Sentiment analysis

2. **Analysis Modes**
   - **Voice Chat Monitor**: Short voice clips (WhatsApp, Telegram)
   - **Voice Call Scanner**: Recorded call files (MP3/WAV)
   - **Voice File Scanner**: Upload and analyze audio files
   - **Live Mic Monitor**: Real-time threat detection

3. **Features**
   - Fast mode for quick analysis
   - Comprehensive feature extraction
   - Real-time monitoring
   - Audio transcription
   - Emotion detection
   - Threat classification

## 🔄 Updates and Maintenance

### Recent Updates

1. **Authentication System**: Complete sign-in/sign-up functionality
2. **Module Integration**: Seamless navigation between modules
3. **Voice Enhancement**: Pre-trained models and comprehensive analysis
4. **UI Improvements**: Modern design and better user experience

### Future Enhancements

1. **Additional OAuth Providers**: Microsoft, Facebook
2. **Advanced Security**: 2FA, password policies
3. **User Profiles**: Personalization and settings
4. **Analytics**: Usage tracking and reports

## 📞 Support

For issues or questions:

1. Run the test scripts to identify problems
2. Check the troubleshooting section
3. Verify all dependencies are installed
4. Ensure proper configuration

## 🎉 Getting Started

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Configure OAuth** (optional): Update `auth/oauth_config.json`
3. **Start Application**: `python launcher.py`
4. **Create Account**: Sign up or use OAuth
5. **Choose Module**: Select Text, Voice, or Face analyzer
6. **Start Analyzing**: Use the comprehensive analysis tools

---

**Cyber Watch** - Emotion-Aware Cybersecurity with Advanced Authentication 