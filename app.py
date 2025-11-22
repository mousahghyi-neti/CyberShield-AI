import streamlit as st
import google.generativeai as genai
import os
import io
import sys
from contextlib import redirect_stdout

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V26 | Native Core",
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
</style>
""", unsafe_allow_html=True)

# --- المفاتيح ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("⚠️ مفتاح API مفقود.")
        st.stop()
except:
    st.stop()

# --- المحرك الخاص بنا (Our Custom Agent Class) ---
class NativeAgent:
    def __init__(self, name, role, model_name="gemini-1.5-flash"):
        self.name = name
        self.role = role
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=f"You are {name}, {role}. Be precise and professional."
        )

    def ask(self, prompt, context=""):
        # دمج السياق السابق مع الطلب الجديد
        full_prompt = f"CONTEXT:\n{context}\n\nYOUR TASK:\n{prompt}"
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

# --- أداة تنفيذ الكود (Manual Tool) ---
def execute_python_code(text):
    """
    يستخرج كود بايثون من النص وينفذه.
    """
    # استخراج الكود بين علامات ```python و ```
    import re
    code_match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if not code_match:
        code_match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    
    if not code_match:
        return "⚠️ No executable code found in the response."
    
    code = code_match.group(1)
    
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(code, globals())
        return f"✅ Execution Output:\n{buffer.getvalue()}"
    except Exception as e:
        return f"❌ Execution Error:\n{str(e)}"

# --- الواجهة ---
st.markdown("<h1>💀 THE COUNCIL V26 (Native)</h1>", unsafe_allow_html=True)
st.caption("Architecture: **Zero-Dependency Logic** (No CrewAI, No LangChain)")

mission = st.text_area("أدخل المهمة:", height=100, placeholder="مثال: اكتب كود بايثون لحساب مضروب الرقم 10.")

if st.button("تنفيذ الهجوم ⚡"):
    if not mission:
        st.warning("أدخل المهمة.")
    else:
        # حاوية النتائج
        results_container = st.container()
        
        # 1. تعريف الوكلاء (يدوياً)
        planner = NativeAgent("The Strategist", "Expert planner. Break down tasks into steps.")
        coder = NativeAgent("The Developer", "Python expert. Write clean code inside ```python blocks.")
        auditor = NativeAgent("The Auditor", "Security expert. Analyze results.")

        with results_container:
            # --- الخطوة 1: التخطيط ---
            with st.spinner("1. المخطط يضع الاستراتيجية..."):
                plan = planner.ask(mission)
                st.markdown(f"<div class='agent-box'><div class='agent-name'>📐 Strategist</div>{plan}</div>", unsafe_allow_html=True)
            
            # --- الخطوة 2: البرمجة ---
            with st.spinner("2. المبرمج يكتب الكود..."):
                # نمرر خطة المخطط للمبرمج
                code_response = coder.ask(f"Write python code to solve this based on the plan.", context=plan)
                st.markdown(f"<div class='agent-box'><div class='agent-name'>💻 Developer</div>{code_response}</div>", unsafe_allow_html=True)

            # --- الخطوة 3: التنفيذ الفعلي (الأداة) ---
            with st.spinner("3. تشغيل الكود في النظام..."):
                execution_result = execute_python_code(code_response)
                st.markdown(f"<div class='output-box'>{execution_result}</div>", unsafe_allow_html=True)

            # --- الخطوة 4: التدقيق ---
            with st.spinner("4. المدقق يراجع النتائج..."):
                # نمرر الكود ونتيجة التنفيذ للمدقق
                full_context = f"PLAN: {plan}\nCODE: {code_response}\nEXECUTION RESULT: {execution_result}"
                audit_report = auditor.ask("Review the code execution and confirm success.", context=full_context)
                st.markdown(f"<div class='agent-box'><div class='agent-name'>🛡️ Auditor</div>{audit_report}</div>", unsafe_allow_html=True)
                
        st.success("✅ تمت المهمة بنجاح.")
