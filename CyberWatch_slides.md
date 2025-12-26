# Cyber Watch — Emotion-aware Threat Detection

---

## Slide 1 — Title

**Cyber Watch — Emotion-aware Threat Detection**

- Multimodal detection (Text | Face | Voice)
- Prototype demo: webcam + microphone + files

**Speaker notes:**
Introduce the project and demo goal: a prototype detecting threats in text, voice, and facial expressions to augment security monitoring.

---

## Slide 2 — Problem Statement

- Multimodal threats: phishing messages, aggressive voice calls, suspicious video behavior
- Current tools miss emotional/contextual cues
- Human moderators face high-volume multimedia streams

**Speaker notes:**
Give examples and emphasize the need to fuse signals (text, voice, face) to improve detection and prioritization.

---

## Slide 3 — Objectives

- Modular prototype analyzing text, voice, and facial emotion
- Usable GUI for analysts with logging
- Lightweight fallbacks + support for heavy models
- Real-time monitoring and alerting

**Speaker notes:**
Clarify modularity and practical constraints (optional heavy model downloads).

---

## Slide 4 — Methodology

- Text: RoBERTa + heuristics
- Voice: MFCC/spectral features + transformer ASR/emotion (fallback: RandomForest)
- Face: YOLO / DeepFace / Haar cascade fallbacks
- UI: Tkinter dashboard with analyzers and live monitoring

**Speaker notes:**
Explain cascaded/fallback approach and voice pipeline.

---

## Slide 5 — System Design (Architecture)

- Frontend: main UI and modular GUIs
- Models: model/voice_model.py, model/text_model.py
- Utilities: file utils, DB history
- Optional models directory for heavy weights

**Speaker notes:**
Walk through data flow: input -> features -> models -> alert/log.

---

## Slide 6 — Implementation Highlights

- Robust GUI with theme, tooltips, back navigation
- VoiceThreatClassifier: transformer pipelines or RandomForest fallback
- FacialEmotionAnalyzer: YOLO/DeepFace/Haar cascades
- Text classifier + Gmail scanner integration (optional)

**Speaker notes:**
Point to key files and defensive imports.

---

## Slide 7 — Demo & Results

- Demo steps:
  1. Open app → voice legacy UI embedding
  2. Upload a sample audio file → show analysis
  3. Start webcam face analyzer → show detection overlay
  4. Trigger a threat popup (text analyzer)
- Results: file-based voice/text tests passed; live webcam validated locally; alerts: popup + beep + log

**Speaker notes:**
Outline demo flow and limitations (model downloads, audio devices).

---

## Slide 8 — Conclusion & Next Steps

- Prototype shows multimodal detection and real-time alerts
- Next: CI, packaged demo weights, labeled dataset & evaluation
- UX polish and dockerized deployment

**Speaker notes:**
Summarize wins and next work items; ask for sample data or resources for large-model demos.

---

## Appendix / Backup

- Environment & setup:

```powershell
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

- Files to capture for slides: `main.py`, `gui/voice_gui.py`, `model/voice_model.py`, `facial_emotion_analyzer.py`, `simple_camera_test.py`

- Known limitations & mitigations: optional dependency downloads, fallback logic included, test scripts available.
