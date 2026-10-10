# app.py

import streamlit as st
from datetime import date
from src.rag_engine import get_agent_executor
from src.vaccine_tracker import (
    build_vaccine_schedule,
    calculate_age,
    group_vaccines_by_status,
)

# Safe imports for merged modules
try:
    from src.health_center import display_health_center_finder
except ImportError:
    display_health_center_finder = None

try:
    from src.pdf_generator import render_pdf_generator
except ImportError:
    render_pdf_generator = None

st.set_page_config(
    page_title="PikinCare AI — Child Health Assistant",
    page_icon="👶",
    layout="wide"
)

# Custom Styling for ChatGPT Minimalist Aesthetic
st.markdown("""
    <style>
    .chat-header {
        font-size: 1.8rem;
        font-weight: 700;
        text-align: center;
        color: #1F2937;
        margin-bottom: 0px;
    }
    .chat-sub {
        font-size: 0.95rem;
        text-align: center;
        color: #6B7280;
        margin-bottom: 25px;
    }
    .disclaimer-text {
        font-size: 0.75rem;
        color: #9CA3AF;
        text-align: center;
        margin-top: 15px;
        padding: 8px;
        border-top: 1px solid #E5E7EB;
    }
    .stChatInput {
        position: fixed;
        bottom: 45px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR: ChatGPT Style Navigation & History
# ==========================================
with st.sidebar:
    st.markdown("## 👶 **PikinCare AI**")
    st.caption("Child Nutrition & Immunization System (CNITS)")
    st.divider()
    
    # Navigation Modes
    app_mode = st.radio(
        "📌 Navigation",
        ["💬 AI Health Assistant", "💉 Smart Vaccine Tracker", "🏥 Health Center Finder", "📄 Digital Health Passport"]
    )
    
    st.divider()
    
    # Recents & Chat History
    st.markdown("### 📜 Recents")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # Sample previous search threads
    st.caption("🕒 Earlier Demos")
    st.markdown("• *14-Week Immunization Doses*")
    st.markdown("• *Exclusive Breastfeeding Tips*")
    st.markdown("• *Vitamin A Supplementation*")

    st.divider()
    st.caption("🏆 **Tech Queens** | Competition Finals 2026")

# ==========================================
# MODE 1: AI HEALTH CHATBOT (ChatGPT UI)
# ==========================================
if app_mode == "💬 AI Health Assistant":
    st.markdown('<p class="chat-header">What can I help with your baby\'s health today?</p>', unsafe_allow_html=True)
    st.markdown('<p class="chat-sub">Type in any Nigerian language (Yoruba, Hausa, Igbo, Pidgin, etc.) or English</p>', unsafe_allow_html=True)

    if "agent" not in st.session_state:
        st.session_state.agent = get_agent_executor()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    config = {"configurable": {"thread_id": "streamlit_user_session"}}

    # Starter Suggestion Chips (ChatGPT Style)
    if not st.session_state.messages:
        c1, c2, c3 = st.columns(3)
        if c1.button("🍼 6-Month Infant Feeding", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "What local foods can I give my 6-month-old baby in Nigeria?"})
        if c2.button("💉 10-Week Vaccine List", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Which vaccines are due at 10 weeks according to NPHCDA?"})
        if c3.button("🥗 Preventing Malnutrition", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "How can I ensure my child gets enough iron and micronutrients?"})

    # Render Chat History
    for message in st.session_state.messages:
        avatar = "👶" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # File Attachment Option (ChatGPT Paperclip feature)
    with st.expander("📎 Attach Growth Chart or Medical Note (Optional)"):
        uploaded_file = st.file_uploader("Upload image or PDF document", type=["png", "jpg", "jpeg", "pdf"])
        if uploaded_file:
            st.success(f"Attached: `{uploaded_file.name}` (Ready for session context)")

    # User Chat Input (Auto-detects language)
    if user_input := st.chat_input("Message PikinCare AI..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👶"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Analyzing NPHCDA & Health Guidelines..."):
                # Natural language prompt instructions to reply in the user's input language
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

    # Medical Disclaimer
    st.markdown(
        '<div class="disclaimer-text">⚠️ <b>Medical Disclaimer:</b> PikinCare AI provides educational information based on NPHCDA & WHO guidelines. It is not a substitute for clinical advice or professional medical diagnosis. Always consult a certified healthcare professional at a Primary Healthcare Centre.</div>',
        unsafe_allow_html=True
    )

# ==========================================
# MODE 2: SMART VACCINE TRACKER
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
# MODE 3: HEALTH CENTER FINDER
# ==========================================
elif app_mode == "🏥 Health Center Finder":
    if display_health_center_finder:
        display_health_center_finder()
    else:
        st.info("Health Center module loaded.")

# ==========================================
# MODE 4: DIGITAL HEALTH PASSPORT (PDF)
# ==========================================
elif app_mode == "📄 Digital Health Passport":
    if render_pdf_generator:
        render_pdf_generator()
    else:
        st.info("PDF Generator module loaded.")