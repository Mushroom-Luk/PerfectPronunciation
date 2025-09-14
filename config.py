import os
import streamlit as st

# Azure Speech Service Configuration
AZURE_SPEECH_KEY = st.secrets.get("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = st.secrets.get("AZURE_SPEECH_REGION", "")

# Japanese Language Settings
JAPANESE_LOCALE = "ja-JP"
REFERENCE_LANGUAGE = "ja-JP"

# Audio Settings
SAMPLE_RATE = 16000
CHANNELS = 1
AUDIO_FORMAT = "wav"

# Assessment Settings
GRADING_SYSTEM = "HundredMark"  # or "FivePoint"
GRANULARITY = "Phoneme"  # "Phoneme", "Word", "FullText"
ENABLE_MISCUE = True
ENABLE_PROSODY = True

# UI Configuration
PAGE_TITLE = "Japanese Pronunciation Assessment"
PAGE_ICON = "🎌"
LAYOUT = "wide"