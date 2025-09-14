import azure.cognitiveservices.speech as speechsdk
import json
import streamlit as st
from config import *


class JapanesePronunciationAssessment:
    def __init__(self):
        if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
            st.error("⚠️ Azure Speech Service credentials not configured!")
            st.info("Please add your Azure Speech Service key and region to Streamlit secrets.")
            st.stop()

        self.speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION
        )
        self.speech_config.speech_recognition_language = JAPANESE_LOCALE

    def assess_pronunciation(self, audio_file_path, reference_text):
        """Assess pronunciation using Azure Speech Service."""
        try:
            # Create audio config
            audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)

            # Create pronunciation assessment config
            pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text,
                grading_system=getattr(speechsdk.PronunciationAssessmentGradingSystem, GRADING_SYSTEM),
                granularity=getattr(speechsdk.PronunciationAssessmentGranularity, GRANULARITY),
                enable_miscue=ENABLE_MISCUE
            )

            # Enable prosody assessment if configured
            if ENABLE_PROSODY:
                pronunciation_config.enable_prosody_assessment()

            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )

            # Apply pronunciation assessment config
            pronunciation_config.apply_to(speech_recognizer)

            # Perform recognition
            result = speech_recognizer.recognize_once()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                # Get pronunciation assessment result
                pronunciation_result = speechsdk.PronunciationAssessmentResult(result)

                # Get detailed JSON result
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
                error_details = result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult,
                                                      "Unknown error")
                return {
                    'success': False,
                    'error': f"Speech recognition failed: {result.reason}",
                    'error_details': error_details
                }

        except Exception as e:
            return {
                'success': False,
                'error': f"Assessment error: {str(e)}"
            }

    def get_word_level_assessment(self, detailed_result):
        """Extract word-level assessment from detailed results."""
        try:
            words_assessment = []
            if 'NBest' in detailed_result and len(detailed_result['NBest']) > 0:
                nbest = detailed_result['NBest'][0]
                if 'Words' in nbest:
                    for word_info in nbest['Words']:
                        word_data = {
                            'word': word_info.get('Word', ''),
                            'accuracy_score': word_info.get('PronunciationAssessment', {}).get('AccuracyScore', 0),
                            'error_type': word_info.get('PronunciationAssessment', {}).get('ErrorType', 'None'),
                            'phonemes': []
                        }

                        # Get phoneme-level details if available
                        if 'Phonemes' in word_info:
                            for phoneme in word_info['Phonemes']:
                                phoneme_data = {
                                    'phoneme': phoneme.get('Phoneme', ''),
                                    'accuracy_score': phoneme.get('PronunciationAssessment', {}).get('AccuracyScore', 0)
                                }
                                word_data['phonemes'].append(phoneme_data)

                        words_assessment.append(word_data)

            return words_assessment
        except Exception as e:
            st.warning(f"Could not extract word-level assessment: {str(e)}")
            return []