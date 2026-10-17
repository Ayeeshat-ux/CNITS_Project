# src/speech_engine.py

import os
import speech_recognition as sr
from gtts import gTTS

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


def text_to_speech(text, filename="output.mp3"):
    """Convert text to speech and save it as an MP3 file."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    tts = gTTS(text=text, lang="en", slow=False)
    tts.save(filename)
    return filename


def speech_to_text(audio_file_path):
    """Convert a recorded audio file into text with multi-format fallback."""
    if not os.path.exists(audio_file_path):
        return None

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    # 1. Direct WAV Recognition
    try:
        with sr.AudioFile(audio_file_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(
            audio_data,
            language="en-NG"
        )
        if text and len(text.strip()) > 0:
            return text.strip()
    except Exception:
        pass

    # 2. Container Audio Conversion Fallback (pydub)
    if PYDUB_AVAILABLE:
        converted_path = audio_file_path + "_converted.wav"
        try:
            sound = AudioSegment.from_file(audio_file_path)
            sound.export(converted_path, format="wav")

            with sr.AudioFile(converted_path) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio_data = recognizer.record(source)

            text = recognizer.recognize_google(
                audio_data,
                language="en-NG"
            )

            if text and len(text.strip()) > 0:
                return text.strip()
        except Exception:
            pass
        finally:
            if os.path.exists(converted_path):
                try:
                    os.remove(converted_path)
                except Exception:
                    pass

    return None