import streamlit as st
import google.generativeai as genai
import os
import io
import sys
import subprocess
import re
from contextlib import redirect_stdout

# --- إعدادات الصفحة ---
st.set_page_config(page_title="THE COUNCIL V38 | Navigator", page_icon="🧭", layout="wide")

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1 { color: #00ffcc; font-family: monospace; text-align:center; text-shadow: 0 0 10px #00ffcc; }
    .agent-box { border-left: 4px solid #d4af37; background: #111; padding: 15px; margin-bottom: 10px; }
    .nav-box { border-left: 4px solid #ff00ff; background: #1a001a; padding: 15px; margin-bottom: 10px; }
    .output-box { background: #0a0a0a; padding: 10px; border: 1px solid #00ff00; font-family: monospace; color: #00ff00; white-space: pre-wrap; }
    .error-box { background: #2a0000; padding: 10px; border: 1px solid #ff0000; color: #ffaaaa; }
</style>
""", unsafe_allow_html=True)

# --- المفاتيح ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("⚠️ مفتاح API مفقود.")
        st.stop()
except: st.stop()

# --- اختيار الموديل ---
@st.cache_data
def get_available_models():
    try: return [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except: return []

with st.sidebar:
    st.header("⚙️ المحرك")
    models = get_available_models()
    default_ix = next((i for i, m in enumerate(models) if "flash" in m), 0) if models else 0
    selected_model = st.selectbox("Model:", models if models else ["models/gemini-1.5-flash"], index=default_ix)
    st.info("💡 V38 Strategy: **Auto-Navigation**\nFinds live links automatically.")

# --- الوكيل ---
class NativeAgent:
    def __init__(self, name, role, model_id):
        self.name = name
        self.role = role
        sys_instruction = f"""
        You are {name}, {role}.
        RULES:
        1. **USE curl_cffi**: `from curl_cffi import requests`. Impersonate "chrome110".
        2. **PHASE 1 (NAVIGATION)**: First, write a function to scrape 'https://receive-smss.com/' homepage and find the first available 'View SMS' or number link.
        3. **PHASE 2 (EXTRACTION)**: Use that valid link to scrape messages.
        4. **NO ASYNC**: Sync code only.
        5. **PRINT**: Print "Target Found: [URL]" then print the messages.
        6. **DEPS**: # pip: curl_cffi beautifulsoup4
        """
        self.model = genai.GenerativeModel(model_name=model_id, system_instruction=sys_instruction)

    def ask(self, prompt, context=""):
        full_prompt = f"CONTEXT:\n{context}\n\nTASK:\n{prompt}"
        try:
            return self.model.generate_content(full_prompt).text
        except Exception as e: return f"Error: {str(e)}"

# --- الأدوات ---
def extract_code(text):
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if not match: match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    return match.group(1) if match else None

def ensure_dependencies(code):
    logs = []
    matches = re.findall(r"#\s*pip:\s*([^\n\r]*)", code)
    all_libs = []
    for match in matches:
        clean = match.split("#")[0]
        libs = [l.strip() for l in re.split(r'[,\s]+', clean) if l.strip()]
        all_libs.extend(libs)
    all_libs = list(set(all_libs))
    
    if all_libs:
        for lib in all_libs:
            try: __import__(lib)
            except ImportError:
                try: subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", lib]); logs.append(f"✅ Installed: {lib}")
                except: logs.append(f"❌ Failed: {lib}")
    return logs

def run_code_safe(code):
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer): exec(code, globals())
        return True, buffer.getvalue()
    except Exception as e: return False, str(e)

def validate_output(output):
    if "http error" in output.lower() or "404" in output.lower(): return False, "404/HTTP Error detected."
    if "no messages" in output.lower() and "target found" not in output.lower(): return False, "Script didn't find target."
    return True, "Valid"

# --- الحلقة الذكية ---
def smart_execute_with_hive(initial_code_response, fixer_agent, context_plan):
    current_code_text = initial_code_response
    max_retries = 3
    attempt = 0
    logs_ui = []

    while attempt <= max_retries:
        code = extract_code(current_code_text)
        if not code: return "⚠️ No code.", logs_ui, current_code_text

        dep_logs = ensure_dependencies(code)
        if dep_logs: logs_ui.extend(dep_logs)

        success, output = run_code_safe(code)
        is_valid, validation_msg = False, ""
        
        if success: is_valid, validation_msg = validate_output(output)

        if success and is_valid:
            return f"✅ Success:\n{output}", logs_ui, current_code_text
        else:
            error_details = output if not success else f"Logic Fail: {validation_msg}\nOutput:\n{output}"
            logs_ui.append(f"⚠️ Attempt {attempt+1} Failed: {validation_msg}...")
            
            if attempt == max_retries: return f"❌ Failed:\n{error_details}", logs_ui, current_code_text
            
            fix_prompt = f"""
            Execution failed.
            Output/Error: "{error_details}"
            
            TASK:
            1. The previous URL might be dead (404).
            2. Write code to GO TO 'https://receive-smss.com/' HOMEPAGE first.
            3. Find the first `<a>` tag with `href` starting with `/sms/`.
            4. Construct the full URL and scrape THAT.
            5. Use 'curl_cffi'.
            
            Return ONLY the corrected code.
            """
            current_code_text = fixer_agent.ask(fix_prompt, context=context_plan)
            attempt += 1
            
    return "Unknown", logs_ui, current_code_text

# --- الواجهة ---
st.markdown("<h1>🧭 THE COUNCIL V38</h1>", unsafe_allow_html=True)
st.caption(f"Strategy: **Dynamic Target Acquisition** | Engine: **{selected_model}**")

st.info("سيقوم النظام الآن بالبحث عن رقم **حي** بنفسه، ولن يعتمد على روابط قديمة.")

if st.button("إطلاق الملاح (Start Navigation) ⚡"):
    results = st.container()
    
    planner = NativeAgent("Navigator", "Plan dynamic scraping.", selected_model)
    coder = NativeAgent("Developer", "Write scraping code.", selected_model)
    fixer = NativeAgent("The Fixer", "Fix dead links by finding new ones.", selected_model)
    
    with results:
        with st.spinner("1. تحديد المسار..."):
            # لاحظ المهمة الجديدة: اذهب للصفحة الرئيسية وجد رابطاً
            plan = planner.ask("Goal: Go to https://receive-smss.com/, find the first active number link on the homepage, and scrape its messages.")
            st.markdown(f"<div class='nav-box'><div class='agent-name' style='color:#ff00ff'>🧭 Navigator</div>{plan}</div>", unsafe_allow_html=True)
        
        with st.spinner("2. تشغيل الكود الديناميكي..."):
            initial_code = coder.ask("Write code to: 1. Get homepage using curl_cffi. 2. Extract first number link. 3. Scrape messages from that link. Print everything.", context=plan)
            final_output, debug_logs, final_code = smart_execute_with_hive(initial_code, fixer, plan)
            
            if debug_logs:
                log_html = "<br>".join([f"<code>{l}</code>" for l in debug_logs])
                st.markdown(f"<div class='install-box'>{log_html}</div>", unsafe_allow_html=True)
            
            st.markdown(f"<div class='agent-box'><div class='agent-name'>💻 Developer (Live Code)</div>{final_code}</div>", unsafe_allow_html=True)
            
            if "Success" in final_output:
                clean_out = final_output.replace("✅ Success:\n", "")
                st.markdown(f"### 🎯 الهدف النشط والرسائل:")
                st.markdown(f"<div class='output-box'>{clean_out}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='error-box'>{final_output}</div>", unsafe_allow_html=True)
    
    st.success("✅ تمت المهمة.")
