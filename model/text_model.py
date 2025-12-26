from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import re
import numpy as np

class TextThreatClassifier:
    def __init__(self, model_name="unitary/unbiased-toxic-roberta"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        # The model has 7 labels: toxic, severe_toxic, obscene, threat, insult, identity_hate, sexual_explicit
        self.label_names = [
            "toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate", "sexual_explicit"
        ]

    def predict(self, text):
        # Money keyword detection (custom business logic)
        money_keywords = [r"\$\d+", r"₹\d+", r"rs\.?\s*\d+", r"transfer", r"payment", r"account", r"bank"]
        for kw in money_keywords:
            if re.search(kw, text, re.IGNORECASE):
                return "Offensive", "❗"
        # Threat keyword detection (custom business logic)
        threat_keywords = [r"\bkill\b", r"\battack\b", r"\bbomb\b", r"\bshoot\b", r"\bdie\b", r"\bmurder\b", r"\bthreat\b", r"\bharm\b"]
        for kw in threat_keywords:
            if re.search(kw, text, re.IGNORECASE):
                return "Threat", "⚠"
        # Model prediction
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.sigmoid(outputs.logits).cpu().numpy()[0]
            # Map to threat level
            threat_score = probs[self.label_names.index("threat")]
            sexual_score = probs[self.label_names.index("sexual_explicit")]
            toxic_score = probs[self.label_names.index("toxic")]
            obscene_score = probs[self.label_names.index("obscene")]
            hate_score = probs[self.label_names.index("identity_hate")]
            severe_toxic_score = probs[self.label_names.index("severe_toxic")]
            insult_score = probs[self.label_names.index("insult")]
            # Decision logic
            if threat_score > 0.4 or sexual_score > 0.4 or hate_score > 0.4:
                return "Threat", "⚠"
            elif toxic_score > 0.4 or obscene_score > 0.4 or severe_toxic_score > 0.4 or insult_score > 0.4:
                return "Offensive", "❗"
            else:
                return "Safe", "✅"

    def predict_scores(self, text):
        """Return a dict of all label scores for advanced integration."""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.sigmoid(outputs.logits).cpu().numpy()[0]
        return dict(zip(self.label_names, probs.tolist()))

    def extract_threat_offensive_words(self, text, threshold=0.2):
        """
        Only analyze the whole line as a single unit for threat or offensive content.
        Return a list with at most one (line, label) tuple if the line is classified as threat or offensive.
        """
        # Only check the whole line
        line_scores = self.predict_scores(text)
        if line_scores.get("threat", 0) > threshold:
            return [(text, "Threat")]
        elif any(line_scores.get(lbl, 0) > threshold for lbl in ["toxic", "obscene", "severe_toxic", "insult", "identity_hate", "sexual_explicit"]):
            return [(text, "Offensive")]
        else:
            return []