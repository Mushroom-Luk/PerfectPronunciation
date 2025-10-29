import sys
import os
import streamlit as st

# --- Path Correction ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ---------------------

from audiorecorder import audiorecorder
from utils.speech_service import PronunciationAssessment, generate_speech_audio, parse_text_with_poe
from utils.audio_utils import convert_audio_format, save_audio_to_temp_file, cleanup_temp_file, get_audio_duration
from utils.language_utils import get_sample_texts, get_romanization_with_words, get_pronunciation_tips, \
    split_text_into_sentences, get_translation_placeholder_text
from config import *

# --- Page and CSS Configuration ---
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout=LAYOUT)

st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem;
        border-left: 5px solid; margin: 0.1rem; text-align: center;
        height: 100%; display: flex; flex-direction: column; justify-content: center;
    }
    .success-card { border-left-color: #28a745; }
    .warning-card { border-left-color: #ffc107; }
    .error-card { border-left-color: #dc3545; }
    .word-correct { background-color: #d4edda; color: #155724; padding: 3px 8px; margin: 2px; border-radius: 4px; display: inline-block; }
    .word-partial { background-color: #fff3cd; color: #856404; padding: 3px 8px; margin: 2px; border-radius: 4px; display: inline-block; }
    .word-incorrect { background-color: #f8d7da; color: #721c24; padding: 3px 8px; margin: 2px; border-radius: 4px; display: inline-block; }
    .japanese-word { cursor: pointer; margin: 0 2px; }
    .stButton>button { width: 100%; }
    @media (max-width: 768px) {
        .metric-card { padding: 0.5rem; }
        .metric-card h3 { font-size: 1rem; margin: 0; }
        .metric-card h2 { font-size: 2rem; margin: 0; }
    }
</style>
""", unsafe_allow_html=True)


# --- Core Functions ---

def assess_pronunciation(reference_text, audio_data, language):
    """Processes audio and returns assessment results."""
    with st.spinner("🔄 Analyzing pronunciation..."):
        try:
            wav_data = convert_audio_format(audio_data, "webm", "wav")
            if not wav_data:
                st.error("Failed to process audio")
                return None

            temp_audio_file = save_audio_to_temp_file(wav_data, "wav")
            if not temp_audio_file:
                st.error("Failed to save audio file")
                return None

            assessor = PronunciationAssessment(language)
            result = assessor.assess_pronunciation(temp_audio_file, reference_text)
            cleanup_temp_file(temp_audio_file)

            if result['success']:
                return {
                    'result': result, 'reference_text': reference_text,
                    'language': language, 'assessor': assessor
                }
            else:
                st.error(f"Assessment failed: {result.get('error', 'Unknown error')}")
                return None
        except Exception as e:
            st.error(f"An unexpected error occurred during assessment: {str(e)}")
            return None


def display_combined_assessment_results(assessment_data):
    """Displays a combined and simplified view of the assessment results."""
    if not assessment_data:
        return

    data = assessment_data
    result = data.get('result', {})
    reference_text = data.get('reference_text', '')
    language = data.get('language', 'English')
    assessor = data.get('assessor')

    if not result or not assessor:
        st.warning("Assessment data is incomplete.")
        return

    st.subheader("📊 Assessment Results")

    if 'detailed_result' in result:
        words_assessment = assessor.get_word_level_assessment(result['detailed_result'])
        if words_assessment:
            st.write("**📝 Word Analysis**")
            word_html = "".join([
                f'<span class="{"word-correct" if w["accuracy_score"] >= 80 else "word-partial" if w["accuracy_score"] >= 60 else "word-incorrect"}">{w["word"]}</span> '
                for w in words_assessment
            ])
            st.markdown(word_html, unsafe_allow_html=True)
        else:
            st.write("**📝 Word Analysis:** Not available for this assessment.")

    st.divider()
    col1, col2 = st.columns([2, 1])

    with col1:
        st.write("**🗣️ You said:**")
        st.write(result.get('recognized_text', 'No speech detected'))
        st.write("**📖 Reference:**")
        if language == "Japanese":
            words_with_romaji = get_romanization_with_words(reference_text, language)
            st.markdown("".join(
                [f'<span class="japanese-word" title="{romaji}">{word}</span>' for word, romaji in words_with_romaji]),
                unsafe_allow_html=True)
        else:
            st.write(reference_text)

    with col2:
        overall_score = result.get('pronunciation_score', 0)
        color = "success-card" if overall_score >= 80 else "warning-card" if overall_score >= 60 else "error-card"
        st.markdown(f"""
        <div class="metric-card {color}">
            <h3>Overall Score</h3>
            <h2>{overall_score:.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
        if overall_score >= 90:
            st.success("🎉 Excellent!")
        elif overall_score >= 80:
            st.info("👍 Good job!")
        elif overall_score >= 60:
            st.warning("Needs practice.")
        else:
            st.error("More practice needed.")


def handle_automatic_processing(audio_data, text, language, max_duration, audio_key, assessment_key, autoplay_key):
    """Unified logic for post-recording processing."""
    duration = get_audio_duration(audio_data)
    if duration > max_duration:
        st.warning(f"⚠️ Recording too long ({duration:.1f}s). Max is {max_duration}s.")
        return

    if duration > 0:
        st.success(f"✅ Recorded: {duration:.1f}s. Processing now...")

        assessment_result = assess_pronunciation(text, audio_data, language)
        st.session_state[assessment_key] = assessment_result

        if not st.session_state.get(audio_key):
            with st.spinner("🎼 Creating reference audio..."):
                st.session_state[audio_key] = generate_speech_audio(text, language)

        if st.session_state.get(audio_key):
            st.session_state[autoplay_key] = st.session_state[audio_key]

        st.rerun()


def display_audio_and_results(audio_key, assessment_key, autoplay_key):
    """Unified logic for displaying audio player and assessment results."""
    # Autoplay is handled first
    if st.session_state.get(autoplay_key):
        audio_url = st.session_state[autoplay_key]
        st.markdown(f'<audio src="{audio_url}" autoplay style="display:none;"></audio>', unsafe_allow_html=True)
        st.audio(audio_url)
        # Unset flag after use to prevent re-playing on other interactions
        del st.session_state[autoplay_key]

    # If not autoplaying, but audio exists, show the standard player
    elif st.session_state.get(audio_key):
        st.audio(st.session_state[audio_key])

    # Display assessment results if available
    if st.session_state.get(assessment_key):
        display_combined_assessment_results(st.session_state[assessment_key])


# --- UI Rendering Functions for Modes ---

def render_speaking_mode():
    """Renders the UI for the standard Speaking Mode."""
    st.header("Speaking Mode")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.selectbox("Select Language:", list(LANGUAGE_CONFIG.keys()), key="speaking_language")
    with col2:
        st.markdown(f"### {LANGUAGE_CONFIG[st.session_state.speaking_language]['icon']}")

    language = st.session_state.speaking_language
    sample_texts = get_sample_texts()[language]
    with st.expander("📚 Sample Texts"):
        for level, texts in sample_texts.items():
            st.write(f"**{level}:**")
            cols = st.columns(len(texts))
            for i, text in enumerate(texts):
                if cols[i].button(text, key=f"{language}_{level}_{i}"):
                    st.session_state.selected_text = text
                    st.session_state.is_breakdown_view = False
                    st.session_state.processed_audio_hash = None  # Reset flag
                    st.rerun()

    reference_text = st.text_area("Enter text to practice:",
                                  value=st.session_state.get('selected_text', sample_texts['Beginner'][0]), height=100,
                                  key="main_text_input")

    if st.session_state.get('is_breakdown_view', False):
        # --- BREAKDOWN VIEW ---
        if st.button("⬅️ Practice as Full Text"):
            st.session_state.is_breakdown_view = False
            st.session_state.processed_audio_hash = None  # Reset flag
            st.rerun()

        st.subheader("Practice Sentences")
        for i, sentence in enumerate(st.session_state.get('speaking_chunks', [])):
            with st.container(border=True):
                st.markdown(f"**Sentence {i + 1}:** `{sentence}`")

                audio_key = f'audio_speak_chunk_{i}'
                assessment_key = f'assessment_result_speak_chunk_{i}'
                autoplay_key = f'autoplay_audio_chunk_{i}'

                col1, col2 = st.columns(2)
                with col1:
                    audio_data = audiorecorder("🎙️ Record", "⏹️ Stop", key=f"recorder_speak_chunk_{i}")
                with col2:
                    if st.button("🔊 Listen", key=f"speak_chunk_listen_{i}"):
                        if not st.session_state.get(audio_key):
                            with st.spinner("Generating audio..."):
                                st.session_state[audio_key] = generate_speech_audio(sentence, language)
                        if st.session_state.get(audio_key):
                            st.session_state[autoplay_key] = st.session_state[audio_key]
                            st.rerun()

                # THE FIX: Check hash of audio data, not its ID
                if audio_data and hash(audio_data) != st.session_state.get('processed_audio_hash'):
                    st.session_state['processed_audio_hash'] = hash(audio_data)
                    handle_automatic_processing(audio_data, sentence, language, MAX_CHUNK_RECORDING_DURATION, audio_key,
                                                assessment_key, autoplay_key)

                display_audio_and_results(audio_key, assessment_key, autoplay_key)

    else:
        # --- FULL TEXT VIEW ---
        if st.button("⏬ Breakdown into Sentences", disabled=not reference_text.strip()):
            st.session_state.speaking_chunks = split_text_into_sentences(reference_text)
            st.session_state.is_breakdown_view = True
            st.session_state.processed_audio_hash = None  # Reset flag
            st.rerun()

        if reference_text.strip():
            audio_key = f'audio_full_{hash(reference_text)}'
            assessment_key = 'assessment_result_full'
            autoplay_key = f'autoplay_audio_full'

            col1, col2 = st.columns([1, 1])
            with col1:
                audio_data = audiorecorder("🎙️ Record", "⏹️ Stop",
                                           key=f"recorder_full_{language}_{hash(reference_text)}")
            with col2:
                if st.button("🔊 Listen", key="listen_full"):
                    if not st.session_state.get(audio_key):
                        with st.spinner("🎼 Creating audio..."):
                            st.session_state[audio_key] = generate_speech_audio(reference_text, language)
                    if st.session_state.get(audio_key):
                        st.session_state[autoplay_key] = st.session_state[audio_key]
                        st.rerun()

            # THE FIX: Check hash of audio data, not its ID
            if audio_data and hash(audio_data) != st.session_state.get('processed_audio_hash'):
                st.session_state['processed_audio_hash'] = hash(audio_data)
                handle_automatic_processing(audio_data, reference_text, language, MAX_RECORDING_DURATION, audio_key,
                                            assessment_key, autoplay_key)

            display_audio_and_results(audio_key, assessment_key, autoplay_key)


def render_translation_mode():
    """Renders the UI for the new Translation Mode."""
    st.header("Translation Mode")

    col1, col2 = st.columns(2)
    col1.selectbox("Display Language:", list(LANGUAGE_CONFIG.keys()), key="translation_display_language")
    col2.selectbox("Speak Language:", list(LANGUAGE_CONFIG.keys()), key="translation_speak_language")

    display_lang = st.session_state.translation_display_language
    speak_lang = st.session_state.translation_speak_language
    placeholder_text = get_translation_placeholder_text(display_lang, speak_lang)

    multi_lang_input = st.text_area(
        "Paste bilingual text here and click Parse.", height=200, placeholder=placeholder_text)

    if st.button("🤖 Parse with AI", type="primary"):
        with st.spinner("Parsing text..."):
            chunks = parse_text_with_poe(multi_lang_input, display_lang, speak_lang)
            st.session_state.translation_chunks = chunks if chunks else []
            st.session_state.processed_audio_hash = None  # Reset flag
            if chunks:
                st.success(f"✅ Successfully parsed into {len(chunks)} chunks.")
            else:
                st.error("Failed to parse text. Please check the format or try again.")
            st.rerun()

    if st.session_state.get('translation_chunks'):
        st.subheader("Practice Chunks")
        for i, chunk in enumerate(st.session_state.translation_chunks):
            with st.container(border=True):
                st.markdown(f"**Display ({display_lang}):** `{chunk['display']}`")
                st.divider()

                speak_text = chunk['speak']
                audio_key = f'audio_chunk_display_{i}'
                assessment_key = f'assessment_result_chunk_{i}'
                autoplay_key = f'autoplay_audio_translation_chunk_{i}'

                with st.expander(f"Reveal and Listen to text ({speak_lang})"):
                    st.write(speak_text)
                    if st.button(f"🔊 Listen", key=f"gen_audio_display_{i}"):
                        if not st.session_state.get(audio_key):
                            with st.spinner("Generating audio..."):
                                st.session_state[audio_key] = generate_speech_audio(speak_text, speak_lang)
                        if st.session_state.get(audio_key):
                            st.session_state[autoplay_key] = st.session_state[audio_key]
                            st.rerun()

                audio_data = audiorecorder("🎙️ Record to Speak", "⏹️ Stop", key=f"recorder_chunk_{i}")

                # THE FIX: Check hash of audio data, not its ID
                if audio_data and hash(audio_data) != st.session_state.get('processed_audio_hash'):
                    st.session_state['processed_audio_hash'] = hash(audio_data)
                    handle_automatic_processing(audio_data, speak_text, speak_lang, MAX_CHUNK_RECORDING_DURATION,
                                                audio_key, assessment_key, autoplay_key)

                display_audio_and_results(audio_key, assessment_key, autoplay_key)


# --- Main Application Logic ---

def main():
    """Main function to run the Streamlit app."""
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")

    # Initialize session state for caching and loop prevention
    if 'mode' not in st.session_state: st.session_state.mode = "Speaking"
    if 'speaking_language' not in st.session_state: st.session_state.speaking_language = "Japanese"
    if 'translation_display_language' not in st.session_state: st.session_state.translation_display_language = "English"
    if 'translation_speak_language' not in st.session_state: st.session_state.translation_speak_language = "French"
    if 'translation_chunks' not in st.session_state: st.session_state.translation_chunks = []
    if 'speaking_chunks' not in st.session_state: st.session_state.speaking_chunks = []
    if 'is_breakdown_view' not in st.session_state: st.session_state.is_breakdown_view = False
    # THE FIX: Initialize the hash variable
    if 'processed_audio_hash' not in st.session_state: st.session_state.processed_audio_hash = None

    def reset_view_and_audio_hash():
        st.session_state.is_breakdown_view = False
        st.session_state.processed_audio_hash = None  # Reset flag on mode change

    st.radio("Select Mode", ["Speaking", "Translation"], key='mode', horizontal=True,
             on_change=reset_view_and_audio_hash)
    st.divider()

    if st.session_state.mode == "Speaking":
        render_speaking_mode()
    else:
        render_translation_mode()

    with st.expander("💡 Pronunciation Tips"):
        lang = st.session_state.speaking_language if st.session_state.mode == "Speaking" else st.session_state.translation_speak_language
        tips = get_pronunciation_tips(lang)
        for tip in tips: st.markdown(f"- {tip}")


if __name__ == "__main__":
    main()