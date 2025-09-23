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
    "German": {"locale": "de-DE", "icon": "🇩🇪"}
}

# Audio Settings
SAMPLE_RATE = 16000
MAX_RECORDING_DURATION = 60  # 1 minute

# Assessment Settings
GRADING_SYSTEM = "HundredMark"
GRANULARITY = "Phoneme"
ENABLE_MISCUE = True
ENABLE_PROSODY = True

# UI Configuration
PAGE_TITLE = "Multilingual Pronunciation Assessment"
PAGE_ICON = "🗣️"
LAYOUT = "centered"