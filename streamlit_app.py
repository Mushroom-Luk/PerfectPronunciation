import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from audiorecorder import audiorecorder
import tempfile
import os

# Import custom modules
from utils.azure_speech import JapanesePronunciationAssessment
from utils.audio_utils import convert_audio_format, save_audio_to_temp_file, cleanup_temp_file, get_audio_duration
from utils.japanese_utils import japanese_to_romaji, get_japanese_sample_texts, analyze_japanese_text, \
    get_pronunciation_tips
from config import *

# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
    }
    .success-card {
        border-left-color: #51cf66;
    }
    .warning-card {
        border-left-color: #ffd43b;
    }
    .error-card {
        border-left-color: #ff6b6b;
    }
    .japanese-text {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2d3748;
        background-color: #f7fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 2px solid #e2e8f0;
    }
    .romaji-text {
        font-size: 1.2rem;
        color: #4a5568;
        font-style: italic;
        background-color: #edf2f7;
        padding: 0.5rem;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)


# --- ALL HELPER FUNCTIONS (assess_pronunciation, display_assessment_results, etc.) GO HERE ---

def assess_pronunciation(reference_text, audio_data, enable_word_analysis, enable_phoneme_analysis):
    """Perform pronunciation assessment."""
    # ... (your existing assess_pronunciation code) ...
    with st.spinner("🔄 Analyzing your pronunciation..."):
        try:
            # Convert audio format
            wav_data = convert_audio_format(audio_data, "webm", "wav")
            if wav_data is None:
                st.error("Failed to process audio data")
                return

            # Save to temporary file
            temp_audio_file = save_audio_to_temp_file(wav_data, "wav")
            if temp_audio_file is None:
                st.error("Failed to save audio file")
                return

            # Initialize assessment
            assessor = JapanesePronunciationAssessment()

            # Perform assessment
            result = assessor.assess_pronunciation(temp_audio_file, reference_text)

            # Clean up temp file
            cleanup_temp_file(temp_audio_file)

            # Display results
            if result['success']:
                display_assessment_results(result, reference_text, enable_word_analysis, enable_phoneme_analysis)
            else:
                st.error(f"Assessment failed: {result['error']}")
                if 'error_details' in result:
                    st.error(f"Details: {result['error_details']}")

        except Exception as e:
            st.error(f"An error occurred during assessment: {str(e)}")


def display_assessment_results(result, reference_text, enable_word_analysis, enable_phoneme_analysis):
    """Display pronunciation assessment results."""
    # ... (your existing display_assessment_results code) ...
    st.header("📊 Assessment Results")

    # Overall scores
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        score = result.get('accuracy_score', 0)
        color = get_score_color(score)
        st.markdown(f"""
        <div class="metric-card {color}">
            <h3>Accuracy</h3>
            <h2>{score:.1f}/100</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        score = result.get('fluency_score', 0)
        color = get_score_color(score)
        st.markdown(f"""
        <div class="metric-card {color}">
            <h3>Fluency</h3>
            <h2>{score:.1f}/100</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        score = result.get('completeness_score', 0)
        color = get_score_color(score)
        st.markdown(f"""
        <div class="metric-card {color}">
            <h3>Completeness</h3>
            <h2>{score:.1f}/100</h2>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        score = result.get('pronunciation_score', 0)
        color = get_score_color(score)
        st.markdown(f"""
        <div class="metric-card {color}">
            <h3>Overall</h3>
            <h2>{score:.1f}/100</h2>
        </div>
        """, unsafe_allow_html=True)

    # Score visualization
    scores_data = {
        'Metric': ['Accuracy', 'Fluency', 'Completeness', 'Overall'],
        'Score': [
            result.get('accuracy_score', 0),
            result.get('fluency_score', 0),
            result.get('completeness_score', 0),
            result.get('pronunciation_score', 0)
        ]
    }

    fig = px.bar(
        scores_data,
        x='Metric',
        y='Score',
        color='Score',
        color_continuous_scale=['red', 'yellow', 'green'],
        range_color=[0, 100],
        title="Pronunciation Assessment Scores"
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Recognized vs Reference text
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📖 Reference Text")
        st.markdown(f'<div class="japanese-text">{reference_text}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("🗣️ What You Said")
        recognized_text = result.get('recognized_text', 'No speech detected')
        st.markdown(f'<div class="japanese-text">{recognized_text}</div>', unsafe_allow_html=True)

    # Word-level analysis
    if enable_word_analysis and 'detailed_result' in result:
        assessor = JapanesePronunciationAssessment()
        words_assessment = assessor.get_word_level_assessment(result['detailed_result'])

        if words_assessment:
            st.subheader("📝 Word-by-Word Analysis")

            # Create word analysis dataframe
            word_data = []
            for word_info in words_assessment:
                word_data.append({
                    'Word': word_info['word'],
                    'Accuracy': word_info['accuracy_score'],
                    'Error Type': word_info['error_type'],
                    'Status': get_word_status(word_info['accuracy_score'])
                })

            if word_data:
                df_words = pd.DataFrame(word_data)

                # Color-coded word display
                word_html = ""
                for _, row in df_words.iterrows():
                    color = "green" if row['Accuracy'] >= 80 else "orange" if row['Accuracy'] >= 60 else "red"
                    word_html += f'<span style="background-color: {color}; color: white; padding: 2px 8px; margin: 2px; border-radius: 4px; font-weight: bold;">{row["Word"]} ({row["Accuracy"]:.0f}%)</span> '

                st.markdown(word_html, unsafe_allow_html=True)

                # Word analysis table
                st.dataframe(df_words, use_container_width=True)

                # Phoneme-level analysis
                if enable_phoneme_analysis:
                    st.subheader("🔤 Phoneme Analysis")
                    for word_info in words_assessment:
                        if word_info['phonemes']:
                            st.write(f"**{word_info['word']}**")
                            phoneme_cols = st.columns(len(word_info['phonemes']))
                            for i, phoneme in enumerate(word_info['phonemes']):
                                with phoneme_cols[i]:
                                    color = get_score_color(phoneme['accuracy_score'])
                                    st.markdown(f"""
                                    <div class="metric-card {color}" style="text-align: center; margin: 5px;">
                                        <div style="font-size: 1.2rem; font-weight: bold;">{phoneme['phoneme']}</div>
                                        <div>{phoneme['accuracy_score']:.0f}%</div>
                                    </div>
                                    """, unsafe_allow_html=True)

    # Feedback and suggestions
    st.subheader("💬 Feedback & Suggestions")

    overall_score = result.get('pronunciation_score', 0)

    if overall_score >= 90:
        st.success("🎉 Excellent pronunciation! Your Japanese sounds very natural.")
    elif overall_score >= 80:
        st.success("👍 Great job! Your pronunciation is quite good with minor areas for improvement.")
    elif overall_score >= 70:
        st.warning("📈 Good effort! Focus on clarity and rhythm for better results.")
    elif overall_score >= 60:
        st.warning("🎯 Keep practicing! Pay attention to individual syllable pronunciation.")
    else:
        st.error("🔄 More practice needed. Try speaking slower and focusing on each sound.")

    # Specific recommendations
    recommendations = generate_recommendations(result)
    for rec in recommendations:
        st.info(rec)


def get_score_color(score):
    """Get color class based on score."""
    if score >= 80:
        return "success-card"
    elif score >= 60:
        return "warning-card"
    else:
        return "error-card"


def get_word_status(accuracy):
    """Get word status based on accuracy."""
    if accuracy >= 80:
        return "✅ Correct"
    elif accuracy >= 60:
        return "⚠️ Needs Improvement"
    else:
        return "❌ Incorrect"


def generate_recommendations(result):
    """Generate specific recommendations based on assessment results."""
    recommendations = []

    accuracy = result.get('accuracy_score', 0)
    fluency = result.get('fluency_score', 0)
    completeness = result.get('completeness_score', 0)

    if accuracy < 70:
        recommendations.append(
            "🎯 **Accuracy**: Focus on pronouncing each syllable clearly. Practice with shorter phrases first.")

    if fluency < 70:
        recommendations.append(
            "⏱️ **Fluency**: Work on speaking rhythm. Japanese has even syllable timing - practice with a metronome.")

    if completeness < 70:
        recommendations.append(
            "🗣️ **Completeness**: Make sure to pronounce all parts of the text. Slow down if needed.")

    if not recommendations:
        recommendations.append(
            "🌟 **Great work!** Continue practicing to maintain your excellent pronunciation skills.")

    return recommendations

# --- END OF HELPER FUNCTIONS ---


def main():
    # Title and description
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    st.markdown("**Practice Japanese pronunciation with AI-powered detailed feedback**")

    # Sidebar for configuration
    with st.sidebar:
        st.header("🎛️ Settings")

        # Azure credentials check
        if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
            st.error("⚠️ Azure Speech Service not configured!")
            st.info("Add your credentials to `.streamlit/secrets.toml`:")
            st.code("""
[secrets]
AZURE_SPEECH_KEY = "your_key_here"
AZURE_SPEECH_REGION = "your_region_here"
            """)
            st.stop()
        else:
            st.success("✅ Azure Speech Service configured")

        # Assessment settings
        st.subheader("Assessment Settings")
        enable_word_analysis = st.checkbox("Word-level Analysis", value=True)
        enable_phoneme_analysis = st.checkbox("Phoneme-level Analysis", value=True)
        show_detailed_tips = st.checkbox("Show Pronunciation Tips", value=True)

        # Sample texts
        st.subheader("📚 Sample Texts")
        sample_texts = get_japanese_sample_texts()

        for level, texts in sample_texts.items():
            st.write(f"**{level}**")
            for text in texts:
                if st.button(f"{text}", key=f"sample_{text}"):
                    st.session_state.selected_text = text

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        # Text input section
        st.header("📝 Japanese Text Input")

        # Text input
        japanese_text = st.text_area(
            "Enter Japanese text to practice:",
            value=st.session_state.get('selected_text', 'こんにちは'),
            height=100,
            placeholder="例: こんにちは、元気ですか？"
        )

        if japanese_text:
            # Show romaji
            romaji = japanese_to_romaji(japanese_text)
            if romaji != japanese_text:
                st.markdown(f'<div class="romaji-text">Romaji: {romaji}</div>', unsafe_allow_html=True)

            # Text analysis
            analysis = analyze_japanese_text(japanese_text)
            if analysis['total_characters'] > 0:
                col1_analysis, col2_analysis, col3_analysis = st.columns(3)
                with col1_analysis:
                    st.metric("Total Characters", analysis['total_characters'])
                with col2_analysis:
                    st.metric("Hiragana", analysis['hiragana_count'])
                with col3_analysis:
                    st.metric("Kanji", analysis['kanji_count'])

        # Audio recording section
        st.header("🎤 Record Your Pronunciation")

        audio_data = audiorecorder(
            start_prompt="Click to record",
            # recording_color="#e74c3c",
            # neutral_color="#34495e",
            # icon_name="microphone",
            # icon_size="2x",
        )

        if audio_data is not None:
            # Get audio duration
            duration = get_audio_duration(audio_data)
            st.info(f"🕐 Recording duration: {duration:.1f} seconds")

            # Assessment button
            if st.button("🔍 Assess Pronunciation", type="primary"):
                if not japanese_text.strip():
                    st.error("Please enter Japanese text first!")
                else:
                    # This call is now valid because assess_pronunciation is defined above
                    assess_pronunciation(japanese_text, audio_data, enable_word_analysis, enable_phoneme_analysis)

    with col2:
        # Tips and information
        st.header("💡 Pronunciation Tips")
        if show_detailed_tips:
            tips = get_pronunciation_tips()
            for tip in tips:
                st.markdown(tip)

        # Audio quality tips
        st.subheader("🎧 Recording Tips")
        st.markdown("""
        - Speak clearly and at normal pace
        - Use a quiet environment
        - Hold device at comfortable distance
        - Pronounce each syllable distinctly
        - Take your time with longer phrases
        """)


if __name__ == "__main__":
    main()