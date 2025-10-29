import streamlit as st
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
        background-color: #f8f9fa; padding: 0.3rem; border-radius: 0.3rem;
        border-left: 3px solid; margin: 0.1rem; text-align: center;
    }
    .success-card { border-left-color: #28a745; }
    .warning-card { border-left-color: #ffc107; }
    .error-card { border-left-color: #dc3545; }
    .word-correct { background-color: #d4edda; color: #155724; padding: 3px 8px; margin: 2px; border-radius: 4px; display: inline-block; }
    .word-partial { background-color: #fff3cd; color: #856404; padding: 3px 8px; margin: 2px; border-radius: 4px; display: inline-block; }
    .word-incorrect { background-color: #f8d7da; color: #721c24; padding: 3px 8px; margin: 2px; border-radius: 4px; display: inline-block; }
    .japanese-word { cursor: pointer; margin: 0 2px; }
    .phoneme-container { border: 1px solid #ddd; border-radius: 8px; padding: 10px; margin: 5px 0; background-color: #fafafa; }
    .phoneme-scores { display: flex; justify-content: space-around; font-weight: bold; margin-bottom: 5px; font-size: 0.9rem; }
    .phoneme-letters { display: flex; justify-content: space-around; font-family: monospace; font-size: 1.1rem; }
    .phoneme-score { color: #666; }
    .phoneme-letter { color: #333; }
    .stButton>button { width: 100%; }
    .chunk-container { border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
    textarea[aria-label="Paste bilingual text here and click Parse."]::placeholder {
        font-size: 0.85rem;
    }
    @media (max-width: 768px) {
        .metric-card { padding: 0.2rem; }
        .metric-card h3 { font-size: 0.8rem; margin: 0; }
        .metric-card h2 { font-size: 1.2rem; margin: 0; }
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


def display_assessment_results(assessment_data):
    """Displays assessment results from a given data dictionary."""
    if not assessment_data: return

    result = assessment_data['result']
    st.subheader("📊 Assessment Results")
    scores = [
        ("Accuracy", result.get('accuracy_score', 0)), ("Fluency", result.get('fluency_score', 0)),
        ("Completeness", result.get('completeness_score', 0)), ("Overall", result.get('pronunciation_score', 0))
    ]
    cols = st.columns(4)
    for i, (label, score) in enumerate(scores):
        color = "success-card" if score >= 80 else "warning-card" if score >= 60 else "error-card"
        with cols[i]:
            st.markdown(f'<div class="metric-card {color}"><h3>{label}</h3><h2>{score:.0f}</h2></div>',
                        unsafe_allow_html=True)

    st.write("**🗣️ You said:** ", result.get('recognized_text', 'No speech detected'))
    overall_score = result.get('pronunciation_score', 0)
    if overall_score >= 90:
        st.success("🎉 Excellent pronunciation!")
    elif overall_score >= 80:
        st.success("👍 Good pronunciation with minor improvements needed")
    elif overall_score >= 70:
        st.warning("📈 Focus on clarity and rhythm")
    else:
        st.error("🔄 More practice needed - speak slower and clearer")


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
                    st.session_state.is_breakdown_view = False  # Reset view
                    st.rerun()

    reference_text = st.text_area("Enter text to practice:",
                                  value=st.session_state.get('selected_text', sample_texts['Beginner'][0]), height=100,
                                  key="main_text_input")

    # --- View Toggle: Full Text vs. Breakdown ---
    if st.session_state.get('is_breakdown_view', False):
        # --- BREAKDOWN VIEW ---
        if st.button("⬅️ Practice as Full Text"):
            st.session_state.is_breakdown_view = False
            st.rerun()

        st.subheader("Practice Sentences")
        for i, sentence in enumerate(st.session_state.get('speaking_chunks', [])):
            with st.container(border=True):
                st.markdown(f"**Sentence {i + 1}:** `{sentence}`")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔊 Listen", key=f"speak_chunk_listen_{i}"):
                        with st.spinner("Generating audio..."):
                            audio_url = generate_speech_audio(sentence, language)
                            st.session_state[f'audio_speak_chunk_{i}'] = audio_url if audio_url else None

                if f'audio_speak_chunk_{i}' in st.session_state and st.session_state[f'audio_speak_chunk_{i}']:
                    st.audio(st.session_state[f'audio_speak_chunk_{i}'])

                with col2:
                    audio_data = audiorecorder("🎙️ Record", "⏹️ Stop", key=f"recorder_speak_chunk_{i}")

                if audio_data:
                    duration = get_audio_duration(audio_data)
                    if duration > MAX_CHUNK_RECORDING_DURATION:
                        st.warning(f"⚠️ Recording too long ({duration:.1f}s). Max is {MAX_CHUNK_RECORDING_DURATION}s.")
                    elif duration > 0:
                        st.success(f"✅ Recorded: {duration:.1f}s")
                        if st.button("🔍 Assess", key=f"assess_speak_chunk_{i}"):
                            assessment_result = assess_pronunciation(sentence, audio_data, language)
                            st.session_state[f'assessment_result_speak_chunk_{i}'] = assessment_result

                if f'assessment_result_speak_chunk_{i}' in st.session_state:
                    display_assessment_results(st.session_state[f'assessment_result_speak_chunk_{i}'])

    else:
        # --- FULL TEXT VIEW ---
        if st.button("⏬ Breakdown into Sentences", disabled=not reference_text.strip()):
            st.session_state.speaking_chunks = split_text_into_sentences(reference_text)
            st.session_state.is_breakdown_view = True
            st.rerun()

        if reference_text.strip():
            col1, col2 = st.columns([1, 1])
            with col1:
                st.write("**🎤 Record (max 60s):**")
                audio_data = audiorecorder("🎙️ Record", "⏹️ Stop",
                                           key=f"recorder_full_{language}_{hash(reference_text)}")
            with col2:
                st.write("**🔊 Listen:**")
                if st.button("🎵 Generate Audio", key="gen_audio_full"):
                    with st.spinner("🎼 Creating audio..."):
                        audio_url = generate_speech_audio(reference_text, language)
                        st.session_state[f'audio_full_{hash(reference_text)}'] = audio_url if audio_url else None

            audio_key = f'audio_full_{hash(reference_text)}'
            if audio_key in st.session_state and st.session_state[audio_key]:
                st.audio(st.session_state[audio_key])

            if audio_data:
                duration = get_audio_duration(audio_data)
                if duration > MAX_RECORDING_DURATION:
                    st.warning(f"⚠️ Recording too long ({duration:.1f}s). Max is {MAX_RECORDING_DURATION}s.")
                elif duration > 0:
                    st.success(f"✅ Recorded: {duration:.1f}s")
                    if st.button("🔍 Assess", type="primary"):
                        assessment_result = assess_pronunciation(reference_text, audio_data, language)
                        st.session_state['assessment_result_full'] = assessment_result

        if 'assessment_result_full' in st.session_state:
            # Use the more detailed display for the full text assessment
            display_assessment_results_detailed(st.session_state.assessment_result_full)


def render_translation_mode():
    """Renders the UI for the new Translation Mode."""
    st.header("Translation Mode")

    col1, col2 = st.columns(2)
    col1.selectbox("Display Language:", list(LANGUAGE_CONFIG.keys()), key="translation_display_language")
    col2.selectbox("Speak Language:", list(LANGUAGE_CONFIG.keys()), key="translation_speak_language")

    display_lang = st.session_state.translation_display_language
    speak_lang = st.session_state.translation_speak_language

    # Generate dynamic placeholder text based on selected languages
    placeholder_text = get_translation_placeholder_text(display_lang, speak_lang)

    multi_lang_input = st.text_area(
        "Paste bilingual text here and click Parse.", height=200,
        placeholder=placeholder_text
    )

    if st.button("🤖 Parse with AI", type="primary"):
        chunks = parse_text_with_poe(multi_lang_input, display_lang, speak_lang)
        st.session_state.translation_chunks = chunks if chunks else []
        if chunks:
            st.success(f"✅ Successfully parsed into {len(chunks)} chunks.")
        else:
            st.error("Failed to parse text. Please check the format or try again.")

    if st.session_state.get('translation_chunks'):
        st.subheader("Practice Chunks")
        for i, chunk in enumerate(st.session_state.translation_chunks):
            with st.container(border=True):
                st.markdown(f"**Display ({display_lang}):** `{chunk['display']}`")

                st.divider()

                with st.expander(f"Reveal text to speak ({speak_lang})"):
                    st.write(chunk['speak'])
                    # Listen to Display Text
                    if st.button(f"🔊 Listen", key=f"gen_audio_display_{i}"):
                        with st.spinner("Generating audio..."):
                            audio_url = generate_speech_audio(chunk['speak'], speak_lang)
                            st.session_state[f'audio_chunk_display_{i}'] = audio_url if audio_url else None

                    if f'audio_chunk_display_{i}' in st.session_state and st.session_state[f'audio_chunk_display_{i}']:
                        st.audio(st.session_state[f'audio_chunk_display_{i}'])

                audio_data = audiorecorder("🎙️ Record to Speak", "⏹️ Stop", key=f"recorder_chunk_{i}")

                if audio_data:
                    duration = get_audio_duration(audio_data)
                    if duration > MAX_CHUNK_RECORDING_DURATION:
                        st.warning(f"⚠️ Recording too long ({duration:.1f}s). Max is {MAX_CHUNK_RECORDING_DURATION}s.")
                    elif duration > 0:
                        st.success(f"✅ Recorded: {duration:.1f}s")
                        if st.button("🔍 Assess", key=f"assess_chunk_{i}"):
                            assessment_result = assess_pronunciation(chunk['speak'], audio_data, speak_lang)
                            st.session_state[f'assessment_result_chunk_{i}'] = assessment_result

                if f'assessment_result_chunk_{i}' in st.session_state:
                    display_assessment_results(st.session_state[f'assessment_result_chunk_{i}'])


def display_assessment_results_detailed(assessment_data):
    """A more detailed version of the display function, used for the full-text assessment."""
    if not assessment_data: return

    data = assessment_data
    result, reference_text, language, assessor = data['result'], data['reference_text'], data['language'], data[
        'assessor']

    st.subheader("📊 Assessment Results")
    words_assessment = assessor.get_word_level_assessment(result['detailed_result'])
    if words_assessment:
        st.write("**📝 Word Analysis:**")
        word_html = "".join([
                                f'<span class="{"word-correct" if w["accuracy_score"] >= 80 else "word-partial" if w["accuracy_score"] >= 60 else "word-incorrect"}">{w["word"]}</span> '
                                for w in words_assessment])
        st.markdown(word_html, unsafe_allow_html=True)

    display_assessment_results(assessment_data)  # Display common elements like scores

    col1, col2 = st.columns(2)
    with col1:
        st.write("**📖 Reference:**")
        if language == "Japanese":
            words_with_romaji = get_romanization_with_words(reference_text, language)
            st.markdown("".join(
                [f'<span class="japanese-word" title="{romaji}">{word}</span>' for word, romaji in words_with_romaji]),
                        unsafe_allow_html=True)
        else:
            st.write(reference_text)
    with col2:
        st.write("**🗣️ You said:**")
        st.write(result.get('recognized_text', 'No speech detected'))


# --- Main Application Logic ---

def main():
    """Main function to run the Streamlit app."""
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")

    # Initialize session state for caching
    if 'mode' not in st.session_state: st.session_state.mode = "Speaking"
    if 'speaking_language' not in st.session_state: st.session_state.speaking_language = "Japanese"
    if 'translation_display_language' not in st.session_state: st.session_state.translation_display_language = "English"
    if 'translation_speak_language' not in st.session_state: st.session_state.translation_speak_language = "French"
    if 'translation_chunks' not in st.session_state: st.session_state.translation_chunks = []
    if 'speaking_chunks' not in st.session_state: st.session_state.speaking_chunks = []
    if 'is_breakdown_view' not in st.session_state: st.session_state.is_breakdown_view = False

    st.radio("Select Mode", ["Speaking", "Translation"], key='mode', horizontal=True,
             on_change=lambda: st.session_state.update(is_breakdown_view=False))
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