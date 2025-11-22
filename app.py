import streamlit as st
import google.generativeai as genai
import os
import io
import sys
from contextlib import redirect_stdout

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V27 | Auto-Discovery",
    page_icon="💀",
    layout="wide"
)

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1 { color: #ff0000; font-family: 'Courier New', monospace; text-align:center; }
    .agent-box { border-left: 4px solid #d4af37; background: #111; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .agent-name { color: #d4af37; font-weight: bold; font-size: 1.1em; }
    .output-box { background: #0a0a0a; padding: 10px; border: 1px solid #333; font-family: monospace; color: #00ff00; }
    .stSelectbox div[data-baseweb="select"] > div { background-color: #1a1a1a; color: white; }
</style>
""", unsafe_allow_html=True)

# --- 1. تهيئة المفاتيح ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("⚠️ مفتاح API مفقود.")
        st.stop()
except:
    st.stop()

# --- 2. الفحص التلقائي للموديلات (The Scanner) ---
# هذه الدالة هي الحل لمشكلتك. لن نخمن الاسم، بل سنجلبه من جوجل.
@st.cache_data # نستخدم الكاش لعدم تكرار الطلب
def get_available_models():
    try:
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # تنظيف الاسم (حذف models/ للعرض الجميل)
                models.append(m.name)
        return models
    except Exception as e:
        return [f"Error fetching models: {e}"]

# --- الشريط الجانبي لاختيار الموديل ---
with st.sidebar:
    st.header("⚙️ المحرك")
    available_models = get_available_models()
    
    if not available_models:
        st.error("لم يتم العثور على موديلات متاحة لحسابك!")
        st.stop()
        
    # القائمة المنسدلة - اختر منها ما يعمل لديك سابقاً
    selected_model = st.selectbox(
        "اختر الموديل المتاح لك:",
        available_models,
        index=0
    )
    st.success(f"تم تفعيل: {selected_model}")

# --- المحرك الخاص بنا (Native Agent) ---
class NativeAgent:
    def __init__(self, name, role, model_id):
        self.name = name
        self.role = role
        # نستخدم الموديل الذي اخترته أنت من القائمة
        self.model = genai.GenerativeModel(
            model_name=model_id,
            system_instruction=f"You are {name}, {role}. Act accordingly."
        )

    def ask(self, prompt, context=""):
        full_prompt = f"CONTEXT:\n{context}\n\nTASK:\n{prompt}"
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

# --- أداة تنفيذ الكود ---
def execute_python_code(text):
    import re
    code_match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if not code_match:
        code_match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    
    if not code_match:
        return "⚠️ No code found."
    
    code = code_match.group(1)
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(code, globals())
        return f"✅ Output:\n{buffer.getvalue()}"
    except Exception as e:
        return f"❌ Error:\n{str(e)}"

# --- الواجهة ---
st.markdown("<h1>💀 THE COUNCIL V27</h1>", unsafe_allow_html=True)
st.caption(f"Running on: **{selected_model}** (Auto-Detected)")

mission = st.text_area("أدخل المهمة:", height=100)

if st.button("تنفيذ ⚡"):
    if not mission:
        st.warning("أدخل المهمة.")
    else:
        results = st.container()
        
        # تعريف الوكلاء بالموديل المختار
        planner = NativeAgent("Strategist", "Plan execution.", selected_model)
        coder = NativeAgent("Developer", "Write python code.", selected_model)
        auditor = NativeAgent("Auditor", "Review results.", selected_model)

        with results:
            # 1. التخطيط
            with st.spinner("التخطيط..."):
                plan = planner.ask(mission)
                st.markdown(f"<div class='agent-box'><div class='agent-name'>📐 Strategist</div>{plan}</div>", unsafe_allow_html=True)
            
            # 2. البرمجة
            with st.spinner("البرمجة..."):
                code_res = coder.ask(f"Write python code for this plan.", context=plan)
                st.markdown(f"<div class='agent-box'><div class='agent-name'>💻 Developer</div>{code_res}</div>", unsafe_allow_html=True)

            # 3. التنفيذ
            with st.spinner("التنفيذ..."):
                exec_res = execute_python_code(code_res)
                st.markdown(f"<div class='output-box'>{exec_res}</div>", unsafe_allow_html=True)

            # 4. التدقيق
            with st.spinner("التدقيق..."):
                final_report = auditor.ask("Analyze execution result.", context=f"{plan}\n{code_res}\n{exec_res}")
                st.markdown(f"<div class='agent-box'><div class='agent-name'>🛡️ Auditor</div>{final_report}</div>", unsafe_allow_html=True)
                
        st.success("✅ تم.")
