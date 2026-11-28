
from pathlib import Path
import whisper

_model = None

def transcribe_audio(audio_path, model_name="base"):
    global _model

    audio_path = Path(audio_path)

    if not audio_path.exists():
        return None, f"Audio file not found: {audio_path}"

    try:
        if _model is None:
            _model = whisper.load_model(model_name)

        result = _model.transcribe(
            str(audio_path),
            fp16=False
        )

        transcript = result["text"].strip()
        return transcript, None

    except Exception as error:
        return None, str(error)
