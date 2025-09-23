import streamlit as st
from pydub import AudioSegment
import io
import tempfile
import os


def convert_audio_format(audio_input, input_format="webm", output_format="wav"):
    try:
        if isinstance(audio_input, AudioSegment):
            audio = audio_input
        else:
            audio = AudioSegment.from_file(io.BytesIO(audio_input), format=input_format)

        audio = audio.set_frame_rate(16000).set_channels(1)
        output_buffer = io.BytesIO()
        audio.export(output_buffer, format=output_format)
        output_buffer.seek(0)
        return output_buffer.getvalue()
    except Exception as e:
        st.error(f"Audio conversion error: {str(e)}")
        return None


def save_audio_to_temp_file(audio_data_bytes, format="wav"):
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}")
        temp_file.write(audio_data_bytes)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        st.error(f"File save error: {str(e)}")
        return None


def cleanup_temp_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass


def get_audio_duration(audio_input):
    try:
        if isinstance(audio_input, AudioSegment):
            return len(audio_input) / 1000.0
        audio = AudioSegment.from_file(io.BytesIO(audio_input))
        return len(audio) / 1000.0
    except:
        return 0