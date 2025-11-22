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
    page_title="THE COUNCIL V37 | Adaptive Hunter",
    page_icon="💀",
    layout="wide"
)

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1 { color: #ff0000; font-family: 'Courier New', monospace; text-align:center; text-shadow: 0 0 10px red; }
    .agent-box { border-left: 4px solid #d4af37; background: #111; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .fixer-box { border-left: 4px solid #00ffff; background: #001111; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .output-box { background: #0a0a0a; padding: 10px; border: 1px solid #00ff00; font-family: monospace; color: #00ff00; white-space: pre-wrap; }
    .error-box { background: #2a0000; padding: 10px; border: 1px solid #ff0000; color: #ffaaaa; font-size: 0.9em; }
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

# --- اختيار الموديل ---
@st.cache_data
def get_available_models():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return models
    except: return []

with st.sidebar:
    st.header("⚙️ المحرك")
    models = get_available_models()
    if models:
        default_ix = next((i for i, m in enumerate(models) if "flash" in m), 0)
        selected_model = st.selectbox("Model:", models, index=default_ix)
    else:
        selected_model = "models/gemini-1.5-flash"
    
    st.info("💡 V37 Strategy: **Multi-Selector Scraping**\n(Table -> Div -> Text Pattern)")

# --- كلاس الوكيل ---
class NativeAgent:
    def __init__(self, name, role, model_id):
        self.name = name
        self.role = role
        sys_instruction = f"""
        You are {name}, {role}.
        
        RULES:
        1. **USE curl_cffi**: `from curl_cffi import requests`. Use `impersonate="chrome110"`.
        2. **NO ASYNC**: Synchronous code only.
        3. **ADAPTIVE SCRAPING**: 
           - Many sites DO NOT use `<table>`. 
           - You MUST search for `<div>` structures with classes like 'row', 'sms-item', 'msg-item', 'list-item'.
           - Look for text inside elements.
        4. **ROBUSTNESS**: Handle 404/Connection errors gracefully (skip bad URLs).
        5. **PRINT**: You MUST print the final found data.
        6. **DEPS**: # pip: curl_cffi beautifulsoup4
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

# --- أدوات المعالجة ---
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
        logs.append(f"📦 Deps check: {', '.join(all_libs)}")
        for lib in all_libs:
            try:
                __import__(lib)
            except ImportError:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", lib])
                    logs.append(f"✅ Installed: {lib}")
                except:
                    logs.append(f"❌ Failed: {lib}")
    return logs

def run_code_safe(code):
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(code, globals())
        return True, buffer.getvalue()
    except Exception as e:
        return False, str(e)

# --- المدقق الذكي ---
def validate_output(output):
    # إذا كان المخرج يحتوي على رسائل فشل فقط
    if "no unique sms" in output.lower() or "no data found" in output.lower():
        return False, "Script ran but found ZERO data. Selector logic is likely wrong."
    if not output.strip():
        return False, "No output printed."
    return True, "Valid"

# --- حلقة الخلية ---
def smart_execute_with_hive(initial_code_response, fixer_agent, context_plan):
    current_code_text = initial_code_response
    max_retries = 4
    attempt = 0
    logs_ui = []

    while attempt <= max_retries:
        code = extract_code(current_code_text)
        if not code: return "⚠️ No code found.", logs_ui, current_code_text

        dep_logs = ensure_dependencies(code)
        if dep_logs: logs_ui.extend(dep_logs)

        success, output = run_code_safe(code)
        
        is_valid = False
        validation_msg = ""
        if success:
            is_valid, validation_msg = validate_output(output)

        if success and is_valid:
            return f"✅ Success:\n{output}", logs_ui, current_code_text
        else:
            error_details = output if not success else f"Logic Fail: {validation_msg}\nOutput:\n{output}"
            logs_ui.append(f"⚠️ Attempt {attempt+1} Rejected. Adapting...")
            
            if attempt == max_retries:
                return f"❌ Failed. Final Status:\n{error_details}", logs_ui, current_code_text
            
            fix_prompt = f"""
            Execution Result:
            "{error_details}"
            
            The code failed to extract data or crashed.
            ADVICE:
            1. If 'No data found', STOP looking for <table>. Look for <div> with classes: 'msg', 'sms', 'row', 'list-item', 'text-content'.
            2. Some sites hide data in <script> tags or JSON. Try printing the raw HTML soup.find() to debug.
            3. Use 'curl_cffi' impersonate='chrome110'.
            
            Fix the code and return ONLY the code block.
            """
            current_code_text = fixer_agent.ask(fix_prompt, context=context_plan)
            attempt += 1
            
    return "Unknown", logs_ui, current_code_text

# --- الواجهة ---
st.markdown("<h1>💀 THE COUNCIL V37</h1>", unsafe_allow_html=True)
st.caption(f"Objective: **Adaptive Extraction** | Engine: **{selected_model}**")

# روابط اختبار حقيقية تعمل في 2025 (أو أقرب وقت ممكن)
default_urls = """
https://receive-smss.com/sms/447418340677/
https://anonymsms.com/number/19137933987/
""".strip()

mission = st.text_area("المهمة:", height=100, value=f"استخرج الرسائل (Sender, Message) من هذه الروابط:\n{default_urls}")

if st.button("الصيد (Hunt) ⚡"):
    if not mission:
        st.warning("أدخل المهمة.")
    else:
        results = st.container()
        
        planner = NativeAgent("Strategist", "Plan extraction logic.", selected_model)
        coder = NativeAgent("Developer", "Write robust scraper code.", selected_model)
        fixer = NativeAgent("The Fixer", "Fix scraping logic. Switch selectors if needed.", selected_model)
        
        with results:
            with st.spinner("1. التخطيط..."):
                plan = planner.ask(mission)
                st.markdown(f"<div class='agent-box'><div class='agent-name'>📐 Strategist</div>{plan}</div>", unsafe_allow_html=True)
            
            with st.spinner("2. المبرمج (Code Generation)..."):
                initial_code = coder.ask("Write python code using curl_cffi. Try BOTH table and div selectors. Print results.", context=plan)
            
            with st.spinner("3. التحقق والتصحيح (The Loop)..."):
                final_output, debug_logs, final_code = smart_execute_with_hive(initial_code, fixer, plan)
                
                if debug_logs:
                    log_html = "<br>".join([f"<code>{l}</code>" for l in debug_logs])
                    st.markdown(f"<div class='install-box'>{log_html}</div>", unsafe_allow_html=True)
                
                st.markdown(f"<div class='fixer-box'><div class='agent-name' style='color:#00ffff'>🔧 Final Code</div>{final_code}</div>", unsafe_allow_html=True)
                
                if "Success" in final_output:
                    clean_out = final_output.replace("✅ Success:\n", "")
                    st.markdown(f"### 📊 الغنيمة (The Loot):")
                    st.markdown(f"<div class='output-box'>{clean_out}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='error-box'>{final_output}</div>", unsafe_allow_html=True)
        
        st.success("✅ العملية انتهت.")
