
import os
import speech_recognition as sr
from gtts import gTTS


def text_to_speech(text, filename="output.mp3"):
    """Convert text to speech and save it as an MP3 file."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    tts = gTTS(text=text, lang="en", slow=False)
    tts.save(filename)

    return filename


def speech_to_text(audio_file_path):
    """Convert a WAV audio recording into text."""
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)

        return recognizer.recognize_google(
            audio_data,
            language="en-NG"
        )

    except sr.UnknownValueError:
        return None

    except sr.RequestError as error:
        raise RuntimeError(
            f"Speech recognition service unavailable: {error}"
        ) from error

    except (OSError, ValueError) as error:
        raise RuntimeError(
            f"Could not process the audio file: {error}"
        ) from error
