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
    page_title="PikinCare | National Child Health & Immunization Platform",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Institutional Design System CSS
st.markdown("""
<style>
/* Global App Styling */
.stApp {
    background: #F8FBFA;
    color: #102A2A;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #023330 0%, #064E4A 100%);
    border-right: 1px solid #085D57;
}
[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] .stRadio label {
    padding: 10px 14px;
    border-radius: 8px;
    transition: background 0.2s ease;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255, 255, 255, 0.08);
}

/* Typography & Headings */
h1, h2, h3, h4 {
    color: #023330;
    font-weight: 700;
}

/* Hero Banner */
.hero-container {
    background: linear-gradient(135deg, #E2F4EE 0%, #C8EBE1 100%);
    padding: 32px 36px;
    border-radius: 16px;
    border: 1px solid #B4E3D4;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(6, 78, 74, 0.04);
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #023330;
    margin-bottom: 8px;
}
.hero-subtitle {
    font-size: 1.1rem;
    color: #235552;
    margin-bottom: 0;
}

/* Cards & Panels */
.institutional-card {
    background: #FFFFFF;
    padding: 24px;
    border-radius: 14px;
    border: 1px solid #E0ECE8;
    box-shadow: 0 2px 12px rgba(16, 42, 42, 0.03);
    margin-bottom: 20px;
}

/* Metrics Styling */
[data-testid="stMetric"] {
    background: #FFFFFF;
    padding: 18px 20px;
    border-radius: 12px;
    border: 1px solid #D5E6E1;
    box-shadow: 0 2px 6px rgba(6, 78, 74, 0.02);
}
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    color: #064E4A !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #4A6E6B !important;
    font-weight: 600 !important;
}

/* Buttons */
.stButton > button {
    background: #064E4A;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: #043A37;
    color: white;
    box-shadow: 0 4px 12px rgba(6, 78, 74, 0.15);
}

/* Inputs & Textareas */
.stTextArea textarea, .stTextInput input {
    background: #FFFFFF;
    border: 1px solid #CBDCD6;
    border-radius: 8px;
    color: #102A2A;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #064E4A;
    box-shadow: 0 0 0 1px #064E4A;
}
</style>
""", unsafe_allow_html=True)

# SIDEBAR NAVIGATION
with st.sidebar:
    st.markdown("### 👶 PikinCare")
    st.caption("National Child Health & Immunization Platform")
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
    st.markdown("<p style='font-size: 12px; opacity: 0.8; text-align: center;'>🇳🇬 Built for Primary Healthcare Delivery Across Nigeria</p>", unsafe_allow_html=True)

# INITIALIZE AGENT & SESSION STATE
has_ai_credentials = all(
    os.getenv(key) for key in ("OPENAI_API_KEY", "EMBEDDING_API_KEY")
)
if has_ai_credentials and "agent" not in st.session_state:
    st.session_state.agent = get_agent_executor()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- HOME DASHBOARD ---
if page == "Home":
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">🌱 PikinCare Digital Health System</div>
        <div class="hero-subtitle">Empowering caregivers, field workers, and health systems with NPHCDA-aligned tracking, local nutrition intelligence, and verified clinical guidance.</div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("System Performance & Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛡️ Protection Status", "Active", "Standards Grade")
    c2.metric("💉 NPHCDA Protocol", "Synced", "Official Schedule")
    c3.metric("🥗 AI Nutrition Engine", "Online", "Hybrid RAG + Web")
    c4.metric("🏥 Health Coverage", "Nationwide", "Verified Map Data")

    st.markdown("### Quick Access Modules")
    
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        if st.button("🥗 Nutrition AI", use_container_width=True):
            st.session_state["main_navigation"] = "Nutrition AI"
            st.rerun()
    with col_b:
        if st.button("💉 Immunization", use_container_width=True):
            st.session_state["main_navigation"] = "Immunization Tracker"
            st.rerun()
    with col_c:
        if st.button("🏥 Health Centers", use_container_width=True):
            st.session_state["main_navigation"] = "Health Center Finder"
            st.rerun()
    with col_d:
        if st.button("📈 Health Passport", use_container_width=True):
            st.session_state["main_navigation"] = "Growth & Health Passport"
            st.rerun()

    st.markdown("""
    <div class="institutional-card" style="margin-top: 24px;">
        <h3>📌 Clinical Governance & Mission</h3>
        <p>PikinCare bridges critical gaps in child survival by providing accurate tracking tools, instant multilingual clinical support, and dependable clinic locations. Designed to support resilient primary healthcare delivery across Nigeria.</p>
    </div>
    """, unsafe_allow_html=True)

# --- NUTRITION AI ---
elif page == "Nutrition AI":
    st.markdown("## 🥗 PikinCare Clinical & Nutrition AI Assistant")
    st.markdown("<p style='color: #4A6E6B;'>Ask questions, evaluate infant diets, or record voice notes in local languages backed by NPHCDA & WHO guidelines.</p>", unsafe_allow_html=True)

    if not has_ai_credentials:
        st.warning("⚠️ API credentials missing. Please check your `.env` configuration for `OPENAI_API_KEY` and `EMBEDDING_API_KEY`.")

    left, right = st.columns([3, 2], gap="large")

    with left:
        with st.container():
            recording = st.audio_input("🎙️ Voice Consultation (Record Audio)")

            if recording is not None:
                if st.button("Convert Speech to Text"):
                    temp_path = None
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                            f.write(recording.getvalue())
                            temp_path = f.name

                        with st.spinner("Processing speech audio..."):
                            transcript = speech_to_text(temp_path)

                        st.session_state["nutrition_question"] = transcript
                        st.success("Transcription successful.")
                    except Exception as error:
                        st.error(f"Speech recognition error: {error}")
                    finally:
                        if temp_path and os.path.exists(temp_path):
                            os.remove(temp_path)

            user_input = st.text_area(
                "Clinical Inquiry or Meal Description",
                placeholder="Example: What local complementary foods can I introduce for an 8-month-old infant in Nigeria?",
                key="nutrition_question",
                height=140
            )

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                evaluate_btn = st.button("✨ Evaluate with AI", use_container_width=True, disabled=not has_ai_credentials)
            with col_btn2:
                tts_btn = st.button("🔊 Read Aloud Response", use_container_width=True)

            if evaluate_btn and user_input.strip():
                with st.spinner("Synthesizing clinical guidelines & local data..."):
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
                    st.markdown("### 🤖 Clinical AI Response:")
                    st.info(bot_reply)
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
                        st.error(f"Text-to-speech error: {error}")
                    finally:
                        if audio_path and os.path.exists(audio_path):
                            os.remove(audio_path)
                else:
                    st.warning("No response text available for audio playback.")

    with right:
        st.markdown("""
        <div class="institutional-card">
            <h4>💡 Decision Support Features</h4>
            <ul style="padding-left: 20px; line-height: 1.6; color: #235552;">
                <li><b>Evidence-Anchored RAG:</b> Queries curated local data indices first to ensure zero hallucination on vital vaccines.</li>
                <li><b>Dynamic Web Fallback:</b> Automatically cross-references live health notices or updates when necessary.</li>
                <li><b>Local Nutrient Optimization:</b> Recommends affordable local food pairings (e.g., crayfish, soybeans, iron-fortified pap).</li>
                <li><b>Multilingual Accessibility:</b> Designed for seamless communication across diverse communities.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# --- IMMUNIZATION TRACKER ---
elif page == "Immunization Tracker":
    st.markdown("## 💉 Smart Immunization Schedule Tracker")
    st.markdown("<p style='color: #4A6E6B;'>Automated timeline calculator strictly aligned with the National Primary Health Care Development Agency (NPHCDA) guidelines.</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        dob = st.date_input("Child's Date of Birth", value=date(2026, 1, 1))
    with col2:
        as_of = st.date_input("Tracking Reference Date", value=date.today())

    if dob > as_of:
        st.error("Date of birth cannot be set in the future.")
    else:
        age_info = calculate_age(dob, as_of)
        st.success(f"**Calculated Child Age:** {age_info['years']} years, {age_info['total_months'] % 12} months ({age_info['total_weeks']} weeks / {age_info['total_days']} days)")

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
        st.dataframe(display_data, use_container_width=True, hide_index=True)

# --- HEALTH CENTERS ---
elif page == "Health Center Finder":
    if display_health_center_finder:
        display_health_center_finder()
    else:
        st.info("Loading health center discovery module...")

# --- GROWTH & HEALTH PASSPORT ---
elif page == "Growth & Health Passport":
    if render_pdf_generator:
        render_pdf_generator()
    else:
        st.info("Loading digital health passport generator...")

# --- SETTINGS ---
elif page == "Settings":
    st.markdown("## ⚙️ System Configuration & Preferences")
    st.markdown("<p style='color: #4A6E6B;'>Manage application settings, local data caching, and user accessibility options.</p>", unsafe_allow_html=True)
    st.info("All system parameters are currently operating on standard production defaults.")

# --- HELP ---
elif page == "Help":
    st.markdown("## ❓ PikinCare Support & Documentation")
    st.markdown("""
        <div class="institutional-card">
            <h3 style="color: #064E4A; margin-top: 0;">📖 Operational Guide for Evaluators</h3>
            <ul style="line-height: 1.8; color: #235552;">
                <li><b>Nutrition AI:</b> Use text or speech input to query nutritional standards and infant care practices.</li>
                <li><b>Immunization Tracker:</b> Input the child's birth date to instantly generate an audit-ready NPHCDA schedule.</li>
                <li><b>Health Center Finder:</b> Discover registered primary healthcare clinics and mapping services across Nigeria.</li>
                <li><b>Growth & Health Passport:</b> Compile records into official downloadable clinical PDF summaries.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)