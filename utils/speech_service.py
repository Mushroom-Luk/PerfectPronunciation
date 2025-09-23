import azure.cognitiveservices.speech as speechsdk
import json
import streamlit as st
import openai
import requests
import re
from config import *
from utils.language_utils import fill_japanese_phonemes


class PronunciationAssessment:
    def __init__(self, language="Japanese"):
        if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
            st.error("⚠️ Azure Speech Service not configured!")
            st.stop()

        self.language = language
        self.locale = LANGUAGE_CONFIG[language]["locale"]

        self.speech_config = speechsdk.SpeechConfig(AZURE_SPEECH_KEY, AZURE_SPEECH_REGION)
        self.speech_config.speech_recognition_language = self.locale

    def assess_pronunciation(self, audio_file_path, reference_text):
        try:
            audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)

            pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text,
                grading_system=getattr(speechsdk.PronunciationAssessmentGradingSystem, GRADING_SYSTEM),
                granularity=getattr(speechsdk.PronunciationAssessmentGranularity, GRANULARITY),
                enable_miscue=ENABLE_MISCUE
            )

            if ENABLE_PROSODY:
                pronunciation_config.enable_prosody_assessment()

            speech_recognizer = speechsdk.SpeechRecognizer(self.speech_config, audio_config)
            pronunciation_config.apply_to(speech_recognizer)

            result = speech_recognizer.recognize_once()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
                json_result = result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
                detailed_result = json.loads(json_result) if json_result else {}

                return {
                    'success': True,
                    'recognized_text': result.text,
                    'accuracy_score': pronunciation_result.accuracy_score,
                    'fluency_score': pronunciation_result.fluency_score,
                    'completeness_score': pronunciation_result.completeness_score,
                    'pronunciation_score': pronunciation_result.pronunciation_score,
                    'detailed_result': detailed_result
                }
            else:
                return {'success': False, 'error': f"Recognition failed: {result.reason}"}

        except Exception as e:
            return {'success': False, 'error': f"Assessment error: {str(e)}"}

    def get_word_level_assessment(self, detailed_result):
        words_assessment = []
        try:
            if 'NBest' in detailed_result and detailed_result['NBest']:
                nbest = detailed_result['NBest'][0]
                if 'Words' in nbest:
                    for word_info in nbest['Words']:
                        word = word_info.get('Word', '')
                        phonemes = []

                        # Get phonemes from Azure
                        if 'Phonemes' in word_info:
                            for phoneme in word_info['Phonemes']:
                                phonemes.append({
                                    'phoneme': phoneme.get('Phoneme', ''),
                                    'accuracy_score': phoneme.get('PronunciationAssessment', {}).get('AccuracyScore', 0)
                                })

                        # Fill empty Japanese phonemes
                        if self.language == "Japanese" and (not phonemes or all(p['phoneme'] == '' for p in phonemes)):
                            japanese_phonemes = fill_japanese_phonemes(word)
                            phonemes = [{'phoneme': p, 'accuracy_score': 85} for p in japanese_phonemes]

                        words_assessment.append({
                            'word': word,
                            'accuracy_score': word_info.get('PronunciationAssessment', {}).get('AccuracyScore', 0),
                            'error_type': word_info.get('PronunciationAssessment', {}).get('ErrorType', 'None'),
                            'phonemes': phonemes
                        })
        except Exception as e:
            st.warning(f"Could not extract word assessment: {str(e)}")

        return words_assessment


@st.cache_data(ttl=300)  # Cache for 5 minutes
def generate_speech_audio(text, language):
    """Generate speech using POE API and return audio URL"""
    if not POE_API_KEY:
        return None

    try:
        # Language-specific voice selection
        voice_config = {
            "Japanese": " --language ja",
            "English": "",
            "Mandarin": " --language zh --voice James Gao",
            "Cantonese": " --language zh --voice River",
            "German": " --language de"
        }

        prompt = text # + voice_config.get(language, "")

        headers = {
            "Authorization": f"Bearer {POE_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "ElevenLabs-v3",
            "messages": [{"role": "user", "content": prompt.strip()}],
            "stream": False
        }

        response = requests.post(
            "https://api.poe.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        response.raise_for_status()
        result = response.json()
        message = result.get('choices', [{}])[0].get('message', {})

        # Check for attachments first
        if 'attachments' in message:
            for attachment in message['attachments']:
                if attachment.get('content_type', '').startswith('audio/'):
                    return attachment.get('url')

        # Fallback: search for URL in content
        content = message.get('content', '')
        url_match = re.search(r'https?://[^\s]+', content)
        if url_match:
            return url_match.group(0)

        return None

    except Exception as e:
        st.error(f"Speech generation error: {str(e)}")
        return None