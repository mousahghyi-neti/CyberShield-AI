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
    page_title="THE COUNCIL V30 | Perfected",
    page_icon="💀",
    layout="wide"
)

# --- التصميم (Dark & Gold) ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1 { color: #ff0000; font-family: 'Courier New', monospace; text-align:center; text-shadow: 0 0 10px red; }
    .agent-box { border-left: 4px solid #d4af37; background: #111; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .agent-name { color: #d4af37; font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
    .output-box { background: #0a0a0a; padding: 10px; border: 1px solid #00ff00; font-family: monospace; color: #00ff00; }
    .install-box { background: #001a33; padding: 8px; border: 1px solid #0066cc; color: #66b3ff; font-size: 0.85em; margin-bottom: 5px; }
    .error-box { background: #2a0000; padding: 10px; border: 1px solid #ff0000; color: #ffaaaa; font-size: 0.9em; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- تهيئة المفاتيح ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("⚠️ مفتاح API مفقود. يرجى إضافته في Secrets.")
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
    st.header("⚙️ المحرك (Engine)")
    available_models = get_available_models()
    if not available_models:
        st.warning("لم يتم العثور على موديلات، جاري استخدام الافتراضي.")
        selected_model = "models/gemini-1.5-flash"
    else:
        # نختار الفلاش كخيار افتراضي إذا وجد
        default_ix = 0
        for i, m in enumerate(available_models):
            if "flash" in m:
                default_ix = i
                break
        selected_model = st.selectbox("اختر الموديل:", available_models, index=default_ix)
    
    st.divider()
    st.info("💡 V30 Features:\n- Self-Healing Loop\n- Multi-Line Pip Install\n- Native Google Core")

# --- 3. كلاس الوكيل (Native Agent) ---
class NativeAgent:
    def __init__(self, name, role, model_id):
        self.name = name
        self.role = role
        # تعليمات صارمة للمكتبات
        sys_instruction = f"""
        You are {name}, {role}.
        
        CODING RULES:
        1. Use python blocks: ```python ... ```
        2. DEPENDENCIES: If you need external libraries (requests, bs4, pandas, etc.), 
           you MUST declare them at the top of the code using comments like this:
           # pip: requests
           # pip: beautifulsoup4
           
        3. ERROR FIXING: If asked to fix code, return ONLY the full corrected code block.
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

# --- 4. دوال المعالجة الأساسية ---

def extract_code(text):
    """استخراج الكود من بين علامات الماركداون"""
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if not match:
        match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    return match.group(1) if match else None

def ensure_dependencies(code):
    """
    (V30) النسخة المثالية: تلتقط كل المكتبات من كل الأسطر
    """
    logs = []
    # البحث عن كل الأسطر التي تحتوي على # pip:
    matches = re.findall(r"#\s*pip:\s*([^\n\r]*)", code)
    
    all_libs = []
    for match in matches:
        # تنظيف الفواصل والتعليقات الجانبية
        clean_match = match.split("#")[0]
        libs = [lib.strip() for lib in clean_match.split(",") if lib.strip()]
        all_libs.extend(libs)
    
    # إزالة التكرار
    all_libs = list(set(all_libs))
    
    if all_libs:
        logs.append(f"📦 Requirements found: {', '.join(all_libs)}")
        for lib in all_libs:
            try:
                # محاولة استيراد سريعة
                __import__(lib)
            except ImportError:
                try:
                    # التثبيت الفعلي
                    subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                    logs.append(f"✅ Installed: {lib}")
                except Exception as e:
                    # محاولة أخيرة (force install) لأسماء مثل bs4
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                        logs.append(f"✅ Installed (Force): {lib}")
                    except:
                        logs.append(f"❌ Failed to install: {lib}")
    return logs

def run_code_safe(code):
    """تشغيل الكود والتقاط المخرجات أو الأخطاء"""
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(code, globals())
        return True, buffer.getvalue()
    except Exception as e:
        return False, str(e)

# --- 5. حلقة التصحيح الذاتي (The Loop) ---
def smart_execute_with_retry(initial_code_response, agent, context_plan):
    current_code_text = initial_code_response
    max_retries = 3
    attempt = 0
    logs_ui = []

    while attempt <= max_retries:
        # 1. استخراج
        code = extract_code(current_code_text)
        if not code:
            return "⚠️ No code found.", logs_ui, current_code_text

        # 2. تثبيت
        dep_logs = ensure_dependencies(code)
        if dep_logs:
            logs_ui.extend(dep_logs)

        # 3. تشغيل
        success, output = run_code_safe(code)

        if success:
            return f"✅ Execution Success:\n{output}", logs_ui, current_code_text
        else:
            error_msg = output
            logs_ui.append(f"⚠️ Attempt {attempt+1} Failed: {error_msg[:100]}...")
            
            if attempt == max_retries:
                return f"❌ Failed after retries. Error:\n{error_msg}", logs_ui, current_code_text
            
            # طلب الإصلاح من الوكيل
            fix_prompt = f"""
            Your code failed with this error:
            {error_msg}
            
            Fix the code. Ensure you declare dependencies like '# pip: libname'.
            Return only the full corrected code block.
            """
            current_code_text = agent.ask(fix_prompt, context=context_plan)
            attempt += 1
            
    return "Unknown Error", logs_ui, current_code_text

# --- الواجهة الرئيسية ---
st.markdown("<h1>💀 THE COUNCIL V30</h1>", unsafe_allow_html=True)
st.caption(f"Mode: **Perfected Autonomous Loop** | Engine: **{selected_model}**")

mission = st.text_
