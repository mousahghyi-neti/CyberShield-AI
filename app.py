import streamlit as st
import google.generativeai as genai
import os
import io
import sys
import subprocess
import re
from contextlib import redirect_stdout

# --- إعدادات الصفحة ---
st.set_page_config(page_title="THE COUNCIL V39 | Hunter", page_icon="🎯", layout="wide")

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
    st.info("💡 V39 Strategy: **Regex Navigation**\nSearches for '/sms/' pattern.")

# --- الوكيل ---
class NativeAgent:
    def __init__(self, name, role, model_id):
        self.name = name
        self.role = role
        sys_instruction = f"""
        You are {name}, {role}.
        RULES:
        1. **USE curl_cffi**: `from curl_cffi import requests`. Impersonate "chrome110".
        2. **NAVIGATION LOGIC**: 
           - Go to 'https://receive-smss.com/'.
           - Find ALL links (`<a>`).
           - Select the FIRST link where `href` contains `/sms/`.
           - IGNORE link text (it might be just a number).
        3. **EXTRACTION LOGIC**:
           - Go to that number link.
           - Find `<div>` with class `sms-item`, `msg-item`, or `row`.
           - Extract Sender and Message text.
        4. **PRINT**: Print "Found Target: [URL]" then the messages.
        5. **DEPS**: # pip: curl_cffi beautifulsoup4
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
    if "http error" in output.lower() or "404" in output.lower(): return False, "404/HTTP Error."
    if "no messages" in output.lower() and "target found" not in output.lower(): return False, "Navigation failed."
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
            Execution failed. Output: "{error_details}"
            
            FIX STRATEGY:
            1. The selector was wrong.
            2. Search for ANY link containing '/sms/' in href.
            3. Print the full HTML of the homepage if you can't find links, to debug.
            4. Use 'curl_cffi'.
            
            Return ONLY the corrected code.
            """
            current_code_text = fixer_agent.ask(fix_prompt, context=context_plan)
            attempt += 1
            
    return "Unknown", logs_ui, current_code_text

# --- الواجهة ---
st.markdown("<h1>🎯 THE COUNCIL V39</h1>", unsafe_allow_html=True)
st.caption(f"Strategy: **Broad Pattern Matching** | Engine: **{selected_model}**")

st.info("سيقوم النظام بالبحث عن أي رابط يحتوي على '/sms/' ويدخل إليه.")

if st.button("إطلاق الصياد (Hunt) ⚡"):
    results = st.container()
    
    planner = NativeAgent("Navigator", "Plan broad scraping.", selected_model)
    coder = NativeAgent("Developer", "Write scraping code.", selected_model)
    fixer = NativeAgent("The Fixer", "Fix navigation logic.", selected_model)
    
    with results:
        with st.spinner("1. التخطيط..."):
            plan = planner.ask("Goal: Go to https://receive-smss.com/, find ANY link with '/sms/' in href, go there, and scrape messages.")
            st.markdown(f"<div class='nav-box'><div class='agent-name' style='color:#ff00ff'>🧭 Navigator</div>{plan}</div>", unsafe_allow_html=True)
        
        with st.spinner("2. تشغيل الكود..."):
            initial_code = coder.ask("Write code to: 1. Get homepage using curl_cffi. 2. Find link with '/sms/'. 3. Scrape messages. Print output.", context=plan)
            final_output, debug_logs, final_code = smart_execute_with_hive(initial_code, fixer, plan)
            
            if debug_logs:
                log_html = "<br>".join([f"<code>{l}</code>" for l in debug_logs])
                st.markdown(f"<div class='install-box'>{log_html}</div>", unsafe_allow_html=True)
            
            st.markdown(f"<div class='agent-box'><div class='agent-name'>💻 Developer (Live Code)</div>{final_code}</div>", unsafe_allow_html=True)
            
            if "Success" in final_output:
                clean_out = final_output.replace("✅ Success:\n", "")
                st.markdown(f"### 🎯 النتائج:")
                st.markdown(f"<div class='output-box'>{clean_out}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='error-box'>{final_output}</div>", unsafe_allow_html=True)
    
    st.success("✅ تمت المهمة.")
