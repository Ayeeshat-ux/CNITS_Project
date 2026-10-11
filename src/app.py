import streamlit as st
import os
import tempfile
from speech_engine import speech_to_text, text_to_speech

st.set_page_config(
        page_title="CNTIS - Child Nutrition & Immunization Tracking System",
        page_icon="👶",
        layout ="wide",
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

# HOME DASHBOARD
if page == "Home":
    st.subheader("Child Health Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💉 Overdue Vaccinations", "0")
    c2.metric("🕒 Due Now", "0")
    c3.metric("📅 Upcoming", "0")
    c4.metric("👤 Total Records", "0")

    st.markdown("### Your CNITS Workspace")
    st.caption("Choose a feature below to continue.")

    nav1, nav2, nav3, nav4 = st.columns(4)

    if nav1.button("🥗 Nutrition AI", use_container_width=True):
        st.session_state["main_navigation"] = "Nutrition AI"
        st.rerun()

    if nav2.button("💉 Immunization", use_container_width=True):
        st.session_state["main_navigation"] = "Immunization Tracker"
        st.rerun()

    if nav3.button("🏥 Health Centers", use_container_width=True):
        st.session_state["main_navigation"] = "Health Center Finder"
        st.rerun()

    if nav4.button("📈 Growth Passport", use_container_width=True):
        st.session_state["main_navigation"] = "Growth & Health Passport"
        st.rerun()

    st.markdown("""
    <div class="panel">
        <h3>💚 Healthy Today, Brighter Tomorrow</h3>
        <p>CNITS brings child nutrition, immunization and health
        record support into one digital workspace.</p>
        <p class="small-note">Designed to support caregivers,
        healthcare professionals and other authorized users.</p>
    </div>
    """, unsafe_allow_html=True)

# NUTRITION AI
elif page == "Nutrition AI":
    st.markdown("## 🥗 Nutrition AI")
    st.write("Ask a nutrition question or describe a child's meal.")

    left, right = st.columns([3, 2], gap="large")

    with left:
        child_age = st.number_input(
            "Child's age (months)",
            min_value=0,
            max_value=59,
            value=12,
            key="nutrition_age"
        )

        recording = st.audio_input("🎙️ Record your question")

        if recording is not None:
            if st.button("Convert Speech to Text"):
                temp_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".wav"
                    ) as f:
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

        question = st.text_area(
            "Your question or meal description",
            placeholder="Example: My child ate rice, beans and egg.",
            key="nutrition_question",
            height=130
        )

        if st.button("✨ Evaluate Meal", use_container_width=True):
            if question.strip():
                st.info(
                    "Your input is ready. Connect the nutrition "
                    "analysis module to generate advice."
                )
            else:
                st.warning("Enter a question or record your voice.")

        if st.button("🔊 Read Question Aloud", use_container_width=True):
            if question.strip():
                audio_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".mp3"
                    ) as f:
                        audio_path = f.name

                    text_to_speech(question, audio_path)

                    with open(audio_path, "rb") as f:
                        st.audio(f.read(), format="audio/mp3")
                except Exception as error:
                    st.error(f"Text-to-speech failed: {error}")
                finally:
                    if audio_path and os.path.exists(audio_path):
                        os.remove(audio_path)
            else:
                st.warning("Enter or record text first.")

    with right:
        st.markdown("""
        <div class="panel">
            <h3>👶 Get Nutrition Support</h3>
            <p>CNITS nutrition guidance can help users:</p>
            <p>✓ Review meal information</p>
            <p>✓ Identify possible nutrient gaps</p>
            <p>✓ Explore practical feeding guidance</p>
            <p>✓ Interact through voice or text</p>
            <hr>
            <p class="small-note">
            Nutrition recommendations will appear here after
            the nutrition module is connected.
            </p>
        </div>
        """, unsafe_allow_html=True)

# IMMUNIZATION
elif page == "Immunization Tracker":
    st.header("💉 Immunization Tracker & Reminders")
    birth_date = st.date_input("Child's date of birth")
    st.info(
        "The vaccine schedule and reminders will be connected "
        "to the immunization module and approved guidelines."
    )

# HEALTH CENTERS
elif page == "Health Center Finder":
    st.header("🏥 Health Center Finder")
    location = st.text_input(
        "Enter a town, area or location",
        placeholder="e.g. Ikorodu, Lagos"
    )
    if st.button("Find Health Centers"):
        if location.strip():
            st.info("Connect the health_center.py module to find facilities.")
        else:
            st.warning("Enter a location first.")

# GROWTH PASSPORT
elif page == "Growth & Health Passport":
    st.header("📈 Growth & Health Passport")
    col1, col2 = st.columns(2)

    with col1:
        height = st.number_input(
            "Height (cm)", min_value=0.0, max_value=150.0, value=0.0
        )

    with col2:
        weight = st.number_input(
            "Weight (kg)", min_value=0.0, max_value=50.0, value=0.0
        )

    if st.button("Record Growth"):
        st.info("Connect the growth-record storage module to save this entry.")

    st.subheader("Growth History")
    st.info("Growth charts and PDF health passports will appear here.")

# SETTINGS
elif page == "Settings":
    st.header("⚙️ Settings")
    st.write("Language preferences and user settings can be added here.")

# HELP
elif page == "Help":
    st.header("❓ Help & Support Center")
    st.write("Instructions and support information can be added here.")
    st.markdown("""
        <div style="background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);">
            <h3 style="color: #0f766e; margin-top: 0;">📌 Quick User Guide</h3>
            <ul>
                <li><b>Nutrition AI (Tab 1):</b> Enter a child's age and type (or record) a meal description to get instant AI nutritional assessments and audio feedback.</li>
                <li><b>Immunization Tracker (Tab 2):</b> Input the child's birthdate to automatically calculate overdue, due, and upcoming vaccine schedules according to NPHCDA guidelines.</li>
                <li><b>Health Center Finder (Tab 3):</b> Locate nearby primary healthcare facilities instantly.</li>
                <li><b>Growth & Health Passport (Tab 4):</b> Track height and weight trends against WHO standards and generate official health passports.</li>
            </ul>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <h4 style="color: #334155;">Need Technical Support?</h4>
            <p style="color: #64748b; margin-bottom: 0;">Contact the UI & Voice Accessibility Lead (Tiamiyu Abimbola Alimot) or your system administrator for assistance.</p>
        </div>
""", unsafe_allow_html=True)
