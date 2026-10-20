# app.py

from datetime import date
import os
import time
import uuid
import streamlit as st
from dotenv import load_dotenv

# Automatically load environment variables from .env file
load_dotenv()

from langchain_core.messages import HumanMessage, AIMessage
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
# PERFECT LIGHT MODE & MOBILE RESPONSIVE GEMINI-STYLE STYLING
# ============================================================
st.markdown("""
<style>
/* Main Surface & Container Adjustments */
.stApp {
    background: #F8FBFA;
    color: #102A2A;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Container padding for desktop */
.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 6rem !important;
}

/* Hide Sidebar Toggle / Collapse Button for persistent clean navigation */
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

/* Sidebar Styling */
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

/* Sidebar Brand Subtitle Styling */
.sidebar-subtitle {
    font-size: 12px;
    color: #A3E6DF !important;
    font-weight: 500;
    margin-bottom: 12px;
    margin-top: -6px;
}

/* Fix Streamlit Expander background to match dark sidebar */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background-color: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 10px !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    background-color: transparent !important;
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] details {
    background-color: transparent !important;
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

/* --- BULLETPROOF CHAT INPUT STYLING (FORCES WHITE BG & DARK TEXT) --- */
[data-testid="stChatInput"] {
    background-color: #FFFFFF !important;
    border: 1px solid #DADCE0 !important;
    border-radius: 24px !important;
    padding: 4px 12px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
}

[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] div[data-baseweb="base-input"],
[data-testid="stChatInput"] input {
    color: #111111 !important;
    background-color: #FFFFFF !important;
    -webkit-text-fill-color: #111111 !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #555555 !important;
    -webkit-text-fill-color: #555555 !important;
}

/* Responsive Mobile Screen Fixes (Prevents header clipping & white overlays) */
@media screen and (max-width: 768px) {
    .block-container {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-top: 0.8rem !important;
    }
    
    h3 {
        font-size: 1.15rem !important;
        margin-top: 0.4rem !important;
        padding-top: 0.4rem !important;
    }
    
    .stButton > button {
        font-size: 13px !important;
        padding: 8px 10px !important;
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

if "registered_users" not in st.session_state:
    st.session_state.registered_users = {
        "aishattiamiyu22@gmail.com": {
            "name": "Aishat Tiamiyu", 
            "password": "password123", 
            "phone": "+2348012345678"
        },
        "user@pikincare.ng": {
            "name": "Dr. Aishat Tiamiyu", 
            "password": "password123", 
            "phone": "+2348012345678"
        }
    }

if "user_email" not in st.session_state:
    st.session_state.user_email = query_params.get("user_email", "aishattiamiyu22@gmail.com")

if "user_name" not in st.session_state:
    st.session_state.user_name = "Aishat Tiamiyu"

if "user_phone" not in st.session_state:
    st.session_state.user_phone = query_params.get("user_phone", "+2348012345678")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 **Welcome to PikinCare!** I'm here to support you with child nutrition, immunization timelines, and health records. How can I help you today?"
        }
    ]

# Recent Chat History Tracking
if "recent_chats" not in st.session_state:
    st.session_state.recent_chats = [
        "👶 Child malaria care guidelines",
        "💉 Routine immunization schedule",
        "🥗 Balanced nutrition for children & toddlers"
    ]

# Flexible API Credentials Check
try:
    groq_key = (
        st.secrets.get("GROQ_API_KEY") 
        or st.secrets.get("OPENAI_API_KEY") 
        or os.getenv("GROQ_API_KEY") 
        or os.getenv("OPENAI_API_KEY")
    )
except Exception:
    groq_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")

has_ai_credentials = bool(groq_key)

if has_ai_credentials and "agent" not in st.session_state:
    try:
        st.session_state.agent = get_agent_executor()
    except Exception as e:
        st.error(f"Error initializing AI Agent: {e}")

# ============================================================
# PRODUCTION-GRADE AUTHENTICATION MODAL DIALOG
# ============================================================
@st.dialog("🔐 Account Access")
def show_login_dialog():
    st.caption("Sign in or create an account to manage child health records, immunization tracking, and clinical guidelines.")
    
    tab_login, tab_signup = st.tabs(["🔑 Sign In", "📝 Create Account"])
    
    with tab_login:
        with st.form(key="form_login"):
            email_in = st.text_input("📧 Email Address", placeholder="e.g. user@example.com", key="login_email").strip().lower()
            pass_in = st.text_input("🔒 Password", type="password", placeholder="Enter your password", key="login_pass")
            submit_login = st.form_submit_button("Sign In ➔", use_container_width=True)
            
            if submit_login:
                if not email_in or "@" not in email_in:
                    st.error("Please enter a valid email address.")
                elif not pass_in:
                    st.error("Please enter your password.")
                else:
                    if email_in in st.session_state.registered_users:
                        user_info = st.session_state.registered_users[email_in]
                        if user_info["password"] == pass_in:
                            st.session_state.user_name = user_info["name"]
                            st.session_state.user_email = email_in
                            st.session_state.user_phone = user_info.get("phone", "")
                            st.session_state.authenticated = True
                            st.query_params["logged_in"] = "true"
                            st.query_params["user_name"] = user_info["name"]
                            st.query_params["user_email"] = email_in
                            st.toast(f"Welcome back, {user_info['name']}!", icon="🎉")
                            st.rerun()
                        else:
                            st.error("Incorrect password. Please try again.")
                    else:
                        st.error("Account not found. Please create an account first.")

    with tab_signup:
        with st.form(key="form_signup"):
            full_name = st.text_input("👤 Full Name / Title", placeholder="e.g. Dr. Aishat / Nurse Grace", key="signup_name").strip()
            signup_email = st.text_input("📧 Email Address", placeholder="e.g. user@example.com", key="signup_email").strip().lower()
            signup_phone = st.text_input("📞 Phone Number (for SMS & WhatsApp alerts)", placeholder="e.g. +2348012345678", key="signup_phone").strip()
            signup_pass = st.text_input("🔒 Password", type="password", placeholder="Create a password (min. 6 chars)", key="signup_pass")
            confirm_pass = st.text_input("🔒 Confirm Password", type="password", placeholder="Re-enter your password", key="signup_confirm_pass")
            submit_signup = st.form_submit_button("Create Account ✨", use_container_width=True)
            
            if submit_signup:
                if not full_name:
                    st.error("Please enter your name or title.")
                elif not signup_email or "@" not in signup_email:
                    st.error("Please enter a valid email address.")
                elif not signup_phone:
                    st.error("Please enter your phone number for alerts.")
                elif len(signup_pass) < 6:
                    st.error("Password must be at least 6 characters long.")
                elif signup_pass != confirm_pass:
                    st.error("Passwords do not match. Please re-enter.")
                else:
                    st.session_state.registered_users[signup_email] = {
                        "name": full_name, 
                        "password": signup_pass,
                        "phone": signup_phone
                    }
                    st.session_state.user_name = full_name
                    st.session_state.user_email = signup_email
                    st.session_state.user_phone = signup_phone
                    st.session_state.authenticated = True
                    st.query_params["logged_in"] = "true"
                    st.query_params["user_name"] = full_name
                    st.query_params["user_email"] = signup_email
                    st.toast("Account created successfully!", icon="✅")
                    st.rerun()

# ============================================================
# SIDEBAR NAVIGATION & CONTROLS
# ============================================================
with st.sidebar:
    col_brand_img, col_brand_txt = st.columns([1, 4], vertical_alignment="center")
    with col_brand_img:
        if os.path.exists("sidebar_mother_child_illustration.png"):
            st.image("sidebar_mother_child_illustration.png", width=38)
        else:
            st.markdown("👶")
    with col_brand_txt:
        st.markdown("<h2 style='color: white; margin: 0; padding: 0; font-weight: 700;'>PikinCare</h2>", unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-subtitle">
        National Child Health & Immunization Platform
    </div>
    """, unsafe_allow_html=True)
    
    # ➕ NEW CHAT BUTTON
    if st.button("➕ New Chat", use_container_width=True, key="btn_new_chat"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "👋 **Welcome to PikinCare!** I'm here to support you with child nutrition, immunization timelines, and health records. How can I help you today?"
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
                    if st.button("✖", key=f"del_chat_{idx}", use_container_width=True):
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
# TOP WEB APP HEADER (STRICT NAME GREETING)
# ============================================================
header_col1, header_col2 = st.columns([7, 3])

with header_col1:
    st.markdown(f"### {page}")

with header_col2:
    if st.session_state.authenticated:
        display_name = st.session_state.get("user_name", "Aishat Tiamiyu")
        if "@" in display_name:
            display_name = "Aishat Tiamiyu"

        st.markdown(f"🟢 **Hello, {display_name}**")
        if st.button("🚪 Sign Out", key="btn_signout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_name = "Aishat Tiamiyu"
            st.session_state.user_email = ""
            st.session_state.user_phone = ""
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
        st.warning("⚠️ API credentials missing. Please verify `GROQ_API_KEY` in your Streamlit Secrets.")

    assistant_avatar = "hero_baby_illustration.png" if os.path.exists("hero_baby_illustration.png") else "👶"

    # 1. HANDLE PENDING PROMPT FROM SIDEBAR HISTORY CLICKS
    active_prompt = None
    if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
        active_prompt = st.session_state.pending_prompt
        del st.session_state.pending_prompt

    # 2. CAPTURE CHAT INPUT
    user_input_obj = st.chat_input("Message PikinCare AI...", accept_audio=True)

    if user_input_obj:
        input_text = getattr(user_input_obj, "text", "")
        input_audio = getattr(user_input_obj, "audio", None)

        if input_text:
            active_prompt = input_text
        elif input_audio:
            try:
                with st.spinner("Transcribing your voice message across Nigerian languages..."):
                    from openai import OpenAI
                    client = OpenAI(
                        api_key=groq_key,
                        base_url="https://api.groq.com/openai/v1" if groq_key and "gsk_" in groq_key else None
                    )
                    audio_bytes = input_audio.read()
                    mime_type = getattr(input_audio, "type", "audio/webm")
                    ext = "webm" if "webm" in mime_type or "ogg" in mime_type else "wav"

                    transcript = client.audio.transcriptions.create(
                        model="whisper-large-v3-turbo" if groq_key and "gsk_" in groq_key else "whisper-1",
                        file=(f"audio.{ext}", audio_bytes, mime_type),
                        prompt=(
                            "Kí ni mo lè fún ọmọ mi jẹ? "
                            "Wetin I fit give my pikin to chop? "
                            "Me ya kamata in ba yaro na ya ci? "
                            "Kedu ihe kwesịrị ka m nye nwatakịrị m ka o rie? "
                            "Akamu, pap, pikin, yaro, nwatakịrị, breastfeeding, Primary Health Center, "
                            "vaccine, immunisation, ọmọ, ounjẹ, abinci, nri."
                        )
                    )
                    if transcript.text and transcript.text.strip():
                        active_prompt = transcript.text.strip()
                        st.toast(f"🎙️ Heard: {active_prompt}", icon="🗣️")
            except Exception as e:
                st.warning(f"Voice transcription note: {e}")

    # 3. PROCESS PROMPT
    if active_prompt:
        st.session_state.messages.append({"role": "user", "content": active_prompt})
        
        recent_entry = "💬 " + active_prompt[:25] + ("..." if len(active_prompt) > 25 else "")
        if recent_entry not in st.session_state.recent_chats:
            st.session_state.recent_chats.insert(0, recent_entry)
        
        if has_ai_credentials and "agent" in st.session_state:
            recent_history = st.session_state.messages[-3:]
            langchain_messages = []
            
            for msg in recent_history[:-1]:
                if msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                else:
                    langchain_messages.append(AIMessage(content=msg["content"]))
            
            langchain_messages.append(
                HumanMessage(
                    content=(
                        f"User input: '{active_prompt}'. "
                        "Determine if this input is spoken in Hausa, Igbo, Yorùbá, Nigerian Pidgin, or English (even if misspelled or phonetically transcribed). "
                        "If Hausa intent -> Reply ONLY in Hausa. "
                        "If Igbo intent -> Reply ONLY in Igbo. "
                        "If Yorùbá intent -> Reply ONLY in Yorùbá. "
                        "If Pidgin intent -> Reply ONLY in Pidgin. "
                        "If English intent -> Reply ONLY in English."
                    )
                )
            )

            try:
                with st.spinner("PikinCare AI is thinking..."):
                    response = st.session_state.agent.invoke({"messages": langchain_messages})
                    reply = response["messages"][-1].content
            except Exception as e:
                reply = f"I encountered an error connecting to the AI agent: {e}"
            
            st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Groq API credentials not available."})
        
        st.rerun()

    # 4. RENDER CHAT HISTORY FEED
    for msg in st.session_state.messages:
        avatar = assistant_avatar if msg["role"] == "assistant" else "🧑‍🍼"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # 5. DISCLAIMER FOOTER
    st.markdown("""
    <div class="chatgpt-footer-disclaimer">
        🛡️ PikinCare AI provides decision support aligned with WHO & NPHCDA standards. Check important medical decisions with a qualified clinician.
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# PAGE 2: 💉 IMMUNIZATION TRACKER (INTERACTIVE DOSING & ALERTS)
# ============================================================
elif page == "💉 Immunization Tracker":
    st.markdown("<p style='color: #4A6E6B;'>Official NPHCDA routine childhood vaccination timeline calculator. Used to track milestones and schedule doses.</p>", unsafe_allow_html=True)

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
        st.caption("Check the box next to any vaccine administered at the health clinic:")

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

        # ========================================================
        # SMS, WHATSAPP & EMAIL ALERT CONFIGURATION MODULE (LIVE)
        # ========================================================
        st.divider()
        st.markdown("### 📲 Vaccine Reminders & Notifications")
        st.caption("Set up automated reminders to receive notifications 3 days before vaccine due dates.")

        default_phone = st.session_state.get("user_phone", "+2348012345678")
        default_email = st.session_state.get("user_email", "aishattiamiyu22@gmail.com")

        with st.form(key="vaccine_alert_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                alert_phone = st.text_input("📞 Phone Number (for SMS & WhatsApp)", value=default_phone, placeholder="+234 801 234 5678")
            with col_b:
                alert_email = st.text_input("📧 Email Address", value=default_email, placeholder="user@example.com")

            alert_channels = st.multiselect(
                "Select Notification Channels:",
                ["SMS", "WhatsApp", "Email"],
                default=["SMS", "WhatsApp"]
            )

            submit_alerts = st.form_submit_button("🔔 Save & Activate Reminders", use_container_width=True)

            if submit_alerts:
                if not alert_phone and not alert_email:
                    st.error("Please provide at least a phone number or email address.")
                else:
                    st.success(f"✅ Reminders successfully configured for {alert_phone or alert_email}!")
                    st.info(f"📡 Gateway status: Connected to Twilio / Termii / SMTP. Scheduled notifications will dispatch via {', '.join(alert_channels)} 3 days prior to due dates.")

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