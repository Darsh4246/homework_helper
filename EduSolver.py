import streamlit as st
from typing import Optional, Dict
import base64
import time
import datetime
import requests
import os

# Hugging Face API Configuration
HUGGINGFACE_API_KEY = os.getenv("EduBot_API_Key")
HUGGINGFACE_MODEL = "HuggingFaceH4/zephyr-7b-beta"

st.set_page_config(
    page_title="EduSolve - Student Q&A with EduBots",
    layout="wide",
    initial_sidebar_state="auto",
    page_icon="🧠"
)

SUBJECTS = {
    "Math": {
        "examples": [
            "Solve quadratic equations.",
            "Calculate derivative of function.",
            "Find integral of polynomial."
        ],
        "recommendations": [
            "Use algebraic formulas.",
            "Review calculus basics.",
            "Practice problem-solving daily."
        ],
    },
    "Science": {
        "examples": [
            "Explain photosynthesis process.",
            "Describe Newton’s laws of motion.",
            "Discuss chemical reactions."
        ],
        "recommendations": [
            "Use diagrams to visualize concepts.",
            "Watch science documentaries.",
            "Take detailed notes in class."
        ],
    },
    "History": {
        "examples": [
            "Analyze causes of World War II.",
            "Discuss ancient civilizations.",
            "Interpret historical documents."
        ],
        "recommendations": [
            "Use timelines to track events.",
            "Read multiple historical sources.",
            "Discuss topics with peers."
        ],
    },
    "Literature": {
        "examples": [
            "Interpret poetry symbolism.",
            "Analyze character development.",
            "Compare literary genres."
        ],
        "recommendations": [
            "Read critically and annotate texts.",
            "Explore different literary time periods.",
            "Attend literary discussions or clubs."
        ],
    },
    "Technology": {
        "examples": [
            "Explain machine learning basics.",
            "Discuss cloud computing advantages.",
            "Describe networking protocols."
        ],
        "recommendations": [
            "Stay updated with latest tech news.",
            "Practice coding daily.",
            "Build small projects regularly."
        ],
    },
}

DEFAULT_PROFILE = {
    "username": None,
    "email": None,
    "avatar_base64": None,
    "joined_on": None,
    "last_active": None,
}

def query_huggingface(question: str, subject: str) -> str:
    prompt = f"You're an expert {subject} tutor named EduBot. Answer the following question clearly and helpfully:"

    Q: {question}
    A:""
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.7,
            "max_new_tokens": 512,
            "return_full_text": False
        }
    }
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}",
        headers=headers,
        json=data
    )
    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"
    try:
        return response.json()[0]["generated_text"]
    except Exception as e:
        return f"Failed to parse response: {e}"

def pil_image_to_base64(img_file) -> Optional[str]:
    try:
        img_bytes = img_file.read()
        base64_str = base64.b64encode(img_bytes).decode("utf-8")
        img_file.seek(0)
        return base64_str
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None

def format_timestamp(timestamp: float) -> str:
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def render_chat_message(message: Dict, is_user: bool) -> None:
    bg_color = "#1d4ed8" if is_user else "#f97316"
    text_color = "#ffffff" if is_user else "#000000"
    style = (
        f"background-color: {bg_color}; color: {text_color}; "
        "padding: 16px; border-radius: 18px; width: 100%; margin-bottom: 12px; "
        "white-space: pre-wrap; overflow-wrap: break-word; font-size: 0.95rem; line-height: 1.4;"
    )
    container_col_user = st.columns([1, 5])
    container_col_ai = st.columns([5, 1])
    col = container_col_user[1] if is_user else container_col_ai[0]
    with col:
        message_html = f'<div style="{style}">{message.get("text","")}</div>'
        if message.get("image_base64"):
            image_html = (
                f'<img src="data:image/png;base64,{message["image_base64"]}" '
                'alt="Question Image" style="max-width:100%; margin-top:8px; border-radius:12px;"/>'
            )
            message_html = (
                f'<div style="{style}">{message.get("text","")}' + "<br/>" + image_html + "</div>"
            )
        st.markdown(message_html, unsafe_allow_html=True)
        timestamp = message.get("timestamp")
        if timestamp:
            ts_str = format_timestamp(timestamp)
            st.markdown(
                f'<p style="font-size:10px; color:gray; margin-top:-10px; text-align: right;">{ts_str}</p>',
                unsafe_allow_html=True
            )

def clear_chat_history():
    st.session_state.chat_history = []

def export_chat_history() -> None:
    import json
    if "chat_history" not in st.session_state or not st.session_state.chat_history:
        st.warning("No chat history to export.")
        return
    history_json = json.dumps(st.session_state.chat_history, indent=2)
    b64 = base64.b64encode(history_json.encode()).decode()
    href = (
        f'<a href="data:file/json;base64,{b64}" download="chat_history.json" '
        'style="color:#10b981; font-weight:bold;">Download chat history as JSON</a>'
    )
    st.markdown(href, unsafe_allow_html=True)

def main():
    if "profile" not in st.session_state:
        st.session_state.profile = DEFAULT_PROFILE.copy()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    with st.sidebar:
        st.image("EduSolve Logo Design.png", width=180)
        st.title("EduSolve")
        st.markdown("""
            Welcome to EduSolve! Ask questions by typing or uploading an image.
            Responses are generated by EduBots via Hugging Face.
        """)
        username_input = st.text_input("Enter username (optional)", value=st.session_state.profile.get("username") or "")
        if username_input and username_input != st.session_state.profile.get("username"):
            st.session_state.profile["username"] = username_input.strip()
            st.session_state.profile["joined_on"] = st.session_state.profile["joined_on"] or datetime.datetime.now().isoformat()
            st.session_state.profile["last_active"] = datetime.datetime.now().isoformat()
        if st.button("Clear username (log out)"):
            st.session_state.profile = DEFAULT_PROFILE.copy()
            clear_chat_history()
            st.rerun()
        st.markdown("""---""")
        st.header("Chat Controls")
        if st.button("Clear chat history"):
            clear_chat_history()
            st.rerun()
        export_chat_history()
        st.markdown("""---""")
        st.markdown('<p style="color: #1d4ed8; font-weight: bold;">© 2025 <span style="color:#f97316;">EduSolve</span> - Powered by EduBots</p>', unsafe_allow_html=True)

    col_main, col_right = st.columns([4, 1])
    subject = st.session_state.get("selected_subject", None)
    with col_right:
        st.header("Subjects")
        subj_selected = st.selectbox("Select Subject", options=[""] + list(SUBJECTS.keys()),
                                     index=list(SUBJECTS.keys()).index(subject) + 1 if subject in SUBJECTS else 0,
                                     key="selected_subject")
        st.subheader("Examples")
        if subj_selected and subj_selected in SUBJECTS:
            for ex in SUBJECTS[subj_selected]["examples"]:
                st.markdown(f"- {ex}")
        else:
            st.info("Select a subject to see examples.")
        st.subheader("Recommendations")
        if subj_selected and subj_selected in SUBJECTS:
            for rec in SUBJECTS[subj_selected]["recommendations"]:
                st.markdown(f"- {rec}")
        else:
            st.info("Select a subject to see recommendations.")

    with col_main:
        st.header("Ask your question")
        with st.form("question_form", clear_on_submit=False):
            question_text = st.text_area("Type your question here:", max_chars=1500, height=150,
                                        key="question_input", placeholder="Type your question or inquiry here...")
            image_file = st.file_uploader("Or upload an image (PNG/JPEG)", type=["png", "jpg", "jpeg"], key="image_input")
            can_send = False
            input_errors = []
            if not subj_selected:
                input_errors.append("Please select a subject.")
            if not question_text.strip() and not image_file:
                input_errors.append("Please type a question or upload an image.")
            if input_errors:
                for err in input_errors:
                    st.error(err)
            else:
                can_send = True
            submitted = st.form_submit_button("Send Question")
            if submitted:
                if not can_send:
                    st.error("Please select a subject and type a question or upload an image.")
                    st.stop()
            if submitted:
                st.session_state.profile["last_active"] = datetime.datetime.now().isoformat()
                img_base64 = pil_image_to_base64(image_file) if image_file else None
                st.session_state.chat_history.append({
                    "user": st.session_state.profile.get("username") or "Guest",
                    "is_user": True,
                    "text": question_text.strip() or "(Image question)",
                    "image_base64": img_base64,
                    "subject": subj_selected,
                    "timestamp": time.time(),
                })
                # Cannot reset widget state directly after use; workaround by clearing form only
# st.session_state["question_input"] = ""
                # st.session_state["image_input"] = None
                st.rerun()

        st.subheader("Conversation")
        if not st.session_state.chat_history:
            st.info("Start by typing a question or uploading an image!")
        for msg in st.session_state.chat_history:
            render_chat_message(msg, msg["is_user"])
        if st.session_state.chat_history and st.session_state.chat_history[-1]["is_user"]:
            last_msg = st.session_state.chat_history[-1]
            with st.spinner("EduBot is generating an answer..."):
                ai_response_text = query_huggingface(last_msg["text"], last_msg["subject"])
                time.sleep(1)
            st.session_state.chat_history.append({
                "user": "EduBot",
                "is_user": False,
                "text": ai_response_text,
                "image_base64": None,
                "subject": last_msg["subject"],
                "timestamp": time.time(),
            })
            st.rerun()

if __name__ == "__main__":
    main()
