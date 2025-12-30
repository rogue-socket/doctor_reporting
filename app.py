import os
import json
import streamlit as st
import time
from datetime import datetime

# --- Your existing imports ---
import whisper
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from fpdf import FPDF, XPos, YPos
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import google.generativeai as genai

# ---------------- CONFIG ----------------
if "audio_path" not in st.session_state:
    st.session_state.audio_path = None

st.set_page_config(page_title="Doctor Reporting Assistant", layout="centered")

BASE_MIC_DIR = "./input_files/liv_mic"
os.makedirs(BASE_MIC_DIR, exist_ok=True)

# ---------------- GEMINI SETUP ----------------
genai.configure(api_key="AIzaSyBQc6oQAzPHxj-GEDgUnDIybQofN0Twjgo")
MODEL = genai.GenerativeModel("gemini-2.5-flash")

# ---------------- SCHEMA ----------------
class DiagnosisOutput(BaseModel):
    patient_name: Optional[str]
    age: Optional[str]
    gender: Optional[str]
    chief_complaint: Optional[str]
    diagnosis: Optional[str]
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    raw_transcript: str

# ---------------- CORE FUNCTIONS ----------------
@st.cache_resource
def load_whisper():
    return whisper.load_model("base", device="cpu")

def transcribe_audio(audio_path: str) -> str:
    model = load_whisper()
    result = model.transcribe(audio_path)
    return result["text"]

def extract_with_gemini(transcript: str) -> DiagnosisOutput:
    schema_json = json.dumps(
        DiagnosisOutput.model_json_schema(),
        indent=2
    )

    prompt = f"""
You are a medical information extraction system.

RULES:
- Populate known fields if present
- Put extra information into extracted_entities
- Use null if missing
- Do not hallucinate
- Output strictly matching JSON schema

JSON SCHEMA:
{schema_json}

TRANSCRIPT:
\"\"\"{transcript}\"\"\"

OUTPUT JSON ONLY:
"""

    response = MODEL.generate_content(prompt)
    text = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(text)

    data["raw_transcript"] = transcript
    return DiagnosisOutput(**data)

def generate_pdf(data: DiagnosisOutput, output_path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Medical Diagnosis Report",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(5)
    pdf.set_font("Helvetica", size=12)

    fixed_fields = [
        ("Patient Name", data.patient_name),
        ("Age", data.age),
        ("Gender", data.gender),
        ("Chief Complaint", data.chief_complaint),
        ("Diagnosis", data.diagnosis),
    ]

    for title, value in fixed_fields:
        if value:
            pdf.multi_cell(0, 8, f"{title}: {value}")
            pdf.ln(1)

    if data.extracted_entities:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Additional Clinical Details",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font("Helvetica", size=12)
        for k, v in data.extracted_entities.items():
            pdf.multi_cell(0, 8, f"{k.replace('_',' ').title()}: {v}")
            pdf.ln(1)

    pdf.output(output_path)

def record_from_mic(duration_seconds: int = 30, sample_rate: int = 16000) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(BASE_MIC_DIR, f"live_recording_{timestamp}.wav")

    audio = sd.rec(
        int(duration_seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )
    sd.wait()
    write(path, sample_rate, audio)

    return path

# ---------------- STREAMLIT UI ----------------
st.title("🩺 Doctor Reporting Assistant")

mode = st.radio(
    "Choose input method:",
    ["Upload Audio File", "Record Live Microphone"]
)

audio_path = None

if mode == "Upload Audio File":
    uploaded = st.file_uploader("Upload diagnosis audio", type=["wav", "mp3", "m4a"])
    if uploaded:
        os.makedirs("./input_files/uploaded", exist_ok=True)
        audio_path = f"./input_files/uploaded/{uploaded.name}"
        with open(audio_path, "wb") as f:
            f.write(uploaded.read())
        st.success("Audio uploaded successfully")

# else:
#     duration = st.slider("Recording duration (seconds)", 10, 120, 30)
#     if st.button("🎙️ Start Recording"):
#         if st.button("🎙️ Start Recording"):
#             st.session_state.audio_path = record_from_mic(duration)
#             st.success("Recording completed. You can now generate the report.")

else:
    duration = st.slider("Recording duration (seconds)", 10, 120, 30)

    if st.button("🎙️ Start Recording"):
        status_text = st.empty()
        countdown_text = st.empty()
        progress_bar = st.progress(0)

        status_text.warning("🔴 Recording in progress...")

        # Start recording in background
        audio_frames = sd.rec(
            int(duration * 16000),
            samplerate=16000,
            channels=1,
            dtype="int16"
        )

        # Countdown + progress bar
        for remaining in range(duration, 0, -1):
            countdown_text.info(f"⏱️ Recording... {remaining} seconds remaining")
            progress = int(((duration - remaining + 1) / duration) * 100)
            progress_bar.progress(progress)
            time.sleep(1)

        sd.wait()

        # Save audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(BASE_MIC_DIR, f"live_recording_{timestamp}.wav")
        write(path, 16000, audio_frames)

        # Update session state
        st.session_state.audio_path = path

        # Final UI update
        progress_bar.progress(100)
        countdown_text.empty()
        status_text.success("✅ Recording completed. Ready to generate report.")


        # with st.spinner("Recording..."):
        #     audio_path = record_from_mic(duration)
        # st.success(f"Recording saved")

if st.session_state.audio_path and st.button("🧠 Generate Report"):
    audio_path = st.session_state.audio_path

    with st.spinner("Transcribing audio..."):
        transcript = transcribe_audio(audio_path)

    st.subheader("📝 Transcript")
    # st.text_area("", transcript, height=200)
    st.text_area(
        "Transcript",
        transcript,
        height=200,
        label_visibility="collapsed"
    )

    with st.spinner("Extracting information with Gemini..."):
        extracted = extract_with_gemini(transcript)

    st.subheader("📊 Extracted Information")
    st.json(extracted.model_dump(exclude={"raw_transcript"}))

    pdf_path = f"diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    generate_pdf(extracted, pdf_path)

    with open(pdf_path, "rb") as f:
        st.download_button(
            label="📄 Download PDF Report",
            data=f,
            file_name=pdf_path,
            mime="application/pdf"
        )
