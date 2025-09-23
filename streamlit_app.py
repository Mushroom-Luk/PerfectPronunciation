import streamlit as st
from audiorecorder import audiorecorder
from utils.speech_service import PronunciationAssessment, generate_speech_audio
from utils.audio_utils import convert_audio_format, save_audio_to_temp_file, cleanup_temp_file, get_audio_duration
from utils.language_utils import get_sample_texts, get_romanization_with_words, get_pronunciation_tips
from config import *

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout=LAYOUT)

# Mobile-friendly CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border-left: 3px solid;
        margin: 0.2rem 0;
    }
    .success-card { border-left-color: #28a745; }
    .warning-card { border-left-color: #ffc107; }
    .error-card { border-left-color: #dc3545; }
    .word-correct { background-color: #d4edda; color: #155724; padding: 2px 6px; margin: 2px; border-radius: 3px; }
    .word-partial { background-color: #fff3cd; color: #856404; padding: 2px 6px; margin: 2px; border-radius: 3px; }
    .word-incorrect { background-color: #f8d7da; color: #721c24; padding: 2px 6px; margin: 2px; border-radius: 3px; }
    .japanese-word { cursor: pointer; margin: 0 2px; }
    .audio-container { margin: 0.5rem 0; }
    @media (max-width: 768px) {
        .metric-card h3 { font-size: 1rem; }
        .metric-card h2 { font-size: 1.5rem; }
    }
</style>
""", unsafe_allow_html=True)


def assess_pronunciation(reference_text, audio_data, language, enable_word_analysis, enable_phoneme_analysis):
    with st.spinner("🔄 Analyzing pronunciation..."):
        try:
            wav_data = convert_audio_format(audio_data, "webm", "wav")
            if not wav_data:
                st.error("Failed to process audio")
                return

            temp_audio_file = save_audio_to_temp_file(wav_data, "wav")
            if not temp_audio_file:
                st.error("Failed to save audio file")
                return

            assessor = PronunciationAssessment(language)
            result = assessor.assess_pronunciation(temp_audio_file, reference_text)
            cleanup_temp_file(temp_audio_file)

            if result['success']:
                display_assessment_results(result, reference_text, language, assessor, enable_word_analysis,
                                           enable_phoneme_analysis)
            else:
                st.error(f"Assessment failed: {result['error']}")

        except Exception as e:
            st.error(f"Error: {str(e)}")


def display_assessment_results(result, reference_text, language, assessor, enable_word_analysis,
                               enable_phoneme_analysis):
    st.subheader("📊 Results")

    # Compact score display
    col1, col2, col3, col4 = st.columns(4)
    scores = [
        ("Accuracy", result.get('accuracy_score', 0)),
        ("Fluency", result.get('fluency_score', 0)),
        ("Completeness", result.get('completeness_score', 0)),
        ("Overall", result.get('pronunciation_score', 0))
    ]

    for i, (label, score) in enumerate(scores):
        color = "success-card" if score >= 80 else "warning-card" if score >= 60 else "error-card"
        with [col1, col2, col3, col4][i]:
            st.markdown(f"""
            <div class="metric-card {color}">
                <h3>{label}</h3>
                <h2>{score:.0f}/100</h2>
            </div>
            """, unsafe_allow_html=True)

    # Reference vs Recognition
    col1, col2 = st.columns(2)
    with col1:
        st.write("**📖 Reference:**")
        if language == "Japanese":
            words_with_romaji = get_romanization_with_words(reference_text, language)
            word_html = ""
            for word, romaji in words_with_romaji:
                word_html += f'<span class="japanese-word" title="{romaji}">{word}</span>'
            st.markdown(word_html, unsafe_allow_html=True)
        else:
            st.write(reference_text)

    with col2:
        st.write("**🗣️ You said:**")
        st.write(result.get('recognized_text', 'No speech detected'))

    # Word analysis
    if enable_word_analysis and 'detailed_result' in result:
        words_assessment = assessor.get_word_level_assessment(result['detailed_result'])
        if words_assessment:
            st.write("**📝 Word Analysis:**")
            word_html = ""
            for word_info in words_assessment:
                accuracy = word_info['accuracy_score']
                css_class = "word-correct" if accuracy >= 80 else "word-partial" if accuracy >= 60 else "word-incorrect"
                word_html += f'<span class="{css_class}">{word_info["word"]}</span> '
            st.markdown(word_html, unsafe_allow_html=True)

            # Phoneme analysis for high-support languages
            if enable_phoneme_analysis and language in ["English", "Mandarin"]:
                st.write("**🔤 Phoneme Analysis:**")
                for word_info in words_assessment:
                    if word_info['phonemes']:
                        st.write(f"**{word_info['word']}:** " +
                                 " ".join(
                                     [f"{p['phoneme']}({p['accuracy_score']:.0f})" for p in word_info['phonemes']]))

    # Feedback
    overall_score = result.get('pronunciation_score', 0)
    if overall_score >= 90:
        st.success("🎉 Excellent pronunciation!")
    elif overall_score >= 80:
        st.success("👍 Good pronunciation with minor improvements needed")
    elif overall_score >= 70:
        st.warning("📈 Focus on clarity and rhythm")
    else:
        st.error("🔄 More practice needed - speak slower and clearer")


def main():
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")

    # Language selection
    col1, col2 = st.columns([3, 1])
    with col1:
        language = st.selectbox("Select Language:", list(LANGUAGE_CONFIG.keys()), index=0)
    with col2:
        st.markdown(f"### {LANGUAGE_CONFIG[language]['icon']}")

    # Sample texts
    sample_texts = get_sample_texts()[language]
    if st.expander("📚 Sample Texts"):
        for level, texts in sample_texts.items():
            st.write(f"**{level}:**")
            cols = st.columns(len(texts))
            for i, text in enumerate(texts):
                if cols[i].button(text, key=f"{language}_{level}_{i}"):
                    st.session_state.selected_text = text

    # Text input
    reference_text = st.text_area(
        "Enter text to practice:",
        value=st.session_state.get('selected_text', sample_texts['Beginner'][0]),
        height=60
    )

    # Audio generation section
    if reference_text.strip():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**🔊 Listen to pronunciation:**")
        with col2:
            if st.button("🎵 Generate Audio"):
                with st.spinner("🎼 Creating audio..."):
                    audio_url = generate_speech_audio(reference_text, language)
                    if audio_url:
                        st.session_state[f'audio_{hash(reference_text)}'] = audio_url
                        st.rerun()
                    else:
                        st.error("Audio generation failed")

        # Display audio player if audio URL exists
        audio_key = f'audio_{hash(reference_text)}'
        if audio_key in st.session_state:
            st.markdown('<div class="audio-container">', unsafe_allow_html=True)
            st.audio(st.session_state[audio_key])  # Remove format parameter for URL
            st.markdown('</div>', unsafe_allow_html=True)

    # Settings
    col1, col2 = st.columns(2)
    with col1:
        enable_word_analysis = st.checkbox("Word Analysis", True)
    with col2:
        enable_phoneme_analysis = st.checkbox("Phoneme Analysis", True)

    # Recording
    st.write("**🎤 Record Your Pronunciation (max 1 min):**")
    audio_data = audiorecorder(start_prompt="🎙️ Record", stop_prompt="⏹️ Stop")

    if audio_data is not None:
        duration = get_audio_duration(audio_data)
        if duration > MAX_RECORDING_DURATION:
            st.warning(f"⚠️ Recording too long ({duration:.1f}s). Please keep under {MAX_RECORDING_DURATION}s")
        else:
            st.success(f"✅ Recorded: {duration:.1f}s")
            if st.button("🔍 Assess Pronunciation", type="primary"):
                assess_pronunciation(reference_text, audio_data, language, enable_word_analysis,
                                     enable_phoneme_analysis)

    # Tips
    if st.expander("💡 Pronunciation Tips"):
        tips = get_pronunciation_tips(language)
        for tip in tips:
            st.markdown(f"- {tip}")


if __name__ == "__main__":
    main()