# app.py

from datetime import date
import os
import tempfile
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
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
# CLEAN CHATGPT / GEMINI UI & FIX POPOVER ALIGNMENT
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
    font-size: 28px;
}

/* Sidebar Subtitle Styling */
.sidebar-subtitle {
    font-size: 12px;
    color: #A3E6DF !important;
    font-weight: 500;
    margin-bottom: 12px;
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

/* Footer Disclaimer */
.chatgpt-footer-disclaimer {
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
    width: 100%;
}
.stButton > button:hover {
    background: #043A37;
    color: white !important;
}

/* FIX POPOVER (🎤) BUTTON IN-LINE */
[data-testid="stPopover"] {
    display: inline-block !important;
}
[data-testid="stPopover"] button {
    background: #E2ECE9 !important;
    border: 1px solid #A3E6DF !important;
    border-radius: 50% !important;
    width: 38px !important;
    height: 38px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 16px !important;
    color: #064E4A !important;
    padding: 0 !important;
    margin-top: 24px !important;
}

/* Recent chat history styling in sidebar */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button {
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-size: 12px !important;
    border-radius: 8px !important;
    padding: 4px 8px !important;
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button:hover {
    background: rgba(255, 255, 255, 0.2) !important;
}

/* Universal Cross-Device Responsive Queries */
@media screen and (max-width: 768px) {
    .block-container {
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        padding-top: 1rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# PERSISTENT SESSION STATE INITIALIZATION
# ============================================================
query_params = st.query_params

if "authenticated" not in st.session_state:
    st.session_state.authenticated = query_params.get("logged_in", "false") == "true"

if "user_name" not in st.session_state:
    st.session_state.user_name = query_params.get("user_name", "Guest Parent")

if "session_id" not in st.session_state:
    st.session_state.session_id = f"pikincare_{st.session_state.user_name.lower().replace(' ', '_')}"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 **Welcome to PikinCare!** I'm here to support you with your child's nutrition, growth, and health journey. How can I help you today?"
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
                user_name = email.split("@")[0].capitalize()
                st.session_state.user_name = user_name
                st.session_state.authenticated = True
                
                st.query_params["logged_in"] = "true"
                st.query_params["user_name"] = user_name
                
                st.toast(f"Welcome back, {user_name}!", icon="🎉")
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
                
                st.query_params["logged_in"] = "true"
                st.query_params["user_name"] = full_name
                
                st.toast("Account created successfully!", icon="✅")
                st.rerun()
            else:
                st.error("Please fill in all details.")


# ============================================================
# SIDEBAR NAVIGATION & GEMINI-STYLE CONTROLS
# ============================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <span class="sidebar-brand-icon">👶</span>
        <span>PikinCare</span>
    </div>
    <div class="sidebar-subtitle">
        Your Trusted Partner in Child Wellness & Nutrition
    </div>
    """, unsafe_allow_html=True)
    
    # ➕ NEW CHAT BUTTON
    if st.button("➕ New Chat", use_container_width=True, key="btn_new_chat"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "👋 **Welcome to PikinCare!** I'm here to support you with your child's nutrition, growth, and health journey. How can I help you today?"
            }
        ]
        if "pending_prompt" in st.session_state:
            del st.session_state.pending_prompt
        st.rerun()

    st.divider()

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

    with st.expander("🕒 Recent Conversations", expanded=True):
        if st.session_state.recent_chats:
            for idx, chat_title in enumerate(list(st.session_state.recent_chats)):
                col_load, col_del = st.columns([5, 1], gap="small")
                with col_load:
                    if st.button(chat_title, key=f"load_chat_{idx}", use_container_width=True):
                        clean_query = chat_title.replace("👶 ", "").replace("💉 ", "").replace("🥗 ", "").replace("💬 ", "")
                        st.session_state.pending_prompt = clean_query
                        st.rerun()
                with col_del:
                    if st.button("❌", key=f"del_chat_{idx}", use_container_width=True):
                        st.session_state.recent_chats.remove(chat_title)
                        st.rerun()
            
            if st.button("🗑️ Clear All History", use_container_width=True, key="clear_all_history"):
                st.session_state.recent_chats = []
                st.rerun()
        else:
            st.caption("No recent conversations.")

    st.markdown("""
    <div class="sidebar-disclaimer">
        ⚠️ <b>Disclaimer:</b> Educational decision-support tool aligned with NPHCDA standards.
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# TOP WEB APP HEADER
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
            st.query_params.clear()
            st.rerun()
    else:
        if st.button("🔑 Sign In / Sign Up", key="btn_signin_modal", use_container_width=True):
            show_login_dialog()

st.divider()


# ============================================================
# PAGE 1: 🥗 NUTRITION & AI ASSISTANT
# ============================================================
if page == "🥗 Nutrition & AI Assistant":
    st.markdown("<p style='color: #4A6E6B; font-size: 15px;'>Your expert AI companion for infant & child nutrition, NPHCDA immunization timelines, and pediatric healthcare guidance.</p>", unsafe_allow_html=True)

    if not has_ai_credentials:
        st.warning("⚠️ API credentials missing. Please verify `OPENAI_API_KEY` and `EMBEDDING_API_KEY` in `.env` or Streamlit Secrets.")

    # 1. RENDER CHAT HISTORY FEED
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # 2. IN-LINE EMBEDDED INPUT ROW (Speech Recognition Popover + Text Input inside form)
    audio_recording = None
    user_typed_input = None

    with st.container():
        with st.form(key="embedded_chat_form", clear_on_submit=True):
            col_mic, col_input, col_send = st.columns([1, 10, 1])

            with col_mic:
                with st.popover("🎤", help="Record Voice Note"):
                    st.markdown("**Voice Recognition**")
                    audio_recording = st.audio_input("Record Voice Note", key="chat_audio_input")

            with col_input:
                user_typed_input = st.text_input(
                    "Message PikinCare AI...",
                    placeholder="Message PikinCare AI...",
                    label_visibility="collapsed",
                    key="embedded_prompt"
                )

            with col_send:
                submit_btn = st.form_submit_button("➔", use_container_width=True)

    # Handle Active Input Priority
    active_prompt = None
    if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
        active_prompt = st.session_state.pending_prompt
        del st.session_state.pending_prompt
    elif submit_btn and user_typed_input:
        active_prompt = user_typed_input
    elif audio_recording is not None:
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

    if active_prompt:
        full_query = active_prompt
        
        st.session_state.messages.append({"role": "user", "content": full_query})
        
        recent_entry = "💬 " + active_prompt[:25] + ("..." if len(active_prompt) > 25 else "")
        if recent_entry not in st.session_state.recent_chats:
            st.session_state.recent_chats.insert(0, recent_entry)
        
        with st.chat_message("assistant", avatar="🤖"):
            if has_ai_credentials:
                with st.spinner("🧠 Thinking..."):
                    config = {"configurable": {"thread_id": st.session_state.session_id}}
                    
                    langchain_messages = []
                    for msg in st.session_state.messages:
                        if msg["role"] == "user":
                            langchain_messages.append(HumanMessage(content=msg["content"]))
                        else:
                            langchain_messages.append(AIMessage(content=msg["content"]))
                    
                    response = st.session_state.agent.invoke(
                        {"messages": langchain_messages},
                        config=config
                    )
                    reply = response["messages"][-1].content
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
            else:
                st.error("API credentials not available.")
        st.rerun()

    # 3. CHATGPT-STYLE DISCLAIMER FOOTER
    st.markdown("""
    <div class="chatgpt-footer-disclaimer">
        🛡️ PikinCare AI provides decision support aligned with WHO & NPHCDA standards. Check important medical decisions with a qualified doctor.
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# PAGE 2: 💉 IMMUNIZATION TRACKER (INTERACTIVE DOSING)
# ============================================================
elif page == "💉 Immunization Tracker":
    st.markdown("<p style='color: #4A6E6B;'>Official NPHCDA routine childhood vaccination timeline calculator. Check off vaccines your baby has already received.</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        dob = st.date_input("🗓️ Child's Date of Birth", value=date(2026, 1, 1))
    with col2:
        as_of = st.date_input("📌 Tracking Reference Date", value=date.today())

    if dob <= as_of:
        age_info = calculate_age(dob, as_of)
        st.info(f"👶 **Current Age:** {age_info['years']} yrs, {age_info['total_months'] % 12} mos ({age_info['total_weeks']} weeks)")

        if "completed_vaccines" not in st.session_state:
            st.session_state.completed_vaccines = []

        records = build_vaccine_schedule(dob, as_of=as_of)
        
        for r in records:
            if r["vaccine"] in st.session_state.completed_vaccines:
                r["status"] = "completed"

        grouped = group_vaccines_by_status(records)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🔴 Overdue", len(grouped["overdue"]))
        m2.metric("🟢 Due Now", len(grouped["due_now"]))
        m3.metric("🔵 Upcoming", len(grouped["upcoming"]))
        m4.metric("✅ Completed", len(grouped["completed"]))

        st.divider()
        st.markdown("### 📋 Vaccination Schedule & Record Check")
        st.caption("Check the box next to any vaccine your baby has already received at the health clinic:")

        updated_completed = list(st.session_state.completed_vaccines)
        
        for idx, r in enumerate(records):
            is_checked = r["vaccine"] in updated_completed
            cols = st.columns([1, 3, 2, 2, 2])
            
            with cols[0]:
                checked = st.checkbox("Done", value=is_checked, key=f"vac_check_{idx}", label_visibility="collapsed")
                if checked and r["vaccine"] not in updated_completed:
                    updated_completed.append(r["vaccine"])
                elif not checked and r["vaccine"] in updated_completed:
                    updated_completed.remove(r["vaccine"])

            with cols[1]:
                st.markdown(f"**{r['vaccine']}**")
            with cols[2]:
                st.caption(f"Milestone: {r['target_age_label']}")
            with cols[3]:
                st.caption(f"Due: {r['due_date_label']}")
            with cols[4]:
                status_color = "🔴" if r['status'] == 'overdue' else ("🟢" if r['status'] == 'due_now' else ("🔵" if r['status'] == 'upcoming' else "✅"))
                st.markdown(f"{status_color} *{r['status']}*")

        if updated_completed != st.session_state.completed_vaccines:
            st.session_state.completed_vaccines = updated_completed
            st.rerun()


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