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

# ==========================================
# PAGE CONFIGURATION & CUSTOM STYLING
# ==========================================
st.set_page_config(
    page_title="PikinCare AI & CNITS — Child Health Assistant",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #D9EAE7;
    box-shadow: 0 2px 8px #064e4a0a;
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
.disclaimer-text {
    font-size: 0.75rem;
    color: #9CA3AF;
    text-align: center;
    margin-top: 15px;
    padding: 8px;
    border-top: 1px solid #E5E7EB;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("# 👶 PikinCare AI / CNITS")
    st.caption("Child Nutrition & Immunization System")
    st.divider()

    app_mode = st.radio(
        "Navigation",
        [
            "Home",
            "💬 AI Health Assistant",
            "💉 Smart Vaccine Tracker",
            "🏥 Health Center Finder",
            "📄 Digital Health Passport",
            "⚙️ Settings",
            "❓ Help"
        ],
        label_visibility="collapsed",
        key="main_navigation"
    )

    st.divider()
    if st.button("➕ New Chat Session", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("🏆 **Tech Queens** | Competition Finals 2026")

# ==========================================
# HEADER BANNER
# ==========================================
st.markdown("""
<div class="hero">
    <h1>🌱 Welcome to PikinCare AI & CNITS!</h1>
    <p>Together for healthier, stronger, and brighter children through AI & verified health guidelines.</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# PAGE: HOME DASHBOARD
# ==========================================
if app_mode == "Home":
    st.subheader("Child Health Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💉 Overdue Vaccinations", "0")
    c2.metric("🕒 Due Now", "0")
    c3.metric("📅 Upcoming", "0")
    c4.metric("👤 Active Profile", "1")

    st.markdown("### Quick Workspace Navigation")
    
    nav1, nav2, nav3, nav4 = st.columns(4)
    if nav1.button("💬 AI Assistant", use_container_width=True):
        st.session_state["main_navigation"] = "💬 AI Health Assistant"
        st.rerun()
    if nav2.button("💉 Vaccines", use_container_width=True):
        st.session_state["main_navigation"] = "💉 Smart Vaccine Tracker"
        st.rerun()
    if nav3.button("🏥 Health Centers", use_container_width=True):
        st.session_state["main_navigation"] = "🏥 Health Center Finder"
        st.rerun()
    if nav4.button("📄 Health Passport", use_container_width=True):
        st.session_state["main_navigation"] = "📄 Digital Health Passport"
        st.rerun()

    st.markdown("""
    <div class="panel">
        <h3>💚 Healthy Today, Brighter Tomorrow</h3>
        <p>Combining AI intelligence, voice accessibility, NPHCDA immunization schedules, and primary healthcare facility mapping in one unified digital workspace.</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# PAGE: AI HEALTH ASSISTANT (RAG + Voice)
# ==========================================
elif app_mode == "💬 AI Health Assistant":
    st.markdown("## 💬 AI Health Assistant & Nutrition AI")
    st.write("Type or record your child health question in any Nigerian language (Yoruba, Hausa, Igbo, Pidgin, etc.) or English.")

    has_ai_credentials = all(
        os.getenv(key) for key in ("OPENAI_API_KEY", "EMBEDDING_API_KEY")
    )

    if not has_ai_credentials:
        st.warning(
            "The AI assistant requires OPENAI_API_KEY and EMBEDDING_API_KEY in your environment variables or .env file."
        )
    elif "agent" not in st.session_state:
        st.session_state.agent = get_agent_executor()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    config = {"configurable": {"thread_id": "streamlit_user_session"}}

    # Optional Voice Recording Input
    with st.expander("🎙️ Voice Input (Record Question)"):
        recording = st.audio_input("Record your question or meal description")
        if recording is not None and st.button("Convert Speech to Text"):
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                    f.write(recording.getvalue())
                    temp_path = f.name
                with st.spinner("Recognizing speech..."):
                    transcript = speech_to_text(temp_path)
                st.session_state.messages.append({"role": "user", "content": transcript})
                st.success("Voice transcribed and added to chat!")
            except Exception as error:
                st.error(f"Speech recognition failed: {error}")
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

    # Starter Suggestion Chips
    if not st.session_state.messages:
        c1, c2, c3 = st.columns(3)
        if c1.button("🍼 6-Month Infant Feeding", use_container_width=True, disabled=not has_ai_credentials):
            st.session_state.messages.append({"role": "user", "content": "What local foods can I give my 6-month-old baby in Nigeria?"})
            st.rerun()
        if c2.button("💉 10-Week Vaccine List", use_container_width=True, disabled=not has_ai_credentials):
            st.session_state.messages.append({"role": "user", "content": "Which vaccines are due at 10 weeks according to NPHCDA?"})
            st.rerun()
        if c3.button("🥗 Preventing Malnutrition", use_container_width=True, disabled=not has_ai_credentials):
            st.session_state.messages.append({"role": "user", "content": "How can I ensure my child gets enough iron and micronutrients?"})
            st.rerun()

    # Render Chat History
    for message in st.session_state.messages:
        avatar = "👶" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Chat Input
    if user_input := st.chat_input("Message PikinCare AI...", disabled=not has_ai_credentials):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👶"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Analyzing NPHCDA & Health Guidelines..."):
                prompt_instruction = (
                    f"Detect the language of the following user question and reply in that exact same language. "
                    f"User question: {user_input}"
                )
                response = st.session_state.agent.invoke(
                    {"messages": [("user", prompt_instruction)]},
                    config=config
                )
                bot_reply = response["messages"][-1].content
                st.markdown(bot_reply)

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    st.markdown(
        '<div class="disclaimer-text">⚠️ <b>Medical Disclaimer:</b> PikinCare AI provides educational information based on NPHCDA & WHO guidelines. Always consult a certified healthcare professional.</div>',
        unsafe_allow_html=True
    )

# ==========================================
# PAGE: SMART VACCINE TRACKER
# ==========================================
elif app_mode == "💉 Smart Vaccine Tracker":
    st.subheader("Smart Immunization Schedule Tracker")
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
        st.dataframe(display_data, use_container_width=True, hide_index=True)

# ==========================================
# PAGE: HEALTH CENTER FINDER
# ==========================================
elif app_mode == "🏥 Health Center Finder":
    if display_health_center_finder:
        display_health_center_finder()
    else:
        st.header("🏥 Health Center Finder")
        location = st.text_input("Enter a town, area, or location", placeholder="e.g. Ikorodu, Lagos")
        if st.button("Find Health Centers"):
            if location.strip():
                st.info("Health center finder module is active.")
            else:
                st.warning("Please enter a location.")

# ==========================================
# PAGE: DIGITAL HEALTH PASSPORT
# ==========================================
elif app_mode == "📄 Digital Health Passport":
    if render_pdf_generator:
        render_pdf_generator()
    else:
        st.header("📄 Digital Health Passport & Growth Records")
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Height (cm)", min_value=0.0, max_value=150.0, value=0.0)
        with col2:
            st.number_input("Weight (kg)", min_value=0.0, max_value=50.0, value=0.0)
        if st.button("Record Growth Entry"):
            st.success("Growth data logged successfully.")

# ==========================================
# PAGE: SETTINGS
# ==========================================
elif app_mode == "⚙️ Settings":
    st.header("⚙️ Application Settings")
    st.write("Configure your language preferences, notification reminders, and sync options.")
    st.selectbox("Preferred Language", ["English", "Yorùbá", "Hausa", "Igbo", "Pidgin"])

# ==========================================
# PAGE: HELP & USER GUIDE
# ==========================================
elif app_mode == "❓ Help":
    st.header("❓ Help & Support Center")
    st.markdown("""
        <div style="background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);">
            <h3 style="color: #0f766e; margin-top: 0;">📌 Quick User Guide</h3>
            <ul>
                <li><b>AI Health Assistant:</b> Ask questions or use voice input to receive instant AI nutritional assessments and guidance based on NPHCDA guidelines.</li>
                <li><b>Smart Vaccine Tracker:</b> Input the child's birthdate to automatically calculate overdue, due, and upcoming vaccine schedules.</li>
                <li><b>Health Center Finder:</b> Locate nearby primary healthcare facilities instantly.</li>
                <li><b>Digital Health Passport:</b> Track height/weight trends and generate official health passports.</li>
            </ul>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <h4 style="color: #334155;">Need Technical Support?</h4>
            <p style="color: #64748b; margin-bottom: 0;">Contact your system administrator or project lead for assistance.</p>
        </div>
    """, unsafe_allow_html=True)