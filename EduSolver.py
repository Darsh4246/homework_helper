# EduSolver with Sidebar Navigation, Quiz Mode, and Score Tracking

import streamlit as st
from typing import Optional, Dict
import base64
import time
import datetime
import requests
import os
import random
import json

# Hugging Face API Configuration
HUGGINGFACE_API_KEY = os.getenv("EduBot_API_Key")
HUGGINGFACE_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"

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
        selected = st.radio("", q["options"], key=f"quiz_q{i}")
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

def query_huggingface(question: str, subject: str) -> str:
    prompt = f"Answer the following {subject} question clearly and concisely and if it is not a {subject} question, then ignore:\n\n{question}"
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
                response = query_huggingface(question, subject)
            st.markdown("**EduBot:**")
            st.success(response)

    elif page == "Quiz Mode":
        st.title(f"Quiz: {subject}")
        render_quiz(subject)

    elif page == "Quiz History":
        show_quiz_history()

if __name__ == "__main__":
    main()
