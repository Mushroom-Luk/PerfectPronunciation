import streamlit as st

# Azure Speech Service Configuration
AZURE_SPEECH_KEY = st.secrets.get("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = st.secrets.get("AZURE_SPEECH_REGION", "")
POE_API_KEY = st.secrets.get("POE_API_KEY", "")

# Language Settings
LANGUAGE_CONFIG = {
    "Japanese": {"locale": "ja-JP", "icon": "🇯🇵"},
    "English": {"locale": "en-US", "icon": "🇺🇸"},
    "Mandarin": {"locale": "zh-CN", "icon": "🇨🇳"},
    "Cantonese": {"locale": "zh-HK", "icon": "🇭🇰"},
    "German": {"locale": "de-DE", "icon": "🇩🇪"},
    "French": {"code": "fr-FR","voice": "fr-FR-DeniseNeural","icon": "🇫🇷"}
}

# --- Audio Recording Configuration ---
MAX_RECORDING_DURATION = 60  # seconds for full text
MAX_CHUNK_RECORDING_DURATION = 20 # seconds for sentence chunks

# --- Application Configuration ---
PAGE_TITLE = "Pronunciation Practice"
PAGE_ICON = "🗣️"
LAYOUT = "centered"

# --- AI Parsing Configuration ---
POE_MODEL = "Grok-4-Fast-Non-Reasoning"

# Assessment Settings
GRADING_SYSTEM = "HundredMark"
GRANULARITY = "Phoneme"
ENABLE_MISCUE = True
ENABLE_PROSODY = True