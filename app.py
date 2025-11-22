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
    page_title="THE COUNCIL V32 | Heavy Artillery",
    page_icon="💀",
    layout="wide"
)

# --- التصميم ---
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
        st.warning("Using default model.")
        selected_model = "models/gemini-1.5-flash"
    else:
        default_ix = 0
        for i, m in enumerate(available_models):
            if "flash" in m:
                default_ix = i
                break
        selected_model = st.selectbox("اختر الموديل:", available_models, index=default_ix)
    
    st.divider()
    st.info("💡 V32: Pre-loaded Arsenal + User Install Mode")

# --- 3. كلاس الوكيل ---
class NativeAgent:
    def __init__(self, name, role, model_id):
        self.name = name
        self.role = role
        sys_instruction = f"""
        You are {name}, {role}.
        CODING RULES:
        1. Use python blocks: ```python ... ```
        2. ALWAYS declare dependencies: # pip: requests beautifulsoup4
        3. ERROR FIXING: Return ONLY the corrected code.
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

# --- 4. دوال المعالجة (التحديث: التثبيت بصلاحيات --user) ---

def extract_code(text):
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if not match:
        match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    return match.group(1) if match else None

def ensure_dependencies(code):
    logs = []
    matches = re.findall(r"#\s*pip:\s*([^\n\r]*)", code)
    
    all_libs = []
    for match in matches:
        clean_match = match.split("#")[0]
        # التقسيم الذكي (فواصل ومسافات)
        libs = [lib.strip() for lib in re.split(r'[,\s]+', clean_match) if lib.strip()]
        all_libs.extend(libs)
    
    all_libs = list(set(all_libs))
    
    if all_libs:
        logs.append(f"📦 Requirements check: {', '.join(all_libs)}")
        for lib in all_libs:
            try:
                __import__(lib)
                # logs.append(f"🔹 {lib} is pre-installed.") # لا داعي لإزعاج المستخدم إذا كانت مثبتة
            except ImportError:
                try:
                    # V32 FIX: إضافة --user لتجاوز مشاكل الصلاحيات
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", lib])
                    logs.append(f"✅ Installed: {lib}")
                except Exception as e:
                    try:
                        # محاولة أخيرة بدون --user
                        subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                        logs.append(f"✅ Installed (System): {lib}")
                    except:
                        logs.append(f"❌ Failed to install: {lib} (Try adding it to requirements.txt)")
    return logs

def run_code_safe(code):
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(code, globals())
        return True, buffer.getvalue()
    except Exception as e:
        return False, str(e)

# --- 5. حلقة التصحيح الذاتي ---
def smart_execute_with_retry(initial_code_response, agent, context_plan):
    current_code_text = initial_code_response
    max_retries = 3
    attempt = 0
    logs_ui = []

    while attempt <= max_retries:
        code = extract_code(current_code_text)
        if not code:
            return "⚠️ No code found.", logs_ui, current_code_text

        dep_logs = ensure_dependencies(code)
        if dep_logs:
            logs_ui.extend(dep_logs)

        success, output = run_code_safe(code)

        if success:
            return f"✅ Execution Success:\n{output}", logs_ui, current_code_text
        else:
            error_msg = output
            logs_ui.append(f"⚠️ Attempt {attempt+1} Failed: {error_msg[:100]}...")
            
            if attempt == max_retries:
                return f"❌ Failed after retries. Error:\n{error_msg}", logs_ui, current_code_text
            
            fix_prompt = f"""
            Error: {error_msg}
            Fix the code. Ensure dependencies format: '# pip: lib1 lib2'.
            Return ONLY the corrected code.
            """
            current_code_text = agent.ask(fix_prompt, context=context_plan)
            attempt += 1
            
    return "Unknown Error", logs_ui, current_code_text

# --- الواجهة الرئيسية ---
st.markdown("<h1>💀 THE COUNCIL V32</h1>", unsafe_allow_html=True)
st.caption(f"Mode: **Pre-Loaded Arsenal** | Engine: **{selected_model}**")

mission = st.text_area("أدخل المهمة التقنية:", height=100, placeholder="مثال: استخرج البيانات من صفحة ويب.")

if st.button("تنفيذ الهجوم ⚡"):
    if not mission:
        st.warning("أدخل المهمة.")
    else:
        results = st.container()
        
        planner = NativeAgent("Strategist", "Plan logic.", selected_model)
        coder = NativeAgent("Developer", "Write python code.", selected_model)
        auditor = NativeAgent("Auditor", "Review results.", selected_model)

        with results:
            with st.spinner("1. التخطيط..."):
                plan = planner.ask(mission)
                st.markdown(f"<div class='agent-box'><div class='agent-name'>📐 Strategist</div>{plan}</div>", unsafe_allow_html=True)
            
            with st.spinner("2. الكود الأولي..."):
                initial_code = coder.ask("Write python code. Dependencies: # pip: lib1 lib2", context=plan)
            
            with st.spinner("3. التشغيل الذاتي..."):
                final_output, debug_logs, final_code = smart_execute_with_retry(initial_code, coder, plan)
                
                if debug_logs:
                    log_html = "<br>".join([f"<code>{l}</code>" for l in debug_logs])
                    st.markdown(f"<div class='install-box'>{log_html}</div>", unsafe_allow_html=True)
                
                st.markdown(f"<div class='agent-box'><div class='agent-name'>💻 Developer (Final Code)</div>{final_code}</div>", unsafe_allow_html=True)
                
                if "Success" in final_output:
                    st.markdown(f"<div class='output-box'>{final_output}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='error-box'>{final_output}</div>", unsafe_allow_html=True)

            with st.spinner("4. التدقيق..."):
                report = auditor.ask("Audit execution.", context=f"{plan}\n{final_output}")
                st.markdown(f"<div class='agent-box'><div class='agent-name'>🛡️ Auditor</div>{report}</div>", unsafe_allow_html=True)
                
        st.success("✅ تمت المهمة.")
