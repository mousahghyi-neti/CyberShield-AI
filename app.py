import streamlit as st
import google.generativeai as genai
import os
import io
import sys
import subprocess
import re
from contextlib import redirect_stdout

# --- إعدادات الصفحة ---
st.set_page_config(page_title="THE COUNCIL V43 | Brute Regex", page_icon="🔨", layout="wide")

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1 { color: #ff0000; font-family: monospace; text-align:center; text-shadow: 0 0 10px red; }
    .agent-box { border-left: 4px solid #d4af37; background: #111; padding: 15px; margin-bottom: 10px; }
    .output-box { background: #0a0a0a; padding: 10px; border: 1px solid #00ff00; font-family: monospace; color: #00ff00; white-space: pre-wrap; }
    .error-box { background: #2a0000; padding: 10px; border: 1px solid #ff0000; color: #ffaaaa; }
</style>
""", unsafe_allow_html=True)

# --- المفاتيح ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else: st.error("⚠️ API Key Missing"); st.stop()
except: st.stop()

# --- المحرك ---
@st.cache_data
def get_available_models():
    try: return [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except: return []

with st.sidebar:
    st.header("⚙️ المحرك")
    models = get_available_models()
    default_ix = next((i for i, m in enumerate(models) if "flash" in m), 0) if models else 0
    selected_model = st.selectbox("Model:", models if models else ["models/gemini-1.5-flash"], index=default_ix)
    st.info("💡 V43: **Regex Bruteforce**\nIgnores HTML classes, hunts patterns.")

# --- الوكيل ---
class NativeAgent:
    def __init__(self, name, role, model_id):
        self.name = name
        self.role = role
        sys_instruction = f"""
        You are {name}, {role}.
        
        STRATEGY:
        1. **IGNORE CLASSES**: Do not rely on 'btn_view' or 'numb' or 'msgg'. They change too often.
        2. **REGEX LINK FINDING**: Find any `<a>` where `href` matches regex `r"/sms/\d+"`.
        3. **REGEX MESSAGE FINDING**: On the message page, look for text patterns like "ago" (e.g., "2 mins ago", "seconds ago"). The message content is usually near this timestamp.
        4. **USE curl_cffi**: Impersonate "chrome110".
        5. **PRINT**: Print the final extracted messages clearly.
        6. **DEPS**: # pip: curl_cffi beautifulsoup4
        """
        self.model = genai.GenerativeModel(model_name=model_id, system_instruction=sys_instruction)

    def ask(self, prompt, context=""):
        full_prompt = f"CONTEXT:\n{context}\n\nTASK:\n{prompt}"
        try: return self.model.generate_content(full_prompt).text
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
    if "http error" in output.lower(): return False, "HTTP Error."
    if "no link" in output.lower() or "no message" in output.lower(): return False, "Extraction Failed."
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
            logs_ui.append(f"⚠️ Attempt {attempt+1} Failed. Retrying with Regex...")
            
            if attempt == max_retries: return f"❌ Failed:\n{error_details}", logs_ui, current_code_text
            
            fix_prompt = f"""
            Execution failed. Output: "{error_details}"
            
            NEW PLAN (BRUTE FORCE):
            1. Forget class names.
            2. To find number link: iterate ALL `<a>` tags. If href matches regex `\/sms\/\d+`, grab it.
            3. To find messages: Look for text containing "ago" (time). The parent/sibling of that text likely holds the message.
            4. Use 'curl_cffi'.
            
            Return ONLY the corrected code.
            """
            current_code_text = fixer_agent.ask(fix_prompt, context=context_plan)
            attempt += 1
            
    return "Unknown", logs_ui, current_code_text

# --- الواجهة ---
st.markdown("<h1>🔨 THE COUNCIL V43</h1>", unsafe_allow_html=True)
st.caption(f"Mode: **Brute Regex Pattern Matching** | Engine: **{selected_model}**")

st.info("النظام الآن يتجاهل تصميم الموقع ويبحث عن 'أنماط البيانات' مباشرة.")

if st.button("الكسر بالقوة (Brute Force) ⚡"):
    results = st.container()
    
    planner = NativeAgent("Navigator", "Plan regex-based scraping.", selected_model)
    coder = NativeAgent("Developer", "Write python code using Regex, not Classes.", selected_model)
    fixer = NativeAgent("The Fixer", "Fix logic failures with broader regex.", selected_model)
    
    with results:
        with st.spinner("1. التخطيط..."):
            plan = planner.ask("Target: receive-smss.com. Goal: Find link matching /sms/digits. Then find text matching 'ago' pattern.")
            st.markdown(f"<div class='agent-box'><div class='agent-name' style='color:#d4af37'>📐 Strategist</div>{plan}</div>", unsafe_allow_html=True)
        
        with st.spinner("2. تشغيل الكود..."):
            initial_code = coder.ask("Write python code. 1. Get homepage. 2. Regex search link. 3. Regex search messages. Print results.", context=plan)
            final_output, debug_logs, final_code = smart_execute_with_hive(initial_code, fixer, plan)
            
            if debug_logs:
                log_html = "<br>".join([f"<code>{l}</code>" for l in debug_logs])
                st.markdown(f"<div class='install-box'>{log_html}</div>", unsafe_allow_html=True)
            
            st.markdown(f"<div class='agent-box'><div class='agent-name'>💻 Developer (Live Code)</div>{final_code}</div>", unsafe_allow_html=True)
            
            if "Success" in final_output:
                clean_out = final_output.replace("✅ Success:\n", "")
                st.markdown(f"### 🔨 النتيجة الغاشمة:")
                st.markdown(f"<div class='output-box'>{clean_out}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='error-box'>{final_output}</div>", unsafe_allow_html=True)
    
    st.success("✅ تمت المهمة.")
