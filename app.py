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
st.set_page_config(
    page_title="THE COUNCIL V41 | Forensic Learning",
    page_icon="🧠",
    layout="wide"
)

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    h1 { color: #ff3333; font-family: 'Courier New', monospace; text-align:center; text-shadow: 0 0 15px red; }
    .agent-box { border-left: 4px solid #d4af37; background: #111; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .fixer-box { border-left: 4px solid #00ffff; background: #001a1a; padding: 15px; margin-bottom: 10px; }
    .output-box { background: #0a0a0a; padding: 10px; border: 1px solid #00ff00; font-family: monospace; color: #00ff00; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
    .error-box { background: #2a0000; padding: 10px; border: 1px solid #ff0000; color: #ffaaaa; font-size: 0.9em; }
    .html-dump { font-size: 0.7em; color: #555; background: #000; border: 1px dashed #333; padding: 5px; max-height: 100px; overflow: hidden; }
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
    st.info("💡 V41: **Forensic Debugging**\nFeeds raw HTML back to AI on failure.")

# --- الوكيل ---
class NativeAgent:
    def __init__(self, name, role, model_id):
        self.name = name
        self.role = role
        sys_instruction = f"""
        You are {name}, {role}.
        RULES:
        1. **USE curl_cffi**: `from curl_cffi import requests`. Impersonate "chrome110".
        2. **NO ASYNC**: Use synchronous code only.
        3. **PRINT**: You MUST print the found data using `print()`.
        4. **DEPS**: # pip: curl_cffi beautifulsoup4
        """
        self.model = genai.GenerativeModel(model_name=model_id, system_instruction=sys_instruction)

    def ask(self, prompt, context=""):
        full_prompt = f"CONTEXT:\n{context}\n\nTASK:\n{prompt}"
        try: return self.model.generate_content(full_prompt).text
        except Exception as e: return f"Error: {str(e)}"

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

# --- 🔍 المحقق الجنائي (The Forensic Analyzer) ---
def get_html_structure(code_output):
    """
    إذا قام الكود بطباعة HTML عند الفشل (وهذا ما سنطلبه)، هذه الدالة تستخرجه.
    """
    if "HTML_DUMP_START" in code_output:
        try:
            html_part = code_output.split("HTML_DUMP_START")[1].split("HTML_DUMP_END")[0]
            # تنظيف الـ HTML لتقليل حجم التوكنز (نأخذ أهم الأجزاء)
            soup_preview = html_part[:4000] # نأخذ أول 4000 حرف فقط للتحليل
            return soup_preview
        except:
            return "HTML Dump failed parsing."
    return None

# --- 🧠 حلقة التعلم والتصحيح (Learning Loop) ---
def smart_execute_with_learning_loop(initial_code_response, fixer_agent, context_plan):
    current_code_text = initial_code_response
    max_retries = 4
    attempt = 0
    logs_ui = []

    while attempt <= max_retries:
        code = extract_code(current_code_text)
        if not code: return "⚠️ No code.", logs_ui, current_code_text

        dep_logs = ensure_dependencies(code)
        if dep_logs: logs_ui.extend(dep_logs)

        # تشغيل الكود
        success, output = run_code_safe(code)

        # --- منطق التحقق المتقدم ---
        is_valid = False
        fail_reason = ""
        
        if not success:
            fail_reason = "Runtime Error (Crash)"
        elif "0 messages" in output or "No messages found" in output or not output.strip():
            fail_reason = "Logical Failure (Zero Data)"
        else:
            is_valid = True

        # --- النجاح ---
        if is_valid:
            return f"✅ Success:\n{output}", logs_ui, current_code_text
        
        # --- الفشل والتعلم ---
        else:
            # استخراج الـ HTML إذا كان المبرمج قد طبعه
            html_evidence = get_html_structure(output)
            
            logs_ui.append(f"⚠️ Attempt {attempt+1} Failed: {fail_reason}")
            
            if attempt == max_retries: return f"❌ Failed:\n{output}", logs_ui, current_code_text
            
            # بناء الأمر للإصلاح (Prompt Engineering)
            if html_evidence:
                fix_prompt = f"""
                EXECUTION FAILED: {fail_reason}
                
                🔬 FORENSIC EVIDENCE (Actual Page HTML):
                ```html
                {html_evidence}
                ```
                
                ANALYSIS:
                Look at the HTML above. The previous CSS selectors (class names) were WRONG.
                Find the correct class for the message container (e.g., look for 'msg', 'row', 'sms', or just table rows).
                
                FIX:
                Rewrite the code using the CORRECT selectors found in the HTML evidence.
                """
                logs_ui.append("🔬 Analyzing HTML Dump to fix selectors...")
            else:
                # إذا لم يكن هناك HTML، نطلب من الكود القادم طباعته
                fix_prompt = f"""
                EXECUTION FAILED: {fail_reason}
                Output: "{output}"
                
                DIAGNOSTIC MODE REQUIRED:
                The code scraped 0 messages. We don't know why.
                
                REWRITE THE CODE TO:
                1. Use 'curl_cffi' to get the page.
                2. PRINT the raw HTML structure using: 
                   `print("HTML_DUMP_START"); print(soup.prettify()[:4000]); print("HTML_DUMP_END")`
                3. Try a very broad search (e.g., find all 'div's with text length > 20).
                """
                logs_ui.append("🕵️ Requesting HTML Dump for analysis...")

            current_code_text = fixer_agent.ask(fix_prompt, context=context_plan)
            attempt += 1
            
    return "Unknown", logs_ui, current_code_text

# --- الواجهة ---
st.markdown("<h1>🧠 THE COUNCIL V41</h1>", unsafe_allow_html=True)
st.caption(f"Protocol: **Fail -> Dump HTML -> Learn -> Fix** | Engine: **{selected_model}**")

st.info("نحن في مركب واحد. إذا فشل الكود في جلب البيانات، سيقوم بنسخ كود الموقع وتحليله لإصلاح نفسه.")

mission = st.text_area("المهمة:", height=100, placeholder="مثال: استخرج الرسائل من https://receive-smss.com/")

if st.button("إثبات الكفاءة (Prove It) ⚡"):
    if not mission:
        st.warning("أدخل المهمة.")
    else:
        results = st.container()
        
        planner = NativeAgent("Strategist", "Plan forensic extraction.", selected_model)
        coder = NativeAgent("Developer", "Write scraping code.", selected_model)
        fixer = NativeAgent("The Fixer", "Analyze HTML dumps and fix selectors.", selected_model)
        
        with results:
            with st.spinner("1. التخطيط الاستراتيجي..."):
                plan = planner.ask("Goal: Go to 'https://receive-smss.com/', find the first active number link, and scrape messages. If it fails, PRINT THE HTML to debug.")
                st.markdown(f"<div class='agent-box'><div class='agent-name'>📐 Strategist</div>{plan}</div>", unsafe_allow_html=True)
            
            with st.spinner("2. الكود الأولي..."):
                initial_code = coder.ask("Write python code using curl_cffi. 1. Go to homepage. 2. Find '/sms/' link. 3. Scrape. IMPORTANT: If 0 messages found, print 'No messages found' AND print the first 2000 chars of HTML soup for debugging.", context=plan)
            
            with st.spinner("3. دورة التعلم والتنفيذ (Learning Loop)..."):
                final_output, debug_logs, final_code = smart_execute_with_learning_loop(initial_code, fixer, plan)
                
                if debug_logs:
                    log_html = "<br>".join([f"<code>{l}</code>" for l in debug_logs])
                    st.markdown(f"<div class='install-box'>{log_html}</div>", unsafe_allow_html=True)
                
                st.markdown(f"<div class='fixer-box'><div class='agent-name' style='color:#00ffff'>🔧 Final Winning Code</div>{final_code}</div>", unsafe_allow_html=True)
                
                if "Success" in final_output:
                    clean_out = final_output.replace("✅ Success:\n", "").replace("HTML_DUMP_START", "").split("HTML_DUMP_END")[-1] # تنظيف
                    st.markdown(f"### 🏆 النتيجة النهائية:")
                    st.markdown(f"<div class='output-box'>{clean_out}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='error-box'>{final_output}</div>", unsafe_allow_html=True)
        
        st.success("✅ الدورة اكتملت.")
