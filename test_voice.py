
from voice_module import transcribe_audio

audio_path = "data/latest_visit_audio.wav"

transcript, error = transcribe_audio(audio_path)

if error:
    print("Error:", error)
else:
    print("Transcript:", transcript)
