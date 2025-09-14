import streamlit as st
import numpy as np
from pydub import AudioSegment
import io
import tempfile
import os


def convert_audio_format(audio_input, input_format="webm", output_format="wav"):
    """
    Convert audio from one format to another or process an AudioSegment.
    Accepts either raw bytes or a pydub.AudioSegment object.
    """
    try:
        if isinstance(audio_input, AudioSegment):
            audio = audio_input
        else:
            # Assume it's bytes if not an AudioSegment
            # The 'input_format' hint is used if audio_input is bytes
            audio = AudioSegment.from_file(io.BytesIO(audio_input), format=input_format)

        # Ensure correct sample rate and channels for Azure Speech
        audio = audio.set_frame_rate(16000).set_channels(1)

        # Export to bytes in the desired output format
        output_buffer = io.BytesIO()
        audio.export(output_buffer, format=output_format)
        output_buffer.seek(0)

        return output_buffer.getvalue()
    except Exception as e:
        st.error(f"Error converting audio: {str(e)}")
        return None


def save_audio_to_temp_file(audio_data_bytes, format="wav"):
    """Save audio data (expected to be bytes) to a temporary file."""
    try:
        if not isinstance(audio_data_bytes, bytes):
            st.error("Expected bytes for saving to file, but received a different type.")
            return None

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}")
        temp_file.write(audio_data_bytes)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        st.error(f"Error saving audio file: {str(e)}")
        return None


def cleanup_temp_file(file_path):
    """Clean up temporary files."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        st.warning(f"Could not clean up temp file: {str(e)}")


def get_audio_duration(audio_input):
    """
    Get duration of audio in seconds.
    Accepts either raw bytes or a pydub.AudioSegment object.
    """
    try:
        if isinstance(audio_input, AudioSegment):
            audio = audio_input
        else:
            # If it's not an AudioSegment, assume it's bytes and try to load it
            audio = AudioSegment.from_file(io.BytesIO(audio_input))
        return len(audio) / 1000.0  # Convert to seconds
    except Exception as e:
        st.error(f"Error getting audio duration: {str(e)}")
        return 0