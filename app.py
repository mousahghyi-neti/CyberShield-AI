import streamlit as st
import google.generativeai as genai
import os
import io
import sys
import subprocess
import re
import time
from contextlib import redirect_stdout

# --- إعدادات الصفحة ---
st.set_page_config(page_title="THE COUNCIL V40 | Mass Harvest", page_icon="🌾", layout="wide")

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1 { color: #00ff00; font-family: monospace; text-align:center; text-shadow: 0 0 10px #00ff00; }
    .agent-box { border-left: 4px solid #d4af37; background: #111; padding: 15px; margin-bottom: 10px; }
    .harvest-box { border-left: 4px solid #00ff00; background: #001a00; padding: 15px; margin-bottom: 10px; }
    .output-box { background: #0a0a0a; padding: 10px; border: 1px solid #00ff00; font-family: monospace; color: #00ff00; white-space: pre-wrap; height: 400px; overflow-y: scroll; }
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
    st.info("💡 V40 Strategy: **Mass Scraping (Limit 30)**\nLoops through links with delay.")

# --- الوكيل ---
class NativeAgent:
    def __init__(self, name, role, model_id):
        self.name = name
        self.role = role
        sys_instruction = f"""
        You are {name}, {role}.
        RULES:
        1. **USE curl_cffi**: `from curl_cffi import requests`. Impersonate "chrome110".
        2. **MASS SCAN**: 
           - Go to homepage.
           - Find ALL links with `/sms/` or similar pattern.
           - Deduplicate list.
           - Take the FIRST 30 links.
        3. **THE LOOP**:
           - Loop through the 30 links.
           - **CRITICAL**: Put `time.sleep(1.5)` inside the loop to be polite.
           - Extract messages from each.
        4. **PRINT**: Print "Scraping [x/30]: URL..." for progress. Print FINAL accumulated data.
        5. **NO ASYNC**: Sync code only.
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
    # التحقق من أن الكود وجد روابط وحاول الدخول إليها
    if "scanning" not in output.lower() and "scraping" not in output.lower(): 
        return False, "Loop logic didn't start."
    if "0 messages found" in output.lower() and "total" not in output.lower():
        return False, "Scraped pages but found NOTHING."
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

        # تحذير للمستخدم لأن العملية ستطول
        st.toast(f"جاري تنفيذ المحاولة {attempt+1}... قد تستغرق دقيقة (30 صفحة).")
        
        success, output = run_code_safe(code)
        is_valid, validation_msg = False, ""
        
        if success: is_valid, validation_msg = validate_output(output)

        if success and is_valid:
            return f"✅ Success:\n{output}", logs_ui, current_code_text
        else:
            error_details = output if not success else f"Logic Fail: {validation_msg}\nOutput Sample:\n{output[:500]}..."
            logs_ui.append(f"⚠️ Attempt {attempt+1} Failed. Retrying...")
            
            if attempt == max_retries: return f"❌ Failed:\n{error_details}", logs_ui, current_code_text
            
            fix_prompt = f"""
            Execution failed or found nothing.
            Output: "{error_details}"
            
            FIX PLAN:
            1. Go to 'https://receive-smss.com/'.
            2. Find ALL hrefs containing '/sms/'.
            3. Limit list to 30 unique links.
            4. Loop through them using `for link in links:`.
            5. Add `import time` and `time.sleep(1)` in the loop.
            6. Scrape messages.
            7. Print stats: "Found X messages in [URL]".
            8. Use 'curl_cffi'.
            """
            current_code_text = fixer_agent.ask(fix_prompt, context=context_plan)
            attempt += 1
            
    return "Unknown", logs_ui, current_code_text

# --- الواجهة ---
st.markdown("<h1>🌾 THE COUNCIL V40</h1>", unsafe_allow_html=True)
st.caption(f"Strategy: **Mass Harvesting (30 Nodes)** | Engine: **{selected_model}**")

st.warning("⚠️ تنبيه: البحث في 30 صفحة قد يستغرق حوالي 30-60 ثانية. كن صبوراً.")

if st.button("بدء الحصاد (Start Harvest) ⚡"):
    results = st.container()
    
    planner = NativeAgent("Navigator", "Plan mass scraping logic.", selected_model)
    coder = NativeAgent("Developer", "Write loop scraping code.", selected_model)
    fixer = NativeAgent("The Fixer", "Fix loop/scraping errors.", selected_model)
    
    with results:
        with st.spinner("1. رسم خطة الهجوم الواسع..."):
            plan = planner.ask("Goal: Scrape 30 different active numbers from 'https://receive-smss.com/' and collect all SMS messages. Use a loop and delays.")
            st.markdown(f"<div class='harvest-box'><div class='agent-name' style='color:#00ff00'>🧭 Navigator</div>{plan}</div>", unsafe_allow_html=True)
        
        with st.spinner("2. كتابة كود الحصاد..."):
            initial_code = coder.ask("Write python code using curl_cffi. 1. Get homepage. 2. Find all /sms/ links. 3. Loop first 30. 4. Scrape & Print.", context=plan)
            final_output, debug_logs, final_code = smart_execute_with_hive(initial_code, fixer, plan)
            
            if debug_logs:
                log_html = "<br>".join([f"<code>{l}</code>" for l in debug_logs])
                st.markdown(f"<div class='install-box'>{log_html}</div>", unsafe_allow_html=True)
            
            st.markdown(f"<div class='agent-box'><div class='agent-name'>💻 Live Code</div>{final_code}</div>", unsafe_allow_html=True)
            
            if "Success" in final_output:
                clean_out = final_output.replace("✅ Success:\n", "")
                st.markdown(f"### 💰 الغلة الكاملة (The Harvest):")
                st.markdown(f"<div class='output-box'>{clean_out}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='error-box'>{final_output}</div>", unsafe_allow_html=True)
    
    st.success("✅ العملية انتهت.")
