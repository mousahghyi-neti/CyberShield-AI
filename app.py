import streamlit as st
import google.generativeai as genai
import os
import io
import sys
import subprocess
import re
from contextlib import redirect_stdout

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V29 | Self-Healing",
    page_icon="❤️‍🩹",
    layout="wide"
)

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1 { color: #ff0000; font-family: 'Courier New', monospace; text-align:center; }
    .agent-box { border-left: 4px solid #d4af37; background: #111; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .agent-name { color: #d4af37; font-weight: bold; font-size: 1.1em; }
    .output-box { background: #0a0a0a; padding: 10px; border: 1px solid #00ff00; font-family: monospace; color: #00ff00; }
    .error-box { background: #2a0000; padding: 10px; border: 1px solid #ff0000; color: #ffaaaa; font-size: 0.9em; margin-bottom: 5px; }
    .fix-badge { background-color: #0066cc; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
</style>
""", unsafe_allow_html=True)

# --- تهيئة المفاتيح ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("⚠️ مفتاح API مفقود.")
        st.stop()
except:
    st.stop()

# --- 1. الفحص التلقائي للموديلات ---
@st.cache_data
def get_available_models():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return models
    except:
        return []

# --- 2. الشريط الجانبي ---
with st.sidebar:
    st.header("⚙️ المحرك")
    available_models = get_available_models()
    if not available_models:
        st.warning("جاري استخدام الافتراضي لعدم العثور على موديلات.")
        selected_model = "models/gemini-1.5-flash"
    else:
        selected_model = st.selectbox("اختر الموديل:", available_models, index=0)

# --- 3. المحرك الخاص بنا ---
class NativeAgent:
    def __init__(self, name, role, model_id):
        self.name = name
        self.role = role
        sys_instruction = f"""
        You are {name}, {role}.
        Coding Rules:
        1. If you write code, use python blocks ```python ... ```.
        2. If you need libraries, verify you add '# pip: libname' at the top.
        3. When fixing errors, ONLY return the corrected code block, do not explain too much.
        """
        self.model = genai.GenerativeModel(
            model_name=model_id,
            system_instruction=sys_instruction
        )

    def ask(self, prompt, context=""):
        full_prompt = f"CONTEXT:\n{context}\n\nTASK:\n{prompt}"
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

# --- 4. دوال الاستخراج والتثبيت ---
def extract_code(text):
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if not match:
        match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    return match.group(1) if match else None

def ensure_dependencies(code):
    match = re.search(r"#\s*pip:\s*(.*)", code)
    logs = []
    if match:
        libs = [lib.strip() for lib in match.group(1).split(",") if lib.strip()]
        for lib in libs:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                logs.append(f"📦 Installed: {lib}")
            except:
                logs.append(f"❌ Failed install: {lib}")
    return logs

def run_code_safe(code):
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(code, globals())
        return True, buffer.getvalue()
    except Exception as e:
        return False, str(e)

# --- 5. 🧠 خوارزمية التصحيح الذاتي (The Self-Healer) ---
def smart_execute_with_retry(initial_code_response, agent, context_plan):
    """
    هذه الدالة تحاول تشغيل الكود، وإذا فشل، تطلب من الوكيل إصلاحه وتعيد التشغيل.
    توفر استهلاك API لأنها لا تطلب خطة كاملة، بل تطلب إصلاحاً فقط.
    """
    current_code_text = initial_code_response
    max_retries = 3 # عدد المحاولات المسموحة
    attempt = 0
    logs_ui = []

    while attempt <= max_retries:
        # 1. استخراج الكود
        code = extract_code(current_code_text)
        if not code:
            return "⚠️ No code found to execute.", logs_ui

        # 2. تثبيت المكتبات
        dep_logs = ensure_dependencies(code)
        if dep_logs:
            logs_ui.append(f"Deps: {', '.join(dep_logs)}")

        # 3. التشغيل
        success, output = run_code_safe(code)

        if success:
            # نجحنا! نرجع النتيجة النهائية
            return f"✅ Execution Success:\n{output}", logs_ui, current_code_text
        else:
            # فشلنا!
            error_msg = output
            logs_ui.append(f"⚠️ Attempt {attempt+1} Failed: {error_msg[:50]}...")
            
            if attempt == max_retries:
                return f"❌ Failed after {max_retries} retries. Last Error:\n{error_msg}", logs_ui, current_code_text
            
            # 4. الطلب من الوكيل الإصلاح (Self-Healing Trigger)
            fix_prompt = f"""
            The code you wrote failed with this error:
            {error_msg}
            
            Here is the code that failed:
            {code}
            
            FIX IT. Return the full corrected code block only.
            """
            # هنا نستخدم الوكيل نفسه لإصلاح خطأه
            current_code_text = agent.ask(fix_prompt, context=context_plan)
            attempt += 1
            
    return "Unknown state", logs_ui, current_code_text

# --- الواجهة ---
st.markdown("<h1>❤️‍🩹 THE COUNCIL V29</h1>", unsafe_allow_html=True)
st.caption(f"Engine: **{selected_model}** | Mode: **Auto-Correction Loop**")

mission = st.text_area("أدخل المهمة:", height=100, placeholder="مثال: اكتب كود يطلب مكتبة غير موجودة ويطبع نصاً.")

if st.button("تنفيذ (مع التصحيح الذاتي) ⚡"):
    if not mission:
        st.warning("أدخل المهمة.")
    else:
        results = st.container()
        
        planner = NativeAgent("Strategist", "Plan logic.", selected_model)
        coder = NativeAgent("Developer", "Write python code.", selected_model)
        auditor = NativeAgent("Auditor", "Review results.", selected_model)

        with results:
            # 1. التخطيط
            with st.spinner("1. التخطيط..."):
                plan = planner.ask(mission)
                st.markdown(f"<div class='agent-box'><div class='agent-name'>📐 Strategist</div>{plan}</div>", unsafe_allow_html=True)
            
            # 2. البرمجة الأولية
            with st.spinner("2. كتابة الكود الأولي..."):
                initial_code = coder.ask("Write python code based on the plan.", context=plan)
                # لا نعرض الكود هنا فوراً، بل ننتظر التصحيح
            
            # 3. حلقة التنفيذ والتصحيح (The Loop)
            with st.spinner("3. الفحص، التشغيل، والإصلاح التلقائي..."):
                final_output, debug_logs, final_code = smart_execute_with_retry(initial_code, coder, plan)
                
                # عرض سجلات الإصلاح
                for log in debug_logs:
                    if "Failed" in log:
                        st.markdown(f"<div class='error-box'>{log}</div>", unsafe_allow_html=True)
                    else:
                        st.info(log)
                
                # عرض الكود النهائي الصحيح
                st.markdown(f"<div class='agent-box'><div class='agent-name'>💻 Developer (Final Code)</div>{final_code}</div>", unsafe_allow_html=True)
                
                # عرض النتيجة
                if "Success" in final_output:
                    st.markdown(f"<div class='output-box'>{final_output}</div>", unsafe_allow_html=True)
                else:
                    st.error(final_output)

            # 4. التدقيق النهائي
            with st.spinner("4. المراجعة النهائية..."):
                report = auditor.ask("Audit the final execution.", context=f"{plan}\n{final_output}")
                st.markdown(f"<div class='agent-box'><div class='agent-name'>🛡️ Auditor</div>{report}</div>", unsafe_allow_html=True)
                
        st.success("✅ الدورة مكتملة.")
