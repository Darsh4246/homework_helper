# EduSolver with Sidebar Navigation, Quiz Mode, and Score Tracking
from openai import OpenAI
from html import escape
import streamlit as st
from typing import Optional, Dict
import base64
import time
import datetime
import os
import random
import json

# Hugging Face API Configuration
HUGGINGFACE_API_KEY = os.getenv("EduBot_API_Key")
HUGGINGFACE_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"

def format_timestamp(timestamp: float) -> str:
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_response_for_streamlit(response: str) -> str:
    import re

    # Convert LaTeX-like blocks to proper LaTeX
    response = re.sub(r'\[\s*(.*?)\s*\]', r'$$\1$$', response, flags=re.DOTALL)  # block equations in [ ]

    # Replace double parentheses like ((x)) to LaTeX-style $x$
    response = re.sub(r'\(\((.*?)\)\)', r'$\1$', response)

    # Fix backslash escaping for LaTeX fractions and other math
    response = response.replace(r'\frac', '\\frac')

    return response


# Subjects and Example Questions
SUBJECTS = {
    "Math": {
        "examples": ["Solve 2x + 3 = 7", "Differentiate x^2", "Integrate x^3"],
        "recommendations": ["Review algebra basics", "Practice calculus daily"],
        "quiz": [
            {"q": "What is 7 * 8?", "options": ["54", "56", "58"], "answer": "56"},
            {"q": "Derivative of x^2?", "options": ["x", "2x", "x^2"], "answer": "2x"},
        ]
    },
    "Science": {
        "examples": ["Explain photosynthesis", "What are Newton's Laws?"],
        "recommendations": ["Use diagrams", "Watch science videos"],
        "quiz": [
            {"q": "What gas do plants use in photosynthesis?", "options": ["Oxygen", "Carbon Dioxide", "Nitrogen"], "answer": "Carbon Dioxide"},
            {"q": "Who proposed the law of gravity?", "options": ["Einstein", "Newton", "Tesla"], "answer": "Newton"},
        ]
    },
    "English": {
        "examples": ["Identify verb in sentence", "What is a synonym?"],
        "recommendations": ["Read daily", "Practice grammar"],
        "quiz": [
            {"q": "What is the synonym of 'Happy'?", "options": ["Sad", "Joyful", "Angry"], "answer": "Joyful"},
            {"q": "What is a verb?", "options": ["Person", "Action", "Thing"], "answer": "Action"},
        ]
    }
}

def render_chat_message(message: Dict, is_user: bool) -> None:
    from html import escape  # needed for safety
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
        # Format LaTeX/Markdown content
        raw_text = message.get("text", "")
        formatted_text = format_response_for_streamlit(raw_text)

        # Apply styling around formatted text
        message_html = f'<div style="{style}">{formatted_text}</div>'

        # If there's an image, add it below the message
        if message.get("image_base64"):
            image_html = (
                f'<img src="data:image/png;base64,{message["image_base64"]}" '
                'alt="Question Image" style="max-width:100%; margin-top:8px; border-radius:12px;"/>'
            )
            message_html = (
                f'<div style="{style}">{formatted_text}<br/>{image_html}</div>'
            )

        # Display message
        st.markdown(message_html, unsafe_allow_html=True)

        # Show timestamp if available
        timestamp = message.get("timestamp")
        if timestamp:
            ts_str = format_timestamp(timestamp)
            st.markdown(
                f'<p style="font-size:10px; color:gray; margin-top:-10px; text-align: right;">{ts_str}</p>',
                unsafe_allow_html=True
            )



# Helper functions
def render_quiz(subject):
    if subject not in SUBJECTS or "quiz" not in SUBJECTS[subject]:
        st.warning("No quiz available for this subject.")
        return
    if "quiz_scores" not in st.session_state:
        st.session_state.quiz_scores = {}

    score = 0
    quiz = SUBJECTS[subject]["quiz"]
    random.shuffle(quiz)
    for i, q in enumerate(quiz):
        st.markdown(f"**Q{i+1}: {q['q']}**")
        selected = st.radio("Select your answer:", q["options"], key=f"quiz_q{i}", label_visibility="collapsed")
        if st.session_state.get("quiz_submitted", False):
            if selected == q["answer"]:
                st.success("Correct!")
                score += 1
            else:
                st.error(f"Wrong! Correct answer: {q['answer']}")
        st.markdown("---")

    if not st.session_state.get("quiz_submitted"):
        if st.button("Submit Quiz"):
            st.session_state.quiz_submitted = True
            st.session_state.quiz_score = score
            if subject not in st.session_state.quiz_scores:
                st.session_state.quiz_scores[subject] = []
            st.session_state.quiz_scores[subject].append({
                "score": score,
                "total": len(quiz),
                "timestamp": datetime.datetime.now().isoformat()
            })
            st.rerun()
    else:
        st.success(f"You scored {score} out of {len(quiz)}")
        if st.button("Try Again"):
            for i in range(len(quiz)):
                del st.session_state[f"quiz_q{i}"]
            st.session_state.quiz_submitted = False
            st.rerun()

def show_quiz_history():
    st.subheader("📊 Quiz Score History")
    if "quiz_scores" not in st.session_state or not st.session_state.quiz_scores:
        st.info("No quiz history yet.")
        return
    for subj, scores in st.session_state.quiz_scores.items():
        st.markdown(f"**{subj}**")
        for entry in scores:
            st.markdown(f"- {entry['timestamp'].split('T')[0]}: {entry['score']} / {entry['total']}")

    history_json = json.dumps(st.session_state.quiz_scores, indent=2)
    b64 = base64.b64encode(history_json.encode()).decode()
    href = f'<a href="data:file/json;base64,{b64}" download="quiz_history.json">📥 Download Quiz History</a>'
    st.markdown(href, unsafe_allow_html=True)


def query_model(question: str, subject: str) -> str:
    prompt = f"Answer the following {subject} question clearly and concisely and if it is not a {subject} question, then ignore:\n\n{question}"

    token = os.getenv("APIKEY")  # Store this in environment
    endpoint = "https://models.github.ai/inference"
    model = "deepseek/DeepSeek-V3-0324"  # Or another model if specified

    try:
        client = OpenAI(base_url=endpoint, api_key=token)

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful educational assistant."},
                {"role": "user", "content": prompt}
            ],
            model=model,
            temperature=0.7,
            top_p=1.0
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error from GitHub Model API: {e}"

def main():
    st.set_page_config(page_title="EduSolve", layout="wide")
    st.sidebar.image("EduSolve Logo Design.png", width=180)
    st.sidebar.title("EduSolve Navigation")
    page = st.sidebar.radio("Go to", ["Ask Question", "Quiz Mode", "Quiz History"])
    subject = st.sidebar.selectbox("Choose Subject", list(SUBJECTS.keys()))

    if page == "Ask Question":
        st.title("Ask EduBot")
        question = st.text_area("Your question:")
        if st.button("Submit") and question.strip():
            with st.spinner("EduBot is thinking..."):
                response = query_model(question, subject)
            render_chat_message({"text": question, "timestamp": time.time()}, is_user=True)
            render_chat_message({"text": response, "timestamp": time.time()}, is_user=False)

    elif page == "Quiz Mode":
        st.title(f"Quiz: {subject}")
        render_quiz(subject)

    elif page == "Quiz History":
        show_quiz_history()

if __name__ == "__main__":
    main()
