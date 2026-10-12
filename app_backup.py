from datetime import date, datetime
import json
import base64
import os
import tempfile
from pathlib import Path

import streamlit as st

# CNITS modules from the existing project
try:
    from src.rag_engine import get_agent_executor
except Exception:
    get_agent_executor = None

try:
    from src.vaccine_tracker import (
        build_vaccine_schedule,
        calculate_age,
        group_vaccines_by_status,
    )
except Exception:
    build_vaccine_schedule = calculate_age = group_vaccines_by_status = None

try:
    from src.health_center import display_health_center_finder
except Exception:
    display_health_center_finder = None

try:
    from src.pdf_generator import render_pdf_generator
except Exception:
    render_pdf_generator = None

try:
    from src.speech_engine import speech_to_text, text_to_speech
except Exception:
    speech_to_text = text_to_speech = None


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
DATA_DIR = ROOT / "data"
MEMORY_FILE = DATA_DIR / "cnits_recent_activity.json"
SUPPORTED_ATTACHMENTS = {"pdf", "txt", "csv", "md", "docx"}


def image_data_uri(filename):
    """Return a local image as a data URI, or an empty string if unavailable."""
    path = ASSETS / filename
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def init_state():
    defaults = {
        "cnits_page": "Home",
        "nutrition_messages": [],
        "home_meal_answer": "",
        "vaccine_summary": None,
        "growth_records": [],
        "agent_instance": None,
        "agent_error": "",
        "recent_activity": None,
        "active_chat_id": None,
        "attached_context": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_recent_activity():
    """Load locally stored recent activity; creates an empty list when absent."""
    if st.session_state.recent_activity is not None:
        return st.session_state.recent_activity
    try:
        if MEMORY_FILE.exists():
            data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            st.session_state.recent_activity = data if isinstance(data, list) else []
        else:
            st.session_state.recent_activity = []
    except (OSError, json.JSONDecodeError):
        st.session_state.recent_activity = []
    return st.session_state.recent_activity


def save_recent_activity(title, messages, kind="Nutrition chat"):
    """Keep a small local history of recent chats or file attachments."""
    history = load_recent_activity()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    item = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "title": (title or kind)[:90],
        "kind": kind,
        "updated_at": now,
        "messages": messages[-30:],
    }
    history.insert(0, item)
    st.session_state.recent_activity = history[:15]
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        MEMORY_FILE.write_text(json.dumps(st.session_state.recent_activity, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        st.session_state.memory_save_error = str(exc)
    st.session_state.active_chat_id = item["id"]


def extract_attachment_text(uploaded_file):
    """Extract readable text from supported uploads without storing the original file."""
    name = uploaded_file.name
    ext = Path(name).suffix.lower().lstrip(".")
    raw = uploaded_file.getvalue()
    if ext in {"txt", "md", "csv"}:
        return raw.decode("utf-8", errors="replace")[:30000]
    if ext == "pdf":
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(raw))
            return "\n".join(page.extract_text() or "" for page in reader.pages)[:30000]
        except ImportError:
            return "PDF text extraction needs pypdf. Install it with: pip install pypdf"
        except Exception as exc:
            return f"Could not read this PDF: {exc}"
    if ext == "docx":
        try:
            from docx import Document
            import io
            document = Document(io.BytesIO(raw))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)[:30000]
        except ImportError:
            return "Word document extraction needs python-docx. Install it with: pip install python-docx"
        except Exception as exc:
            return f"Could not read this Word document: {exc}"
    return "This file type is not supported. Upload PDF, TXT, CSV, Markdown or DOCX."


def render_recent_activity():
    history = load_recent_activity()
    with st.sidebar.expander(f"🕘 Recent activity ({len(history)})", expanded=False):
        if not history:
            st.caption("Your recent chats and attachments will appear here.")
        for item in history[:10]:
            st.caption(f"{item.get('updated_at', '')} · {item.get('kind', 'Activity')}")
            if st.button(f"📄 {item.get('title', 'Untitled')[:42]}", key=f"recent_{item.get('id', '')}", use_container_width=True):
                st.session_state.nutrition_messages = item.get("messages", [])
                st.session_state.cnits_page = "Nutrition AI"
                st.rerun()
        if history and st.button("Clear recent activity", key="clear_recent_activity"):
            st.session_state.recent_activity = []
            try:
                if MEMORY_FILE.exists():
                    MEMORY_FILE.unlink()
            except OSError:
                pass
            st.rerun()

def get_agent():
    if st.session_state.agent_instance is not None:
        return st.session_state.agent_instance
    if get_agent_executor is None:
        st.session_state.agent_error = "src.rag_engine could not be imported."
        return None
    try:
        st.session_state.agent_instance = get_agent_executor()
        st.session_state.agent_error = ""
        return st.session_state.agent_instance
    except Exception as exc:
        st.session_state.agent_error = str(exc)
        return None


def ask_cnits(question):
    agent = get_agent()
    if agent is None:
        return (
            "The Nutrition AI is not connected yet. Check your RAG configuration, "
            "API keys and source documents. "
            + st.session_state.get("agent_error", "")
        )
    prompt = (
        "Answer the user's child nutrition or immunization question using the "
        "available trusted source documents. Match the language used by the user "
        "when possible. Do not diagnose or prescribe treatment. If the source "
        "documents do not contain the answer, say that clearly.\n\n"
        f"User question: {question}"
    )
    response = agent.invoke(
        {"messages": [("user", prompt)]},
        config={"configurable": {"thread_id": "cnits_streamlit_session"}},
    )
    messages = response.get("messages", [])
    if not messages:
        return "I could not produce a response from the connected assistant."
    content = getattr(messages[-1], "content", messages[-1])
    return content if isinstance(content, str) else str(content)


def show_disclaimer():
    st.markdown(
        '<div class="cnits-disclaimer">⚠️ <b>Medical disclaimer:</b> CNITS provides '
        'educational information and tracking support. It does not replace medical '
        'advice, diagnosis or treatment from a qualified healthcare professional. '
        'For urgent concerns, contact a healthcare professional or health facility.</div>',
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="CNITS | Child Nutrition & Immunization Tracking System",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_state()

# Responsive CNITS styling
st.markdown(
    r"""
<style>
:root {
    --teal: #087F79;
    --deep-teal: #004B48;
    --ink: #0A4648;
    --blue: #254D78;
    --line: #D5E5F4;
    --page: #F8FBFC;
}
.stApp {
    background: var(--page);
    color: var(--ink);
    overflow-x: hidden;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #087F79, #04524E);
}
[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}
.cnits-hero {
    position: relative;
    isolation: isolate;
    overflow: hidden;
    min-height: 100px;
    margin-bottom: 12px;
    padding: 14px 20px;
    border: 1px solid #DCEFE9;
    border-radius: 13px;
    background: linear-gradient(105deg, #F1FAF8, #E5F7F1 55%, #D3F1E6);
}
.cnits-hero h1 {
    color: #07494A;
    font-size: 1.8rem;
}
.cnits-stat {
    min-width: 0;
    min-height: 85px;
    padding: 9px 10px;
    border: 1px solid #D6E6F3;
    border-radius: 10px;
    background: white;
    box-shadow: 0 3px 12px rgba(10, 70, 80, .025);
}
.cnits-stat .label {
    font-size: .78rem;
    color: #244E68;
}
.cnits-stat .value {
    font-size: 1.4rem;
    font-weight: 750;
}
.cnits-stat .hint {
    font-size: .7rem;
    color: #355D75;
}
.cnits-panel, .cnits-sidepanel {
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 12px;
    background: white;
}
.cnits-sidepanel {
    text-align: center;
}
.stButton > button {
    width: 100%;
    border-radius: 9px;
    font-weight: 600;
}
.stButton > button[kind="primary"] {
    background: var(--teal);
    color: white;
}
.cnits-disclaimer {
    color: #607C80;
    font-size: .75rem;
    text-align: center;
    border-top: 1px solid #D8E7E9;
    margin-top: 12px;
    padding-top: 8px;
}
</style>
""",
    unsafe_allow_html=True,
)

# Sidebar navigation
pages = [
    "Home",
    "Nutrition AI",
    "Immunization Tracker",
    "Health Center Finder",
    "Growth & Health Passport",
    "Settings",
    "Help",
]
with st.sidebar:
    logo_uri = image_data_uri("cnits_logo.png")
    if logo_uri:
        st.image(logo_uri, width=62)
    st.markdown("# CNITS")
    st.caption("Child Nutrition & Immunization Tracking System")
    st.divider()
    page = st.radio(
        "Navigation",
        pages,
        key="cnits_page",
        label_visibility="collapsed",
        format_func=lambda item: {
            "Home": "⌂   Home",
            "Nutrition AI": "🍴   Nutrition AI",
            "Immunization Tracker": "💉   Immunization Tracker",
            "Health Center Finder": "📍   Health Center Finder",
            "Growth & Health Passport": "📈   Growth & Health Passport",
            "Settings": "⚙️   Settings",
            "Help": "❔   Help",
        }[item],
    )
    st.divider()
    mother_uri = image_data_uri("sidebar_mother_child_illustration.png")
    if mother_uri:
        st.image(mother_uri, use_container_width=True)
    st.markdown("**Healthy Children, Brighter Futures**")
    st.caption("Nutrition • Immunization • Child Health")
    render_recent_activity()

# Welcome banner
baby_uri = image_data_uri("hero_baby_illustration.png")
baby_html = f'<img class="baby" src="{baby_uri}" alt="Smiling baby illustration" style="position:absolute; right:3%; bottom:12px; width:200px; max-height:120px; object-fit:contain;">' if baby_uri else ""
st.markdown(
    f'<div class="cnits-hero"><span style="font-size:2.0rem;">🌱</span>'
    f'<h1 style="display:inline; font-size:1.6rem;">Welcome to CNITS!</h1>'
    f'<p style="margin:5px 0 0 35px; font-size:.9rem;">Together for healthier, stronger and brighter children.</p>{baby_html}</div>',
    unsafe_allow_html=True,
)

if page == "Home":
    st.subheader("Child Health Overview")
    summary = st.session_state.vaccine_summary or {}
    total_records = len(st.session_state.growth_records)
    cards = [
        ("💉", "Overdue Vaccinations", summary.get("overdue", 0), "Keep your child protected", "#FFF0F2", "#8E0A1B"),
        ("◷", "Due Now", summary.get("due_now", 0), "Stay on schedule", "#FFF6E7", "#4E3004"),
        ("▦", "Upcoming", summary.get("upcoming", 0), "Plan ahead", "#E9F9F0", "#024222"),
        ("♟", "Total Records", total_records, "Growing healthier", "#EDF7FF", "#053463"),
    ]
    columns = st.columns(4, gap="small")
    for col, (icon, label, value, hint, tint, color) in zip(columns, cards):
        with col:
            st.markdown(
                f'<div class="cnits-stat" style="background:linear-gradient(135deg,#FFFFFF,{tint})">'
                f'<div class="label">{icon} &nbsp; {label}</div>'
                f'<div class="value" style="color:{color}">{value}</div>'
                f'<div class="hint">{hint}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("")
    workspace, side = st.columns([4, 1], gap="small")
    with workspace:
        tabs = st.tabs(["🍴 Nutrition AI", "💉 Immunization Tracker", "📍 Health Center Finder", "📈 Growth & Health Passport"])
        with tabs[0]:
            c_left, c_right = st.columns([1.2, .8], gap="small")
            with c_left:
                st.markdown("### 🥗 Nutrition AI")
                st.caption("Analyze meals and get child nutrition guidance.")
                age = st.number_input("Child's age (months)", min_value=0, max_value=59, value=12, key="home_child_age")
                meal = st.text_area("Enter the child's meal", placeholder="e.g. Rice, beans, egg, vegetables...", height=90, key="home_meal")
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("✨ Evaluate Meal", type="primary", use_container_width=True):
                        if meal.strip():
                            with st.spinner("Checking available nutrition guidance..."):
                                try:
                                    st.session_state.home_meal_answer = ask_cnits(
                                        f"My child is {age} months old. Assess this meal: {meal}"
                                    )
                                except Exception as exc:
                                    st.session_state.home_meal_answer = f"Unable to get a response: {exc}"
                        else:
                            st.warning("Enter the meal before evaluating it.")
                with b2:
                    recording = st.audio_input("🎙️ Speak instead", key="home_meal_audio")
                    if recording and st.button("Transcribe & ask", key="home_transcribe", use_container_width=True):
                        if speech_to_text is None:
                            st.warning("Speech support is unavailable.")
                        else:
                            audio_path = None
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                                    tmp.write(recording.getvalue())
                                    audio_path = tmp.name
                                transcript = speech_to_text(audio_path)
                                if transcript:
                                    st.session_state.home_meal = transcript
                                    st.session_state.home_meal_answer = ask_cnits(f"My child is {age} months old. Question: {transcript}")
                            finally:
                                if audio_path and os.path.exists(audio_path):
                                    os.remove(audio_path)
                if st.session_state.home_meal_answer:
                    st.markdown("**Nutrition guidance**")
                    st.write(st.session_state.home_meal_answer)
            with c_right:
                st.markdown(
                    '<div class="cnits-panel" style="background:linear-gradient(145deg,#F0FBF8,#E5F7F1);">'
                    '<h3>Get AI-powered nutrition advice</h3>'
                    '<p>✓ Analyzes meal nutrition</p><p>✓ Identifies possible nutrient gaps</p>'
                    '<p>✓ Gives simple, actionable tips</p></div>',
                    unsafe_allow_html=True,
                )
        with tabs[1]:
            st.markdown("### Smart Immunization Tracker")
            if st.button("Open Immunization Tracker", key="home_open_vaccine"):
                st.session_state.cnits_page = "Immunization Tracker"
                st.rerun()
        with tabs[2]:
            st.markdown("### Health Center Finder")
            if st.button("Open Health Center Finder", key="home_open_centers"):
                st.session_state.cnits_page = "Health Center Finder"
                st.rerun()
        with tabs[3]:
            st.markdown("### Growth & Health Passport")
            if st.button("Open Growth Passport", key="home_open_growth"):
                st.session_state.cnits_page = "Growth & Health Passport"
                st.rerun()
    with side:
        hands_uri = image_data_uri("health_hands_heart_illustration.png")
        if hands_uri:
            st.image(hands_uri, use_container_width=True)
        st.markdown(
            '<div class="cnits-sidepanel"><div style="font-size:2rem;">💚</div>'
            '<h3>Healthy Today,<br>Brighter Tomorrow</h3>'
            '<p>CNITS helps you track your child’s nutrition and health records.</p></div>',
            unsafe_allow_html=True,
        )
    show_disclaimer()

elif page == "Nutrition AI":
    st.header("🥗 Nutrition AI")
    st.write("Ask about child feeding and nutrition by text or voice.")
    age = st.number_input("Child's age (months)", min_value=0, max_value=59, value=12, key="nutrition_age")
    
    for message in st.session_state.nutrition_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    text_question = st.chat_input("Ask about feeding, nutrition or child health...")
    if text_question:
        st.session_state.nutrition_messages.append({"role": "user", "content": text_question})
        with st.chat_message("user"):
            st.markdown(text_question)
        with st.chat_message("assistant"):
            answer = ask_cnits(f"Child age: {age} months. Question: {text_question}")
            st.markdown(answer)
        st.session_state.nutrition_messages.append({"role": "assistant", "content": answer})
    show_disclaimer()

elif page == "Immunization Tracker":
    st.header("💉 Smart Immunization Schedule Tracker")
    st.write("Calculate the child's vaccination timeline from their date of birth.")
    if not all([build_vaccine_schedule, calculate_age, group_vaccines_by_status]):
        st.error("The vaccine tracker module could not be imported.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            dob = st.date_input("Child's date of birth", value=date(2026, 1, 1), max_value=date.today(), key="tracker_dob")
        with col2:
            as_of = st.date_input("Tracking reference date", value=date.today(), key="tracker_as_of")
        if dob > as_of:
            st.error("Date of birth cannot be after the reference date.")
        else:
            age_info = calculate_age(dob, as_of)
            st.info(f"**Current age:** {age_info['years']} years, {age_info['total_months'] % 12} months")
            records = build_vaccine_schedule(dob, as_of=as_of)
            grouped = group_vaccines_by_status(records)
            summary = {
                "overdue": len(grouped.get("overdue", [])),
                "due_now": len(grouped.get("due_now", [])),
                "upcoming": len(grouped.get("upcoming", [])),
                "completed": len(grouped.get("completed", [])),
            }
            st.session_state.vaccine_summary = summary
            cols = st.columns(4)
            for col, label, key in zip(cols, ["Overdue", "Due Now", "Upcoming", "Completed"], ["overdue", "due_now", "upcoming", "completed"]):
                col.metric(label, summary[key])
            st.dataframe(
                [{
                    "Vaccine": r.get("vaccine", ""),
                    "Milestone": r.get("target_age_label", ""),
                    "Due Date": r.get("due_date_label", ""),
                    "Status": r.get("status", ""),
                    "Dosage": r.get("dosage", ""),
                    "Route": r.get("route", ""),
                    "Site": r.get("site", ""),
                } for r in records],
                use_container_width=True,
                hide_index=True
            )

elif page == "Health Center Finder":
    if display_health_center_finder:
        display_health_center_finder()
    else:
        st.info("Health center finder module loading...")

elif page == "Growth & Health Passport":
    if render_pdf_generator:
        render_pdf_generator()
    else:
        st.info("PDF generator module loading...")

elif page == "Settings":
    st.header("⚙️ Settings")
    st.write("Manage app configuration and preferences.")

elif page == "Help":
    st.header("❔ Help & Support")
    st.write("Refer to the user guide or reach out to healthcare support teams.")