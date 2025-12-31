# import os
# import json
# import time
# import av
# import queue
# import streamlit as st
# from datetime import datetime
# from typing import Optional, Dict, Any

# import whisper
# from fpdf import FPDF, XPos, YPos
# from pydantic import BaseModel, Field
# import google.generativeai as genai
# from streamlit_webrtc import webrtc_streamer, AudioProcessorBase

# # ---------------- PAGE CONFIG ----------------
# st.set_page_config(page_title="Doctor Reporting Assistant", layout="centered")

# BASE_MIC_DIR = "./input_files/liv_mic"
# UPLOAD_DIR = "./input_files/uploaded"
# os.makedirs(BASE_MIC_DIR, exist_ok=True)
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# # ---------------- GEMINI ----------------
# genai.configure(api_key=st.secrets["gem_key"])
# MODEL = genai.GenerativeModel("gemini-2.5-flash")

# # ---------------- SCHEMA ----------------
# class DiagnosisOutput(BaseModel):
#     patient_name: Optional[str]
#     age: Optional[str]
#     gender: Optional[str]
#     chief_complaint: Optional[str]
#     diagnosis: Optional[str]
#     extracted_entities: Dict[str, Any] = Field(default_factory=dict)
#     raw_transcript: str

# # ---------------- WHISPER ----------------
# @st.cache_resource
# def load_whisper():
#     return whisper.load_model("base", device="cpu")

# def transcribe_audio(audio_path: str) -> str:
#     model = load_whisper()
#     return model.transcribe(audio_path)["text"]

# # ---------------- GEMINI EXTRACTION ----------------
# def extract_with_gemini(transcript: str) -> DiagnosisOutput:
#     schema_json = json.dumps(DiagnosisOutput.model_json_schema(), indent=2)

#     prompt = f"""
# You are a medical information extraction system.

# Rules:
# - Use null if missing
# - Do not hallucinate
# - Output valid JSON only
# - Match schema exactly

# SCHEMA:
# {schema_json}

# TRANSCRIPT:
# \"\"\"{transcript}\"\"\"
# """

#     response = MODEL.generate_content(prompt)
#     text = response.text.replace("```json", "").replace("```", "").strip()
#     data = json.loads(text)
#     data["raw_transcript"] = transcript
#     return DiagnosisOutput(**data)

# # ---------------- PDF ----------------
# def generate_pdf(data: DiagnosisOutput, output_path: str):
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_auto_page_break(True, 15)

#     pdf.set_font("Helvetica", "B", 16)
#     pdf.cell(0, 10, "Medical Diagnosis Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
#     pdf.ln(5)

#     pdf.set_font("Helvetica", size=12)

#     fields = [
#         ("Patient Name", data.patient_name),
#         ("Age", data.age),
#         ("Gender", data.gender),
#         ("Chief Complaint", data.chief_complaint),
#         ("Diagnosis", data.diagnosis),
#     ]

#     for k, v in fields:
#         if v:
#             pdf.multi_cell(0, 8, f"{k}: {v}")
#             pdf.ln(1)

#     if data.extracted_entities:
#         pdf.ln(3)
#         pdf.set_font("Helvetica", "B", 13)
#         pdf.cell(0, 8, "Additional Clinical Details",
#                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
#         pdf.set_font("Helvetica", size=12)
#         for k, v in data.extracted_entities.items():
#             pdf.multi_cell(0, 8, f"{k.replace('_',' ').title()}: {v}")

#     pdf.output(output_path)

# # ---------------- WEBRTC AUDIO ----------------
# class AudioRecorder(AudioProcessorBase):
#     def __init__(self):
#         self.frames = queue.Queue()

#     def recv(self, frame: av.AudioFrame):
#         self.frames.put(frame)
#         return frame

#     def save(self, path):
#         import soundfile as sf
#         samples = []
#         while not self.frames.empty():
#             frame = self.frames.get()
#             samples.append(frame.to_ndarray())
#         if samples:
#             audio = samples[0] if len(samples) == 1 else sum(samples)
#             sf.write(path, audio.T, 16000)

# # ---------------- UI ----------------
# st.title("🩺 Doctor Reporting Assistant")

# mode = st.radio(
#     "Choose input method",
#     ["Upload Audio File", "Record Live Microphone"]
# )

# audio_path = None

# # -------- UPLOAD MODE --------
# if mode == "Upload Audio File":
#     uploaded = st.file_uploader("Upload diagnosis audio", type=["wav", "mp3", "m4a"])
#     if uploaded:
#         audio_path = os.path.join(UPLOAD_DIR, uploaded.name)
#         with open(audio_path, "wb") as f:
#             f.write(uploaded.read())
#         st.success("Audio uploaded successfully")

# # -------- LIVE MIC MODE --------
# else:
#     duration = st.slider("Recording duration (seconds)", 5, 60, 20)

#     st.info("🎙️ Press start, speak clearly, and wait for countdown")

#     recorder = AudioRecorder()

#     ctx = webrtc_streamer(
#         key="mic",
#         audio_processor_factory=lambda: recorder,
#         media_stream_constraints={"audio": True, "video": False},
#     )

#     if ctx.state.playing:
#         countdown = st.empty()
#         for i in range(duration, 0, -1):
#             countdown.markdown(f"⏱️ **Recording… {i}s remaining**")
#             time.sleep(1)
#         countdown.markdown("✅ **Recording finished**")

#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         audio_path = os.path.join(BASE_MIC_DIR, f"live_recording_{timestamp}.wav")
#         recorder.save(audio_path)
#         st.success("Recording saved")

# # -------- PROCESS --------
# if audio_path and st.button("🧠 Generate Report"):
#     with st.spinner("Transcribing audio..."):
#         transcript = transcribe_audio(audio_path)

#     st.subheader("📝 Transcript")
#     st.text_area("Transcript", transcript, height=200)

#     with st.spinner("Extracting information with Gemini..."):
#         extracted = extract_with_gemini(transcript)

#     st.subheader("📊 Extracted Information")
#     st.json(extracted.model_dump(exclude={"raw_transcript"}))

#     pdf_path = f"diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
#     generate_pdf(extracted, pdf_path)

#     with open(pdf_path, "rb") as f:
#         st.download_button(
#             "📄 Download PDF",
#             data=f,
#             file_name=pdf_path,
#             mime="application/pdf"
#         )


# import os
# import json
# import time
# import av
# import queue
# import streamlit as st
# from datetime import datetime
# from typing import Optional, Dict, Any
# from textwrap import wrap

# import whisper
# from fpdf import FPDF
# from pydantic import BaseModel, Field
# import google.generativeai as genai
# from streamlit_webrtc import webrtc_streamer, AudioProcessorBase

# # ---------------- PAGE CONFIG ----------------
# st.set_page_config(page_title="Doctor Reporting Assistant", layout="centered")

# BASE_MIC_DIR = "./input_files/liv_mic"
# UPLOAD_DIR = "./input_files/uploaded"
# os.makedirs(BASE_MIC_DIR, exist_ok=True)
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# # ---------------- GEMINI ----------------
# genai.configure(api_key=st.secrets["gem_key"])
# MODEL = genai.GenerativeModel("gemini-2.5-flash")

# # ---------------- SCHEMA ----------------
# class DiagnosisOutput(BaseModel):
#     patient_name: Optional[str]
#     age: Optional[str]
#     gender: Optional[str]
#     chief_complaint: Optional[str]
#     diagnosis: Optional[str]
#     extracted_entities: Dict[str, Any] = Field(default_factory=dict)
#     raw_transcript: str

# # ---------------- WHISPER ----------------
# @st.cache_resource
# def load_whisper():
#     return whisper.load_model("base", device="cpu")

# def transcribe_audio(audio_path: str) -> str:
#     model = load_whisper()
#     return model.transcribe(audio_path)["text"]

# # ---------------- GEMINI EXTRACTION ----------------
# def extract_with_gemini(transcript: str) -> DiagnosisOutput:
#     schema_json = json.dumps(DiagnosisOutput.model_json_schema(), indent=2)
#     prompt = f"""
# You are a medical information extraction system.

# Rules:
# - Use null if missing
# - Do not hallucinate
# - Output valid JSON only
# - Match schema exactly

# SCHEMA:
# {schema_json}

# TRANSCRIPT:
# \"\"\"{transcript}\"\"\"
# """
#     response = MODEL.generate_content(prompt)
#     text = response.text.replace("```json", "").replace("```", "").strip()
#     data = json.loads(text)
#     data["raw_transcript"] = transcript
#     return DiagnosisOutput(**data)

# # ---------------- PDF SAFE MULTI_CELL ----------------
# def safe_multi_cell(pdf: FPDF, text: str, line_height: int = 8):
#     """Wraps text safely and prints with multi_cell"""
#     max_width = pdf.w - 2 * pdf.l_margin
#     lines = []
#     for line in text.split("\n"):
#         # Wrap each line at ~max 90 characters
#         wrapped = wrap(line, width=90)
#         lines.extend(wrapped if wrapped else [""])
#     for line in lines:
#         pdf.multi_cell(0, line_height, line)

# def generate_pdf(data: DiagnosisOutput, output_path: str):
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_auto_page_break(True, 15)

#     pdf.set_font("Helvetica", "B", 16)
#     safe_multi_cell(pdf, "Medical Diagnosis Report", line_height=10)
#     pdf.ln(5)

#     pdf.set_font("Helvetica", size=12)

#     fields = [
#         ("Patient Name", data.patient_name),
#         ("Age", data.age),
#         ("Gender", data.gender),
#         ("Chief Complaint", data.chief_complaint),
#         ("Diagnosis", data.diagnosis),
#     ]

#     for k, v in fields:
#         if v:
#             safe_multi_cell(pdf, f"{k}: {v}")
#             pdf.ln(1)

#     if data.extracted_entities:
#         pdf.ln(3)
#         pdf.set_font("Helvetica", "B", 13)
#         safe_multi_cell(pdf, "Additional Clinical Details", line_height=9)
#         pdf.set_font("Helvetica", size=12)
#         for k, v in data.extracted_entities.items():
#             if v is not None:
#                 safe_multi_cell(pdf, f"{k.replace('_',' ').title()}: {v}")
#                 pdf.ln(1)

#     pdf.output(output_path)

# # ---------------- WEBRTC AUDIO ----------------
# class AudioRecorder(AudioProcessorBase):
#     def __init__(self):
#         self.frames = queue.Queue()

#     def recv(self, frame: av.AudioFrame):
#         self.frames.put(frame)
#         return frame

#     def save(self, path):
#         import soundfile as sf
#         samples = []
#         while not self.frames.empty():
#             frame = self.frames.get()
#             samples.append(frame.to_ndarray())
#         if samples:
#             audio = samples[0] if len(samples) == 1 else sum(samples)
#             sf.write(path, audio.T, 16000)

# # ---------------- UI ----------------
# st.title("🩺 Doctor Reporting Assistant")

# mode = st.radio(
#     "Choose input method",
#     ["Upload Audio File", "Record Live Microphone"]
# )

# audio_path = None

# # -------- UPLOAD MODE --------
# if mode == "Upload Audio File":
#     uploaded = st.file_uploader("Upload diagnosis audio", type=["wav"])
#     if uploaded:
#         audio_path = os.path.join(UPLOAD_DIR, uploaded.name)
#         with open(audio_path, "wb") as f:
#             f.write(uploaded.read())
#         st.success("Audio uploaded successfully")

# # -------- LIVE MIC MODE --------
# else:
#     duration = st.slider("Recording duration (seconds)", 5, 60, 20)
#     st.info("🎙️ Press start, speak clearly, and wait for countdown")

#     recorder = AudioRecorder()
#     ctx = webrtc_streamer(
#         key="mic",
#         audio_processor_factory=lambda: recorder,
#         media_stream_constraints={"audio": True, "video": False},
#     )

#     if ctx.state.playing:
#         countdown = st.empty()
#         for i in range(duration, 0, -1):
#             countdown.markdown(f"⏱️ **Recording… {i}s remaining**")
#             time.sleep(1)
#         countdown.markdown("✅ **Recording finished**")

#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         audio_path = os.path.join(BASE_MIC_DIR, f"live_recording_{timestamp}.wav")
#         recorder.save(audio_path)
#         st.success("Recording saved")

# # -------- PROCESS --------
# if audio_path and st.button("🧠 Generate Report"):
#     with st.spinner("Transcribing audio..."):
#         transcript = transcribe_audio(audio_path)

#     st.subheader("📝 Transcript")
#     st.text_area("Transcript", transcript, height=200)

#     with st.spinner("Extracting information with Gemini..."):
#         extracted = extract_with_gemini(transcript)

#     st.subheader("📊 Extracted Information")
#     st.json(extracted.model_dump(exclude={"raw_transcript"}))

#     pdf_path = f"diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
#     generate_pdf(extracted, pdf_path)

#     with open(pdf_path, "rb") as f:
#         st.download_button(
#             "📄 Download PDF",
#             data=f,
#             file_name=pdf_path,
#             mime="application/pdf"
#         )


import os
import json
import time
import av
import queue
import textwrap
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any

import whisper
from fpdf import FPDF, XPos, YPos
from pydantic import BaseModel, Field
import google.generativeai as genai
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Doctor Reporting Assistant",
    layout="centered"
)

# ================= PATHS =================
BASE_MIC_DIR = "./input_files/liv_mic"
UPLOAD_DIR = "./input_files/uploaded"

os.makedirs(BASE_MIC_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ================= GEMINI =================
genai.configure(api_key=st.secrets["gem_key"])
MODEL = genai.GenerativeModel("gemini-2.5-flash")

# ================= SCHEMA =================
class DiagnosisOutput(BaseModel):
    patient_name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    raw_transcript: str

# ================= WHISPER =================
@st.cache_resource
def load_whisper():
    return whisper.load_model("base", device="cpu")

def transcribe_audio(path: str) -> str:
    model = load_whisper()
    result = model.transcribe(path)
    return result.get("text", "").strip()

# ================= GEMINI EXTRACTION =================
def extract_with_gemini(transcript: str) -> DiagnosisOutput:
    schema = json.dumps(DiagnosisOutput.model_json_schema(), indent=2)

    prompt = f"""
You are a medical information extraction system.

Rules:
- Use null if missing
- Do not hallucinate
- Output VALID JSON ONLY
- Match schema EXACTLY

SCHEMA:
{schema}

TRANSCRIPT:
\"\"\"{transcript}\"\"\"
"""

    response = MODEL.generate_content(prompt)
    text = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(text)
    data["raw_transcript"] = transcript
    return DiagnosisOutput(**data)

# ================= SAFE PDF HELPERS =================
def safe_multicell(pdf, text, line_height=8, max_chars=90):
    """
    Bulletproof wrapper for FPDF.multi_cell
    Prevents 'Not enough horizontal space' crashes.
    """
    if not text:
        return

    text = str(text).replace("\t", " ").replace("\r", "")
    lines = []

    for raw_line in text.split("\n"):
        wrapped = textwrap.wrap(
            raw_line,
            width=max_chars,
            break_long_words=True,
            break_on_hyphens=False
        )
        lines.extend(wrapped if wrapped else [" "])

    for line in lines:
        pdf.multi_cell(
            0,
            line_height,
            line,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
        )

def generate_pdf(data: DiagnosisOutput, output_path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, 15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(
        0,
        10,
        "Medical Diagnosis Report",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT
    )
    pdf.ln(4)

    pdf.set_font("Helvetica", size=12)

    fields = [
        ("Patient Name", data.patient_name),
        ("Age", data.age),
        ("Gender", data.gender),
        ("Chief Complaint", data.chief_complaint),
        ("Diagnosis", data.diagnosis),
    ]

    for label, value in fields:
        if value:
            safe_multicell(pdf, f"{label}: {value}")
            pdf.ln(1)

    if data.extracted_entities:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(
            0,
            8,
            "Additional Clinical Details",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
        )
        pdf.set_font("Helvetica", size=12)

        for k, v in data.extracted_entities.items():
            safe_multicell(
                pdf,
                f"{k.replace('_', ' ').title()}: {v}"
            )

    pdf.output(output_path)

# ================= WEBRTC AUDIO =================
class AudioRecorder(AudioProcessorBase):
    def __init__(self):
        self.frames = queue.Queue()

    def recv(self, frame: av.AudioFrame):
        self.frames.put(frame)
        return frame

    def save(self, path):
        import soundfile as sf
        import numpy as np

        samples = []
        while not self.frames.empty():
            f = self.frames.get()
            samples.append(f.to_ndarray())

        if not samples:
            return

        audio = np.concatenate(samples, axis=1)
        sf.write(path, audio.T, 16000)

# ================= UI =================
st.title("🩺 Doctor Reporting Assistant")

mode = st.radio(
    "Choose input method",
    ["Upload Audio File", "Record Live Microphone"]
)

audio_path = None

# -------- UPLOAD --------
if mode == "Upload Audio File":
    uploaded = st.file_uploader(
        "Upload diagnosis audio",
        type=["wav", "mp3", "m4a"]
    )
    if uploaded:
        audio_path = os.path.join(UPLOAD_DIR, uploaded.name)
        with open(audio_path, "wb") as f:
            f.write(uploaded.read())
        st.success("Audio uploaded")

# -------- LIVE MIC --------
else:
    duration = st.slider("Recording duration (seconds)", 5, 60, 20)
    st.info("🎙 Speak clearly after pressing Start")

    recorder = AudioRecorder()

    ctx = webrtc_streamer(
        key="live-mic",
        audio_processor_factory=lambda: recorder,
        media_stream_constraints={"audio": True, "video": False},
    )

    if ctx.state.playing:
        countdown = st.empty()
        for i in range(duration, 0, -1):
            countdown.markdown(f"⏱ Recording… {i}s")
            time.sleep(1)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = os.path.join(
            BASE_MIC_DIR,
            f"live_recording_{timestamp}.wav"
        )
        recorder.save(audio_path)
        countdown.markdown("✅ Recording complete")
        st.success("Audio saved")

# -------- PROCESS --------
if audio_path and st.button("🧠 Generate Report"):
    with st.spinner("Transcribing audio…"):
        transcript = transcribe_audio(audio_path)

    st.subheader("📝 Transcript")
    st.text_area("Transcript", transcript, height=200)

    with st.spinner("Extracting information with Gemini…"):
        extracted = extract_with_gemini(transcript)

    st.subheader("📊 Extracted Information")
    st.json(extracted.model_dump(exclude={"raw_transcript"}))

    pdf_path = f"diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    generate_pdf(extracted, pdf_path)

    with open(pdf_path, "rb") as f:
        st.download_button(
            "📄 Download PDF",
            data=f,
            file_name=pdf_path,
            mime="application/pdf"
        )
