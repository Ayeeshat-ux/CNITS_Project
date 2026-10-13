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
    page_title="PikinCare | National Child Health Platform",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# MODERN UI/UX & STYLING
# ============================================================
st.markdown("""
<style>
/* Main App Surface */
.stApp {
    background: #F8FBFA;
    color: #102A2A;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Sidebar Gradient */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #023330 0%, #064E4A 100%);
    border-right: 1px solid #085D57;
}
[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3, 
[data-testid="stSidebar"] h4, 
[data-testid="stSidebar"] label, 
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] summary {
    background-color: rgba(255, 255, 255, 0.12) !important;
    color: #FFFFFF !important;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Sidebar Brand Header */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 22px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 2px;
}
.sidebar-brand-icon {
    font-size: 30px;
}

/* Sidebar Disclaimer */
.sidebar-disclaimer {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.75);
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    padding-top: 12px;
    margin-top: 20px;
    line-height: 1.4;
}

/* Gemini Chat Disclaimer Footer */
.gemini-footer-disclaimer {
    text-align: center;
    font-size: 11px;
    color: #5C7A77;
    margin-top: 8px;
    margin-bottom: 4px;
}

/* Custom Primary Buttons */
.stButton > button {
    background: #064E4A;
    color: white !important;
    border: none;
    border-radius: 20px;
    padding: 6px 14px;
    font-weight: 600;
}
.stButton > button:hover {
    background: #043A37;
    color: white !important;
}

/* Popover (+) button styling */
[data-testid="stPopover"] button {
    background: #E2ECE9 !important;
    border: none !important;
    border-radius: 50% !important;
    width: 40px !important;
    height: 40px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 18px !important;
    color: #064E4A !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_name" not in st.session_state:
    st.session_state.user_name = "Guest Parent"
if "session_id" not in st.session_state:
    st.session_state.session_id = "pikincare_session_1"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Hello! I am your **PikinCare Nutrition & Child Health Assistant**. How can I help you and your child today with healthy meal plans, immunization schedules, or healthcare guidelines?"
        }
    ]

# Recent Chat History Tracking
if "recent_chats" not in st.session_state:
    st.session_state.recent_chats = [
        "👶 Child malaria care guidelines",
        "💉 Routine immunization schedule",
        "🥗 Balanced nutrition for children & toddlers"
    ]

# Initialize Agent
has_ai_credentials = all(os.getenv(key) for key in ("OPENAI_API_KEY", "EMBEDDING_API_KEY"))
if has_ai_credentials and "agent" not in st.session_state:
    st.session_state.agent = get_agent_executor()


# ============================================================
# SIGN IN / AUTHENTICATION MODAL DIALOG
# ============================================================
@st.dialog("🔐 Sign In to PikinCare")
def show_login_dialog():
    st.markdown("Access personalized growth tracking and saved child health records.")
    
    tab_login, tab_signup = st.tabs(["🔑 Sign In", "📝 Create Account"])
    
    with tab_login:
        email = st.text_input("📧 Email Address", key="login_email")
        password = st.text_input("🔒 Password", type="password", key="login_pass")
        if st.button("Sign In ➔", use_container_width=True, key="btn_login_submit"):
            if email:
                st.session_state.user_name = email.split("@")[0].capitalize()
                st.session_state.authenticated = True
                st.toast(f"Welcome back, {st.session_state.user_name}!", icon="🎉")
                st.rerun()
            else:
                st.error("Please enter a valid email.")

    with tab_signup:
        full_name = st.text_input("👤 Full Name", key="signup_name")
        signup_email = st.text_input("📧 Email Address", key="signup_email")
        signup_pass = st.text_input("🔒 Password", type="password", key="signup_pass")
        if st.button("Create Account ✨", use_container_width=True, key="btn_signup_submit"):
            if full_name and signup_email:
                st.session_state.user_name = full_name
                st.session_state.authenticated = True
                st.toast("Account created successfully!", icon="✅")
                st.rerun()
            else:
                st.error("Please fill in all details.")


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
with st.sidebar:
    # 1. BRAND HEADER WITH CHILD ICON
    st.markdown("""
    <div class="sidebar-brand">
        <span class="sidebar-brand-icon">👶</span>
        <span>PikinCare</span>
    </div>
    """, unsafe_allow_html=True)
    st.caption("🇳🇬 National Child Health Platform")
    st.divider()

    # 2. NAVIGATION TABS WITH ICONS
    page = st.radio(
        "Navigation",
        [
            "🥗 Nutrition & AI Assistant",
            "💉 Immunization Tracker",
            "🏥 Health Center Finder",
            "📈 Growth & Health Passport"
        ],
        label_visibility="collapsed",
        key="main_navigation"
    )

    st.divider()

    # 3. INTERACTIVE & DELETABLE RECENT CONVERSATIONS SECTION
    with st.expander("🕒 Recent Conversations", expanded=True):
        if st.session_state.recent_chats:
            # Iterate over a copy to safely handle deletions
            for idx, chat_title in enumerate(list(st.session_state.recent_chats)):
                c_load, c_del = st.columns([5, 1], gap="small")
                with c_load:
                    if st.button(chat_title, key=f"load_chat_{idx}", use_container_width=True):
                        st.toast(f"Loaded conversation: {chat_title}", icon="💬")
                with c_del:
                    if st.button("❌", key=f"del_chat_{idx}", use_container_width=True):
                        st.session_state.recent_chats.remove(chat_title)
                        st.rerun()
            
            if st.button("🗑️ Clear All History", use_container_width=True, key="clear_all_history"):
                st.session_state.recent_chats = []
                st.rerun()
        else:
            st.caption("No recent conversations.")

    # 4. SIDEBAR DISCLAIMER FOOTER
    st.markdown("""
    <div class="sidebar-disclaimer">
        ⚠️ <b>Disclaimer:</b> Educational decision-support tool aligned with NPHCDA standards.
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# TOP WEB APP HEADER (WITH STANDARD SIGN-IN BUTTON)
# ============================================================
header_col1, header_col2 = st.columns([7, 3])

with header_col1:
    st.markdown(f"### {page}")

with header_col2:
    if st.session_state.authenticated:
        st.markdown(f"🟢 **{st.session_state.user_name}**")
        if st.button("🚪 Sign Out", key="btn_signout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_name = "Guest Parent"
            st.rerun()
    else:
        if st.button("🔑 Sign In / Sign Up", key="btn_signin_modal", use_container_width=True):
            show_login_dialog()

st.divider()


# ============================================================
# PAGE 1: 🥗 NUTRITION & AI ASSISTANT
# ============================================================
if page == "🥗 Nutrition & AI Assistant":
    st.markdown("## 🥗 Nutrition & Child Health AI Assistant")
    st.markdown("<p style='color: #4A6E6B; font-size: 15px;'>Your expert AI companion for infant & child nutrition, NPHCDA immunization timelines, and pediatric healthcare guidance.</p>", unsafe_allow_html=True)

    if not has_ai_credentials:
        st.warning("⚠️ API credentials missing. Please verify `OPENAI_API_KEY` and `EMBEDDING_API_KEY` in `.env`.")

    # 1. RENDER CHAT HISTORY FEED
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # 2. UNIFIED GEMINI-STYLE INPUT BAR
    attached_file = None
    audio_recording = None

    with st.container():
        with st.form(key="gemini_chat_form", clear_on_submit=True):
            col_add, col_input, col_send = st.columns([1, 12, 2])

            with col_add:
                with st.popover("➕"):
                    st.markdown("**Attach Media or Voice**")
                    attached_file = st.file_uploader("Upload File/Image", type=["pdf", "txt", "csv", "png", "jpg"])
                    audio_recording = st.audio_input("Record Voice")

            with col_input:
                user_text_input = st.text_input(
                    "Ask about child nutrition, meal plans, vaccines, or health...",
                    placeholder="Ask a question about child nutrition, feeding, or vaccines...",
                    label_visibility="collapsed",
                    key="gemini_prompt"
                )

            with col_send:
                submit_btn = st.form_submit_button("Send ➔", use_container_width=True)

    # Process Voice Input
    active_prompt = None
    if audio_recording is not None:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(audio_recording.getvalue())
                temp_path = f.name
            with st.spinner("🎙️ Transcribing voice note..."):
                active_prompt = speech_to_text(temp_path)
        except Exception as e:
            st.error(f"Voice error: {e}")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    # Process File Context
    file_context = ""
    if attached_file is not None:
        file_context = f"\n[Attached File: {attached_file.name}]"
        st.toast(f"Attached: {attached_file.name}", icon="📎")

    user_prompt = user_text_input.strip() or active_prompt
    if submit_btn and user_prompt:
        full_query = user_prompt + file_context
        
        st.session_state.messages.append({"role": "user", "content": full_query})
        
        # Add to recent chats tracker
        recent_entry = "💬 " + user_prompt[:25] + ("..." if len(user_prompt) > 25 else "")
        if recent_entry not in st.session_state.recent_chats:
            st.session_state.recent_chats.insert(0, recent_entry)
        
        with st.chat_message("assistant", avatar="🤖"):
            if has_ai_credentials:
                with st.spinner("🧠 Thinking..."):
                    config = {"configurable": {"thread_id": st.session_state.session_id}}
                    response = st.session_state.agent.invoke(
                        {"messages": [("user", full_query)]},
                        config=config
                    )
                    reply = response["messages"][-1].content
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
            else:
                st.error("API credentials not available.")
        st.rerun()

    # 3. GEMINI DISCLAIMER FOOTER UNDER CHAT DOCK
    st.markdown("""
    <div class="gemini-footer-disclaimer">
        🛡️ PikinCare AI provides decision support aligned with WHO & NPHCDA standards. Check important medical decisions with a qualified doctor.
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# PAGE 2: 💉 IMMUNIZATION TRACKER
# ============================================================
elif page == "💉 Immunization Tracker":
    st.markdown("<p style='color: #4A6E6B;'>Official NPHCDA routine childhood vaccination timeline calculator.</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        dob = st.date_input("🗓️ Child's Date of Birth", value=date(2026, 1, 1))
    with col2:
        as_of = st.date_input("📌 Tracking Reference Date", value=date.today())

    if dob <= as_of:
        age_info = calculate_age(dob, as_of)
        st.info(f"👶 **Current Age:** {age_info['years']} yrs, {age_info['total_months'] % 12} mos ({age_info['total_weeks']} weeks)")

        records = build_vaccine_schedule(dob, as_of=as_of)
        grouped = group_vaccines_by_status(records)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🔴 Overdue", len(grouped["overdue"]))
        m2.metric("🟢 Due Now", len(grouped["due_now"]))
        m3.metric("🔵 Upcoming", len(grouped["upcoming"]))
        m4.metric("✅ Completed", len(grouped["completed"]))

        st.divider()
        display_data = [{
            "Vaccine": r["vaccine"], "Milestone": r["target_age_label"],
            "Due Date": r["due_date_label"], "Status": r["status"], "Route": r["route"]
        } for r in records]
        
        st.dataframe(display_data, use_container_width=True, hide_index=True)


# ============================================================
# PAGE 3: 🏥 HEALTH CENTER FINDER
# ============================================================
elif page == "🏥 Health Center Finder":
    if display_health_center_finder:
        display_health_center_finder()
    else:
        st.info("Loading health center discovery module...")


# ============================================================
# PAGE 4: 📈 GROWTH & HEALTH PASSPORT
# ============================================================
elif page == "📈 Growth & Health Passport":
    if render_pdf_generator:
        render_pdf_generator()
    else:
        st.info("Loading digital health passport generator...")