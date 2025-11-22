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
    page_title="THE COUNCIL V34 | The Hive Mind",
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
    .agent-name { font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
    .output-box { background: #0a0a0a; padding: 10px; border: 1px solid #00ff00; font-family: monospace; color: #00ff00; }
    .error-box { background: #2a0000; padding: 10px; border: 1px solid #ff0000; color: #ffaaaa; font-size: 0.9em; }
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
        st.warning("Defaulting to Flash.")
        selected_model = "models/gemini-1.5-flash"
    else:
        default_ix = 0
        for i, m in enumerate(available_models):
            if "flash" in m: default_ix = i; break
        selected_model = st.selectbox("اختر الموديل:", available_models, index=default_ix)
    
    st.divider()
    st.info("💡 V34 New Agent: **The Fixer** (Dedicated Debugger)")

# --- 3. كلاس الوكيل ---
class NativeAgent:
    def __init__(self, name, role, model_id, specialized_instruction=""):
        self.name = name
        self.role = role
        sys_instruction = f"""
        You are {name}, {role}.
        
        GLOBAL RULES:
        1. Code Blocks: ```python ... ```
        2. Dependencies: # pip: lib1 lib2
        3. Stealth: Use 'curl_cffi' instead of 'requests' for scraping to bypass 403.
        
        {specialized_instruction}
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

# --- 4. أدوات المعالجة ---

def extract_code(text):
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if not match: match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    return match.group(1) if match else None

def ensure_dependencies(code):
    logs = []
    matches = re.findall(r"#\s*pip:\s*([^\n\r]*)", code)
    all_libs = []
    for match in matches:
        clean_match = match.split("#")[0]
        libs = [lib.strip() for lib in re.split(r'[,\s]+', clean_match) if lib.strip()]
        all_libs.extend(libs)
    all_libs = list(set(all_libs))
    
    if all_libs:
        logs.append(f"📦 Deps found: {', '.join(all_libs)}")
        for lib in all_libs:
            try:
                __import__(lib)
            except ImportError:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", lib])
                    logs.append(f"✅ Installed: {lib}")
                except:
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                        logs.append(f"✅ Installed (Sys): {lib}")
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

# --- 5. حلقة الخلية (The Hive Loop) ---
def smart_execute_with_hive(initial_code_response, fixer_agent, context_plan):
    """
    تستخدم هذه الدالة 'المصحح' (Fixer Agent) لإصلاح الأخطاء بدلاً من المطور الأصلي.
    """
    current_code_text = initial_code_response
    max_retries = 5 # زدنا عدد المحاولات كما طلبت
    attempt = 0
    logs_ui = []

    while attempt <= max_retries:
        # 1. استخراج
        code = extract_code(current_code_text)
        if not code:
            return "⚠️ No code found.", logs_ui, current_code_text

        # 2. تثبيت
        dep_logs = ensure_dependencies(code)
        if dep_logs: logs_ui.extend(dep_logs)

        # 3. تشغيل
        success, output = run_code_safe(code)

        if success:
            return f"✅ Execution Success:\n{output}", logs_ui, current_code_text
        else:
            error_msg = output
            logs_ui.append(f"⚠️ Attempt {attempt+1}/{max_retries} Failed: {error_msg[:100]}...")
            
            if attempt == max_retries:
                return f"❌ Failed after {max_retries} attempts. Last Error:\n{error_msg}", logs_ui, current_code_text
            
            # 4. استدعاء المصحح (The Fixer)
            fix_prompt = f"""
            The code failed with this error:
            "{error_msg}"
            
            Current Code:
            {code}
            
            YOUR TASK:
            1. Analyze the traceback.
            2. Rewrite the code to fix it.
            3. If it's a 403 Forbidden, use 'curl_cffi'.
            4. Return ONLY the corrected code block.
            """
            # لاحظ: نطلب من fixer_agent وليس developer
            current_code_text = fixer_agent.ask(fix_prompt, context=context_plan)
            attempt += 1
            
    return "Unknown Error", logs_ui, current_code_text

# --- الواجهة الرئيسية ---
st.markdown("<h1>💀 THE COUNCIL V34</h1>", unsafe_allow_html=True)
st.caption(f"Mode: **Hive Mind (Dedicated Fixer)** | Engine: **{selected_model}**")

mission = st.text_area("أدخل المهمة التقنية:", height=100, placeholder="مثال: استخرج بيانات من موقع يرفض البوتات.")

if st.button("تنفيذ الهجوم (Hive Mode) ⚡"):
    if not mission:
        st.warning("أدخل المهمة.")
    else:
        results = st.container()
        
        # --- تعريف الفيلق (4 وكلاء) ---
        planner = NativeAgent(
            "Strategist", 
            "Plan logical steps.", 
            selected_model
        )
        
        coder = NativeAgent(
            "Developer", 
            "Write python code. Always declare deps: # pip: lib", 
            selected_model
        )
        
        # --- العميل الجديد: المصحح ---
        fixer = NativeAgent(
            "The Fixer", 
            "You are a Code Debugger. You DO NOT write logic from scratch. You only FIX broken code based on errors.", 
            selected_model,
            specialized_instruction="Focus on syntax errors, missing libraries, and logic bugs."
        )
        
        auditor = NativeAgent(
            "Auditor", 
            "Review final results.", 
            selected_model
        )

        with results:
            # 1. التخطيط
            with st.spinner("1. التخطيط..."):
                plan = planner.ask(mission)
                st.markdown(f"<div class='agent-box'><div class='agent-name' style='color:#d4af37'>📐 Strategist</div>{plan}</div>", unsafe_allow_html=True)
            
            # 2. الكود الأولي
            with st.spinner("2. المبرمج يكتب الكود الأولي..."):
                initial_code = coder.ask("Write python code for this plan. Use '# pip: lib' for dependencies.", context=plan)
            
            # 3. معركة الإصلاح (Hive Loop)
            with st.spinner("3. اختبار الكود وتصحيحه (بواسطة The Fixer)..."):
                # نمرر fixer هنا بدلاً من coder
                final_output, debug_logs, final_code = smart_execute_with_hive(initial_code, fixer, plan)
                
                if debug_logs:
                    log_html = "<br>".join([f"<code>{l}</code>" for l in debug_logs])
                    st.markdown(f"<div class='install-box'>{log_html}</div>", unsafe_allow_html=True)
                
                # عرض من قام بالإصلاح النهائي
                st.markdown(f"<div class='fixer-box'><div class='agent-name' style='color:#00ffff'>🔧 The Fixer (Final Code)</div>{final_code}</div>", unsafe_allow_html=True)
                
                if "Success" in final_output:
                    st.markdown(f"<div class='output-box'>{final_output}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='error-box'>{final_output}</div>", unsafe_allow_html=True)

            # 4. التدقيق
            with st.spinner("4. التدقيق النهائي..."):
                report = auditor.ask("Audit this execution.", context=f"{plan}\n{final_output}")
                st.markdown(f"<div class='agent-box'><div class='agent-name' style='color:#d4af37'>🛡️ Auditor</div>{report}</div>", unsafe_allow_html=True)
                
        st.success("✅ تمت المهمة.")
