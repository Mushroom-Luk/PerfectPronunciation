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
                    'success': True, 'recognized_text': result.text,
                    'accuracy_score': pronunciation_result.accuracy_score,
                    'fluency_score': pronunciation_result.fluency_score,
                    'completeness_score': pronunciation_result.completeness_score,
                    'pronunciation_score': pronunciation_result.pronunciation_score,
                    'detailed_result': detailed_result
                }
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                error_message = f"Recognition Canceled: {cancellation_details.reason}. "
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    error_message += f"Error Details: {cancellation_details.error_details}"
                return {'success': False, 'error': error_message}
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
                        if 'Phonemes' in word_info:
                            for phoneme in word_info['Phonemes']:
                                phonemes.append({
                                    'phoneme': phoneme.get('Phoneme', ''),
                                    'accuracy_score': phoneme.get('PronunciationAssessment', {}).get('AccuracyScore', 0)
                                })
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


@st.cache_data(ttl=300)
def parse_text_with_poe(raw_text, display_lang, speak_lang):
    """Parses multi-language text into sentence pairs using POE API."""
    if not POE_API_KEY:
        st.error("POE API Key not configured in Streamlit secrets.")
        return None

    client = openai.OpenAI(api_key=POE_API_KEY, base_url="https://api.poe.com/v1")
    prompt = f"""
You are a text processing expert. Your task is to take a block of text containing two languages, identify the corresponding sentences or phrases, and format them into a JSON array.

The user has provided the text below.
Display Language: {display_lang}
Speak Language: {speak_lang}

---
{raw_text}
---

Rules:
1. Parse the input text and identify pairs of corresponding sentences or phrases between the two languages.
2. The output MUST be a valid JSON array of objects.
3. Each object in the array should have two keys: "display" and "speak".
4. The value of the "display" key should be a phrase from the {display_lang} text.
5. The value of the "speak" key should be the corresponding phrase from the {speak_lang} text.
6. Keep the phrases relatively short, suitable for a 10-15 second voice recording. Break down longer sentences if necessary.
7. Ensure the order of the phrases in the JSON array matches the order in the original text.
8. Do not include any explanations, markdown formatting like ```json, or any text outside of the JSON array in your response. Your entire response must be only the JSON content.

Example output format:
[
  {{"display": "Phrase 1 in display language", "speak": "Phrase 1 in speak language"}},
  {{"display": "Phrase 2 in display language", "speak": "Phrase 2 in speak language"}}
]
"""
    try:
        with st.spinner("🤖 Asking AI to parse text..."):
            chat = client.chat.completions.create(
                model=POE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            response_text = chat.choices[0].message.content
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                st.error("AI parsing failed: Could not find a JSON array in the response.")
                st.code(response_text)
                return None

            parsed_json = json.loads(json_match.group(0))

            if not isinstance(parsed_json, list) or not all(
                    isinstance(item, dict) and 'display' in item and 'speak' in item for item in parsed_json):
                st.error("AI parsing failed: The returned JSON has an incorrect structure.")
                st.code(parsed_json)
                return None
            return parsed_json
    except json.JSONDecodeError:
        st.error("AI parsing failed: The response was not valid JSON.")
        st.code(response_text)
        return None
    except Exception as e:
        st.error(f"An error occurred while calling the POE API: {e}")
        return None


@st.cache_data(ttl=300)
def generate_speech_audio(text, language):
    """Generate speech using POE API and return audio URL"""
    if not POE_API_KEY: return None
    try:
        headers = {"Authorization": f"Bearer {POE_API_KEY}", "Content-Type": "application/json"}
        data = {"model": "ElevenLabs-v3", "messages": [{"role": "user", "content": text.strip()}], "stream": False}
        response = requests.post("https://api.poe.com/v1/chat/completions", headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        message = result.get('choices', [{}])[0].get('message', {})
        if 'attachments' in message:
            for attachment in message['attachments']:
                if attachment.get('content_type', '').startswith('audio/'):
                    return attachment.get('url')
        content = message.get('content', '')
        url_match = re.search(r'https?://[^\s]+', content)
        if url_match: return url_match.group(0)
        return None
    except Exception as e:
        st.error(f"Speech generation error: {str(e)}")
        return None