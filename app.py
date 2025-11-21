import streamlit as st
import google.generativeai as genai
import re

# --- [1. إعداد النظام والحماية] ---
# هذه النقطة حرجة جداً لمنع الشاشة السوداء
# نضعها داخل try-except لضمان عدم توقف النظام إذا تم الإعداد مسبقاً
try:
    st.set_page_config(page_title="Dev Squad | Stable", page_icon="🛡️", layout="wide")
except:
    pass

# --- [2. دوال الاتصال الذكي] ---
def call_ai_agent(agent_role, prompt_text):
    """محاولة الاتصال بعدة موديلات لضمان عدم التوقف"""
    # القائمة: نبدأ بالفلاش السريع، ثم البرو المستقر
    models = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']
    
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: API Key Missing. Please check Streamlit Secrets."

    genai.configure(api_key=api_key)

    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            # حرارة متوسطة (0.7) لتوازن الإبداع والدقة في الكود
            config = genai.types.GenerationConfig(temperature=0.7)
            response = model.generate_content(prompt_text, generation_config=config)
            return response.text
        except:
            continue # إذا فشل موديل، ننتقل للتالي بصمت
    return "⚠️ Error: All AI models are busy or unreachable."

def extract_code(text):
    """تنظيف الكود من النصوص الزائدة (Markdown)"""
    # نبحث عن الكود الموجود بين علامات
