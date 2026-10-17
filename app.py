# app.py

from datetime import date
import os
import time
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
# CLEAN CHATGPT / GEMINI UI & CUSTOM STYLING
# ============================================================
st.markdown("""
<style>
/* Main App Surface */
.stApp {
    background: #F8FBFA;
    color: #102A2A;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* HIDE SIDEBAR COLLAPSE ARROW / TOGGLE */
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
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

/* Sidebar Brand Subtitle Styling */
.sidebar-subtitle {
    font-size: 12px;
    color: #A3E6DF !important;
    font-weight: 500;
    margin-bottom: 12px;
    margin-top: -6px;
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

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "registered_users" not in st.session_state:
    st.session_state.registered_users = {"parent@pikincare.ng": {"name": "Aishat Tiamiyu", "password": "password123"}}

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

# Flexible API Credentials Check
groq_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
has_ai_credentials = bool(groq_key)

if has_ai_credentials and "agent" not in st.session_state:
    try:
        st.session_state.agent = get_agent_executor()
    except Exception as e:
        st.error(f"Error initializing AI Agent: {e}")


# ============================================================
# REALISTIC AUTHENTICATION MODAL DIALOG
# ============================================================
@st.dialog("🔐 Account Access")
def show_login_dialog():
    st.caption("Sign in or create an account to save your child's health records & growth tracking.")
    
    tab_login, tab_signup = st.tabs(["🔑 Sign In", "📝 Create Account"])
    
    with tab_login:
        with st.form(key="form_login"):
            email_in = st.text_input("📧 Email Address", placeholder="e.g. parent@example.com", key="login_email").strip().lower()
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
                            st.session_state.authenticated = True
                            st.query_params["logged_in"] = "true"
                            st.query_params["user_name"] = user_info["name"]
                            st.toast(f"Welcome back, {user_info['name']}!", icon="🎉")
                            st.rerun()
                        else:
                            st.error("Incorrect password. Please try again.")
                    else:
                        display_name = email_in.split("@")[0].capitalize()
                        st.session_state.registered_users[email_in] = {"name": display_name, "password": pass_in}
                        st.session_state.user_name = display_name
                        st.session_state.user_email = email_in
                        st.session_state.authenticated = True
                        st.query_params["logged_in"] = "true"
                        st.query_params["user_name"] = display_name
                        st.toast(f"Welcome, {display_name}!", icon="🎉")
                        st.rerun()

    with tab_signup:
        with st.form(key="form_signup"):
            full_name = st.text_input("👤 Full Name", placeholder="e.g. Aishat Tiamiyu", key="signup_name").strip()
            signup_email = st.text_input("📧 Email Address", placeholder="e.g. parent@example.com", key="signup_email").strip().lower()
            signup_pass = st.text_input("🔒 Password", type="password", placeholder="Create a password (min. 6 chars)", key="signup_pass")
            submit_signup = st.form_submit_button("Create Account ✨", use_container_width=True)
            
            if submit_signup:
                if not full_name:
                    st.error("Please enter your full name.")
                elif not signup_email or "@" not in signup_email:
                    st.error("Please enter a valid email address.")
                elif len(signup_pass) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    st.session_state.registered_users[signup_email] = {"name": full_name, "password": signup_pass}
                    st.session_state.user_name = full_name
                    st.session_state.user_email = signup_email
                    st.session_state.authenticated = True
                    st.query_params["logged_in"] = "true"
                    st.query_params["user_name"] = full_name
                    st.toast("Account created successfully!", icon="✅")
                    st.rerun()


# ============================================================
# SIDEBAR NAVIGATION & GEMINI-STYLE CONTROLS
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
            st.session_state.user_email = ""
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
        st.warning("⚠️ API credentials missing. Please verify `GROQ_API_KEY` in your `.env` file.")

    # Determine assistant avatar safely based on file existence
    assistant_avatar = "hero_baby_illustration.png" if os.path.exists("hero_baby_illustration.png") else "👶"

    # 1. RENDER CHAT HISTORY FEED
    for msg in st.session_state.messages:
        avatar = assistant_avatar if msg["role"] == "assistant" else "🧑‍🍼"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # 2. CHAT INPUT WITH NATIVE AUDIO RECORDING & WHISPER TRANSCRIPTION
    active_prompt = None

    if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
        active_prompt = st.session_state.pending_prompt
        del st.session_state.pending_prompt

    user_input_obj = st.chat_input("Message PikinCare AI...", accept_audio=True)

    if user_input_obj:
        if isinstance(user_input_obj, dict):
            if user_input_obj.get("text"):
                active_prompt = user_input_obj["text"]
            elif user_input_obj.get("audio"):
                audio_file = user_input_obj["audio"]
                try:
                    with st.spinner("Transcribing your voice message..."):
                        from openai import OpenAI
                        client = OpenAI(
                            api_key=os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY"),
                            base_url="https://api.groq.com/openai/v1" if os.getenv("GROQ_API_KEY") else None
                        )
                        transcript = client.audio.transcriptions.create(
                            model="whisper-large-v3-turbo" if os.getenv("GROQ_API_KEY") else "whisper-1",
                            file=("audio.wav", audio_file.read(), "audio/wav")
                        )
                        active_prompt = transcript.text
                        st.toast(f"Heard: {active_prompt}", icon="🎙️")
                except Exception as e:
                    active_prompt = "Hello PikinCare, I need assistance with my child's health and nutrition."
                    st.warning(f"Voice transcription fallback used: {e}")
        elif isinstance(user_input_obj, str):
            active_prompt = user_input_obj

    # 3. PROCESS ACTIVE PROMPT & GET AI RESPONSE WITH STREAMING
    if active_prompt:
        full_query = active_prompt
        
        st.session_state.messages.append({"role": "user", "content": full_query})
        
        recent_entry = "💬 " + active_prompt[:25] + ("..." if len(active_prompt) > 25 else "")
        if recent_entry not in st.session_state.recent_chats:
            st.session_state.recent_chats.insert(0, recent_entry)
        
        with st.chat_message("assistant", avatar=assistant_avatar):
            if has_ai_credentials and "agent" in st.session_state:
                config = {"configurable": {"thread_id": st.session_state.session_id}}
                
                langchain_messages = []
                for msg in st.session_state.messages[:-1]:
                    if msg["role"] == "user":
                        langchain_messages.append(HumanMessage(content=msg["content"]))
                    else:
                        langchain_messages.append(AIMessage(content=msg["content"]))
                langchain_messages.append(HumanMessage(content=full_query))

                def response_generator():
                    response = st.session_state.agent.invoke(
                        {"messages": langchain_messages},
                        config=config
                    )
                    full_reply = response["messages"][-1].content
                    for word in full_reply.split(" "):
                        yield word + " "
                        time.sleep(0.02)

                reply = st.write_stream(response_generator())
                st.session_state.messages.append({"role": "assistant", "content": reply})
            else:
                st.error("Groq API credentials not available.")
        st.rerun()

    # 4. CHATGPT-STYLE DISCLAIMER FOOTER
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