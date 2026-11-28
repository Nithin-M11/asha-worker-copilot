# ASHA Worker Copilot — runnable prototype

A Streamlit + SQLite demonstration aligned with the ASHA Copilot build plan:
voice capture → speech-to-text (optional local Whisper) → keyword/regex extraction → human confirmation → SQLite record → transparent rule flags → follow-up list → PHC dashboard → simulated sync.

## Run on Windows / VS Code

1. Install Python 3.10 or newer.
2. Extract this ZIP and open the `asha_worker_copilot` folder in VS Code.
3. Open Terminal in VS Code and run:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

On Ubuntu/macOS, activate with `source .venv/bin/activate`.

The app opens in your browser at the local address shown in the terminal.

## Test the main flow

Go to **Record a visit** and paste:

`Lakshmi is 7 months pregnant. She has headache and swelling in feet. BP 145 over 92. Weight 58 kg.`

Click **Extract fields from note**, review the fields and symptoms, then click **Confirm & save visit**. The record is saved in `data/asha_copilot.db`. Check the Overview and PHC dashboard.

## Optional audio transcription

The browser audio control captures a recording. For local Whisper transcription, install FFmpeg and then:

```bash
pip install openai-whisper
```

Restart Streamlit, record audio, then choose **Transcribe audio with local Whisper**. Whisper model download requires an internet connection the first time. If Whisper/FFmpeg is unavailable, use the transcript text box and symptom selector.

## What works in this prototype

- Synthetic beneficiary seed data (fictional names/villages)
- Voice recording control and optional Whisper integration
- Keyword and regex extraction for pregnancy month, BP, weight and symptoms
- Editable confirmation form before saving
- SQLite local persistence
- Explainable demonstration risk rules
- Follow-up to-do list with completion
- PHC-style dashboard and CSV export
- Simulated offline sync status

## Important limitations

- The risk rules are illustrative software-demo logic, not validated clinical decision support. They have not been reviewed by a doctor/ANM and must not be used for care decisions.
- No real PHC server, authentication, encryption, consent workflow, or multi-device sync is configured.
- Demo data only. Never enter identifiable or real patient health data.
- Local-language recognition (Kannada/Hindi) needs accuracy testing with multiple speakers before being claimed as supported.
- A real deployment requires current official Ministry of Health / MCP guidance, clinical review, security/privacy design and field testing.

## Reset demo database

Stop Streamlit, delete `data/asha_copilot.db`, and run `streamlit run app.py` again. The sample data will be recreated.
