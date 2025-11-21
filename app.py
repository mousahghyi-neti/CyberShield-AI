import streamlit as st
import google.generativeai as genai
import json
import os
import re

# --- [CONFIGURATION] ---
LOG_FILE = "abyss_memory_v6.json"
st.set_page_config(page_title="Dev Squad | Live Sandbox", page_icon="⚡", layout="wide")

# --- [CORE FUNCTIONS] ---
def load_memory():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

def save_memory():
    data = {
        "messages": st.session_state.messages,
        "current_code": st.session_state.current_code,
        "dark_plan": st.session_state.dark_plan
    }
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def call_ai_agent(agent_role, prompt_text):
    models_priority = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']
    for model_name in models_priority:
        try:
            model = genai.GenerativeModel(model_name)
            config = genai.types.GenerationConfig(temperature=0.7) 
            response = model.generate_content(prompt_text, generation_config=config)
            return response.text
        except:
            continue
    return "⚠️ Error: Connection Failed."

def extract_code(text):
    """استخراج الكود الصافي من رد الذكاء الاصطناعي"""
    # محاولة استخراج ما بين ``` و
