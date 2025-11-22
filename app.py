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
    page_title="THE COUNCIL V36 | The Critic",
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
    .warning-box { background: #332b00; padding: 10px; border: 1px solid #ffcc00; color: #ffdd99; font-size: 0.9em; }
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
    default_ix = 0
    if models:
        for i, m in enumerate(models):
            if "flash" in m: default_ix = i; break
        selected_model = st.selectbox("Model:", models, index=default_ix)
    else:
        selected_model = "models/gemini-1.5-flash"
    
    st.info("💡 V36 Feature: **Semantic Validation**\nRejects empty results.")

# --- كلاس الوكيل ---
class NativeAgent:
    def __init__(self, name, role, model_id):
        self.name = name
        self.role = role
        sys_instruction = f"""
        You are {name}, {role}.
        RULES:
        1. NO ASYNC. Use synchronous code only.
        2. Use 'curl_cffi' for requests (impersonate="chrome110").
        3. PRINT the data. If you don't print, it fails.
        4. Try different HTML selectors if table/divs are not found (be adaptive).
        5. Deps: # pip: curl_cffi beautifulsoup4
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
        logs.append(f"📦 Checking deps: {', '.join(all_libs)}")
        for lib in all_libs:
            try:
                __import__(lib)
            except ImportError:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", lib])
                    logs.append(f"✅ Installed: {lib}")
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

# --- 🧠 المدقق النقدي (The Critical Validator) ---
def validate_output(output):
    """
    يفحص المخرجات بحثاً عن علامات الفشل "المنطقي" وليس التقني فقط.
    """
    # كلمات تدل على أن الكود اشتغل لكن لم يجد شيئاً
    failure_keywords = [
        "لا توجد بيانات", "no data found", "empty", "not found", 
        "لم يتم العثور", "0 items", "no tables"
    ]
    
    # إذا كانت المخرجات قصيرة جداً (أقل من 50 حرف)، غالباً فشل
    if len(output.strip()) < 50:
        return False, "Output is too short (likely empty)."
    
    lower_out = output.lower()
    for kw in failure_keywords:
        if kw in lower_out:
            return False, f"Detected failure keyword: '{kw}'"
            
    return True, "Valid"

# --- حلقة الخلية المطورة ---
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

        # --- التحقق المزدوج (تقني + دلالي) ---
        logic_success = False
        validation_msg = ""
        
        if success:
            logic_success, validation_msg = validate_output(output)
        
        # إذا نجح تقنياً ومنطقياً، نخرج
        if success and logic_success:
            return f"✅ Success:\n{output}", logs_ui, current_code_text
        
        # إذا فشل (سواء كراش أو نتيجة فارغة)
        else:
            error_details = output if not success else f"Logical Failure: {validation_msg}\nOutput was: {output}"
            logs_ui.append(f"⚠️ Attempt {attempt+1} Rejected: {validation_msg}...")
            
            if attempt == max_retries:
                return f"❌ Failed. Final Status:\n{error_details}", logs_ui, current_code_text
            
            # طلب تعديل الاستراتيجية
            fix_prompt = f"""
            The code ran but failed validation.
            Issue: {validation_msg}
            
            Actual Output:
            "{output}"
            
            ADVICE:
            - If 'No tables found', try finding 'div' elements with classes like 'row', 'message', 'list-item'.
            - The site structure might not use <table> tags.
            - Inspect the HTML soup logic.
            
            Fix the code and return ONLY the code block.
            """
            current_code_text = fixer_agent.ask(fix_prompt, context=context_plan)
            attempt += 1
            
    return "Unknown", logs_ui, current_code_text

# --- الواجهة ---
st.markdown("<h1>💀 THE COUNCIL V36</h1>", unsafe_allow_html=True)
st.caption(f"Validator: **Semantic (Logic Check)** | Engine: **{selected_model}**")

mission = st.text_area("المهمة:", height=100, placeholder="مثال: استخرج الرسائل من الرابط...")

if st.button("بدء العملية ⚡"):
    if not mission:
        st.warning("أدخل المهمة.")
    else:
        results = st.container()
        
        planner = NativeAgent("Strategist", "Plan execution.", selected_model)
        coder = NativeAgent("Developer", "Write python code.", selected_model)
        # المصحح هنا تم تعزيزه ليكون خبيراً في استخراج البيانات
        fixer = NativeAgent("The Fixer", "Fix scraping logic. Try different HTML selectors if one fails.", selected_model)
        
        with results:
            with st.spinner("1. التخطيط..."):
                plan = planner.ask(mission)
                st.markdown(f"<div class='agent-box'><div class='agent-name'>📐 Strategist</div>{plan}</div>", unsafe_allow_html=True)
            
            with st.spinner("2. المحاولة الأولى..."):
                initial_code = coder.ask("Write python code using curl_cffi. Print ALL extracted text.", context=plan)
            
            with st.spinner("3. التحقق والتصحيح (The Critical Loop)..."):
                final_output, debug_logs, final_code = smart_execute_with_hive(initial_code, fixer, plan)
                
                if debug_logs:
                    log_html = "<br>".join([f"<code>{l}</code>" for l in debug_logs])
                    st.markdown(f"<div class='install-box'>{log_html}</div>", unsafe_allow_html=True)
                
                st.markdown(f"<div class='fixer-box'><div class='agent-name' style='color:#00ffff'>🔧 Final Code Used</div>{final_code}</div>", unsafe_allow_html=True)
                
                if "Success" in final_output:
                    clean_out = final_output.replace("✅ Success:\n", "")
                    st.markdown(f"### 📊 النتائج المعتمدة:")
                    st.markdown(f"<div class='output-box'>{clean_out}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='error-box'>{final_output}</div>", unsafe_allow_html=True)
        
        st.success("✅ العملية انتهت.")
