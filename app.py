# app.py

from datetime import date
import os
import tempfile
import streamlit as st
from src.speech_engine import speech_to_text, text_to_speech
from src.rag_engine import get_agent_executor
from src.vaccine_tracker import (
    build_vaccine_schedule,
    calculate_age,
    group_vaccines_by_status,
)

# Safe imports for modular components
try:
    from src.health_center import display_health_center_finder
except ImportError:
    display_health_center_finder = None

try:
    from src.pdf_generator import render_pdf_generator
except ImportError:
    render_pdf_generator = None

st.set_page_config(
    page_title="CNITS - Child Nutrition & Immunization Tracking System",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for vibrant cards, badges, and layout styling
st.markdown("""
<style>
.stApp {
    background: #F5FAF9;
    color: #153D3D;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #064E4A, #003F40);
}
[data-testid="stSidebar"] * {
    color: #FFFFFF;
}
[data-testid="stSidebar"] .stRadio label {
    padding: 8px 10px;
}
h1, h2, h3 {
    color: #064E4A;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
.stButton > button {
    background: #087F79;
    color: white;
    border: 1px solid #087F79;
    border-radius: 10px;
    min-height: 42px;
    font-weight: 600;
}
.stButton > button:hover {
    background: #05645F;
    color: white;
}
.stTextArea textarea, .stTextInput input {
    background: white;
    border-radius: 8px;
}
[data-testid="stMetric"] {
    background: white;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #D9EAE7;
    box-shadow: 0 2px 8px #064e4a0a;
}
[data-testid="stMetricValue"] {
    font-size: 1.35rem !important;
}
[data-testid="stMetricLabel"] {
    color: #315A59;
}
.hero {
    background: linear-gradient(110deg, #E8F8F3, #D4F0E5);
    padding: 28px;
    border-radius: 16px;
    border: 1px solid #D7EEE6;
    margin-bottom: 20px;
}
.panel {
    background: white;
    padding: 22px;
    border: 1px solid #DCEAE8;
    border-radius: 14px;
    margin-bottom: 16px;
}
.small-note {
    color: #496C69;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.markdown("# 👶 CNITS")
    st.caption("Child Nutrition & Immunization Tracking System")
    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Home",
            "Nutrition AI",
            "Immunization Tracker",
            "Health Center Finder",
            "Growth & Health Passport",
            "Settings",
            "Help"
        ],
        label_visibility="collapsed",
        key="main_navigation"
    )

    st.divider()
    st.caption("💚 Healthy Children, Brighter Futures")
    st.caption("Nutrition • Immunization • Child Health")

# HEADER
st.markdown("""
<div class="hero">
    <h1>🌱 Welcome to CNITS!</h1>
    <p>Together for healthier, stronger and brighter children.</p>
</div>
""", unsafe_allow_html=True)

# Initialize Agent
has_ai_credentials = all(
    os.getenv(key) for key in ("OPENAI_API_KEY", "EMBEDDING_API_KEY")
)
if has_ai_credentials and "agent" not in st.session_state:
    st.session_state.agent = get_agent_executor()

if "messages" not in st.session_state:
    st.session_state.messages = []

# HOME DASHBOARD
if page == "Home":
    st.subheader("Child Health Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💉 System Status", "Active" if has_ai_credentials else "Setup Key")
    c2.metric("📚 Vector DB", "Connected")
    c3.metric("🏥 Health Centers", "Loaded")
    c4.metric("🏆 Competition", "Finals 2026")

    st.markdown("### Your CNITS Workspace")
    st.caption("Choose a feature below to continue.")

    nav1, nav2, nav3, nav4 = st.columns(4)

    if nav1.button("🥗 Nutrition AI", width='stretch'):
        st.session_state["main_navigation"] = "Nutrition AI"
        st.rerun()

    if nav2.button("💉 Immunization", width='stretch'):
        st.session_state["main_navigation"] = "Immunization Tracker"
        st.rerun()

    if nav3.button("🏥 Health Centers", width='stretch'):
        st.session_state["main_navigation"] = "Health Center Finder"
        st.rerun()

    if nav4.button("📈 Growth Passport", width='stretch'):
        st.session_state["main_navigation"] = "Growth & Health Passport"
        st.rerun()

    st.markdown("""
    <div class="panel">
        <h3>💚 Healthy Today, Brighter Tomorrow</h3>
        <p>CNITS brings child nutrition, immunization and health record support into one digital workspace.</p>
        <p class="small-note">Designed to support caregivers, healthcare professionals and competition judges.</p>
    </div>
    """, unsafe_allow_html=True)

# NUTRITION AI (RAG & Voice Integration)
elif page == "Nutrition AI":
    st.markdown("## 🥗 Nutrition AI Assistant")
    st.write("Ask any nutrition question, describe a meal, or record your voice in English or local Nigerian languages.")

    if not has_ai_credentials:
        st.warning("Please configure your `OPENAI_API_KEY` and `EMBEDDING_API_KEY` in your `.env` file.")

    left, right = st.columns([3, 2], gap="large")

    with left:
        recording = st.audio_input("🎙️ Record your question")

        if recording is not None:
            if st.button("Convert Speech to Text"):
                temp_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                        f.write(recording.getvalue())
                        temp_path = f.name

                    with st.spinner("Recognizing speech..."):
                        transcript = speech_to_text(temp_path)

                    st.session_state["nutrition_question"] = transcript
                    st.success("Transcription complete.")
                except Exception as error:
                    st.error(f"Speech recognition failed: {error}")
                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)

        user_input = st.text_area(
            "Your question or meal description",
            placeholder="Example: What local foods can I give my 6-month-old baby in Nigeria?",
            key="nutrition_question",
            height=130
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            evaluate_btn = st.button("✨ Evaluate with AI", width='stretch', disabled=not has_ai_credentials)
        with col_btn2:
            tts_btn = st.button("🔊 Read Aloud", width='stretch')

        if evaluate_btn and user_input.strip():
            with st.spinner("Analyzing NPHCDA & Health Guidelines..."):
                config = {"configurable": {"thread_id": "streamlit_user_session"}}
                prompt_instruction = (
                    f"Detect the language of the following user question and reply in that exact same language. "
                    f"User question: {user_input}"
                )
                response = st.session_state.agent.invoke(
                    {"messages": [("user", prompt_instruction)]},
                    config=config
                )
                bot_reply = response["messages"][-1].content
                st.markdown("### 🤖 AI Response:")
                st.success(bot_reply)
                st.session_state["last_bot_reply"] = bot_reply

        if tts_btn:
            text_to_read = st.session_state.get("last_bot_reply", user_input)
            if text_to_read.strip():
                audio_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                        audio_path = f.name
                    text_to_speech(text_to_read, audio_path)
                    with open(audio_path, "rb") as f:
                        st.audio(f.read(), format="audio/mp3")
                except Exception as error:
                    st.error(f"Text-to-speech failed: {error}")
                finally:
                    if audio_path and os.path.exists(audio_path):
                        os.remove(audio_path)
            else:
                st.warning("No text available to read.")

    with right:
        st.markdown("""
        <div class="panel">
            <h3>👶 Get Nutrition Support</h3>
            <p>CNITS nutrition guidance helps users:</p>
            <p>✓ Review meal information against NFCMS data</p>
            <p>✓ Identify possible nutrient gaps</p>
            <p>✓ Explore local Nigerian food pairings (crayfish, soybeans, pap)</p>
            <p>✓ Interact through voice or text in local languages</p>
        </div>
        """, unsafe_allow_html=True)

# IMMUNIZATION TRACKER
elif page == "Immunization Tracker":
    st.header("💉 Smart Immunization Schedule Tracker")
    st.write("Calculate your child's vaccination timeline based on the official Nigerian NPHCDA schedule.")

    col1, col2 = st.columns(2)
    with col1:
        dob = st.date_input("Child's Date of Birth", value=date(2026, 1, 1))
    with col2:
        as_of = st.date_input("Tracking Reference Date", value=date.today())

    if dob > as_of:
        st.error("Date of birth cannot be in the future.")
    else:
        age_info = calculate_age(dob, as_of)
        st.info(f"**Current Age:** {age_info['years']} yrs, {age_info['total_months'] % 12} mos ({age_info['total_weeks']} weeks / {age_info['total_days']} days)")

        records = build_vaccine_schedule(dob, as_of=as_of)
        grouped = group_vaccines_by_status(records)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🔴 Overdue", len(grouped["overdue"]))
        m2.metric("🟢 Due Now", len(grouped["due_now"]))
        m3.metric("🔵 Upcoming", len(grouped["upcoming"]))
        m4.metric("✅ Completed", len(grouped["completed"]))

        st.divider()
        display_data = []
        for r in records:
            display_data.append({
                "Vaccine": r["vaccine"],
                "Milestone": r["target_age_label"],
                "Due Date": r["due_date_label"],
                "Status": r["status"],
                "Dosage": r["dosage"],
                "Route": r["route"],
                "Site": r["site"]
            })
        st.dataframe(display_data, width='stretch', hide_index=True)

# HEALTH CENTERS
elif page == "Health Center Finder":
    if display_health_center_finder:
        display_health_center_finder()
    else:
        st.info("Health center finder module loading...")

# GROWTH & HEALTH PASSPORT
elif page == "Growth & Health Passport":
    if render_pdf_generator:
        render_pdf_generator()
    else:
        st.info("PDF generator module loading...")

# SETTINGS
elif page == "Settings":
    st.header("⚙️ Settings")
    st.write("Language preferences, API configuration, and user settings.")

# HELP
elif page == "Help":
    st.header("❓ Help & Support Center")
    st.markdown("""
        <div style="background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0;">
            <h3 style="color: #064E4A; margin-top: 0;">📌 Quick User Guide</h3>
            <ul>
                <li><b>Nutrition AI:</b> Ask questions or record voice notes to get localized nutritional advice.</li>
                <li><b>Immunization Tracker:</b> Automatically calculates NPHCDA routine childhood immunization schedules.</li>
                <li><b>Health Center Finder:</b> Locate nearby primary healthcare facilities instantly.</li>
                <li><b>Growth & Health Passport:</b> Export downloadable digital health passport PDFs.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)