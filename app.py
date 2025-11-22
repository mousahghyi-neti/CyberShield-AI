import streamlit as st
import google.generativeai as genai
import os
import io
import sys
import subprocess # <--- أداة استدعاء التيرمينال
import re
from contextlib import redirect_stdout

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V28 | Auto-Install",
    page_icon="💀",
    layout="wide"
)

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1 { color: #ff0000; font-family: 'Courier New', monospace; text-align:center; }
    .agent-box { border-left: 4px solid #d4af37; background: #111; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .agent-name { color: #d4af37; font-weight: bold; font-size: 1.1em; }
    .output-box { background: #0a0a0a; padding: 10px; border: 1px solid #333; font-family: monospace; color: #00ff00; }
    .install-box { background: #001a33; padding: 10px; border: 1px solid #0066cc; color: #66b3ff; font-size: 0.8em; margin-bottom: 5px; }
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
        st.warning("لم يتم العثور على موديلات، سنستخدم الافتراضي.")
        selected_model = "models/gemini-1.5-flash" # محاولة يائسة
    else:
        selected_model = st.selectbox("اختر الموديل:", available_models, index=0)

# --- 3. المحرك الخاص بنا ---
class NativeAgent:
    def __init__(self, name, role, model_id):
        self.name = name
        self.role = role
        # تعليمات النظام المحدثة لتشمل طلب المكتبات
        sys_instruction = f"""
        You are {name}, {role}.
        IMPORTANT FOR CODING: If you need external libraries (like requests, pandas, numpy, scapy, etc.), 
        you MUST list them in the first line of your code like this:
        # pip: library1, library2
        Example:
        # pip: requests, beautifulsoup4
        import requests
        ...
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

# --- 4. دالة التثبيت التلقائي (The Injector) ---
def ensure_dependencies(code):
    """
    تبحث عن تعليق # pip: وتقوم بتثبيت المكتبات
    """
    # البحث عن السطر السحري
    match = re.search(r"#\s*pip:\s*(.*)", code)
    logs = []
    
    if match:
        libs_str = match.group(1)
        # تنظيف أسماء المكتبات
        libs = [lib.strip() for lib in libs_str.split(",") if lib.strip()]
        
        if libs:
            logs.append(f"📦 Detected required libraries: {', '.join(libs)}")
            for lib in libs:
                try:
                    # تشغيل pip install داخل بيئة العمل الحالية
                    subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                    logs.append(f"✅ Installed: {lib}")
                except Exception as e:
                    logs.append(f"❌ Failed to install {lib}: {e}")
    
    return logs

# --- 5. منفذ الكود ---
def execute_python_code(text):
    # استخراج الكود
    code_match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if not code_match:
        code_match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    
    if not code_match:
        return "⚠️ No code found."
    
    code = code_match.group(1)
    
    # -- الخطوة الجديدة: التثبيت قبل التنفيذ --
    install_logs = ensure_dependencies(code)
    install_report = "\n".join(install_logs)
    
    # التنفيذ
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(code, globals())
        
        output = buffer.getvalue()
        final_res = ""
        if install_report:
            final_res += f"{install_report}\n{'-'*20}\n"
        final_res += f"✅ Execution Output:\n{output}"
        return final_res
        
    except Exception as e:
        return f"{install_report}\n❌ Execution Error:\n{str(e)}"

# --- الواجهة ---
st.markdown("<h1>💀 THE COUNCIL V28</h1>", unsafe_allow_html=True)
st.caption(f"Engine: **{selected_model}** | Feature: **Auto-Dependency Injection**")

mission = st.text_area("أدخل المهمة:", height=100, placeholder="مثال: استخدم مكتبة 'requests' لجلب الآي بي الخاص بالسيرفر.")

if st.button("تنفيذ ⚡"):
    if not mission:
        st.warning("أدخل المهمة.")
    else:
        results = st.container()
        
        planner = NativeAgent("Strategist", "Plan logic.", selected_model)
        coder = NativeAgent("Developer", "Write python code. Remember to use '# pip: lib' if needed.", selected_model)
        auditor = NativeAgent("Auditor", "Review results.", selected_model)

        with results:
            # 1. التخطيط
            with st.spinner("التخطيط..."):
                plan = planner.ask(mission)
                st.markdown(f"<div class='agent-box'><div class='agent-name'>📐 Strategist</div>{plan}</div>", unsafe_allow_html=True)
            
            # 2. البرمجة
            with st.spinner("البرمجة وتحديد المكتبات..."):
                code_res = coder.ask(f"Write python code for this. If you need external libs, verify you put '# pip: name' at the top.", context=plan)
                st.markdown(f"<div class='agent-box'><div class='agent-name'>💻 Developer</div>{code_res}</div>", unsafe_allow_html=True)

            # 3. التثبيت والتنفيذ
            with st.spinner("جاري تثبيت المكتبات وتشغيل الكود..."):
                # هنا السحر: الدالة ستقوم بالتثبيت أولاً ثم التنفيذ
                exec_res = execute_python_code(code_res)
                
                # عرض النتائج مع تقرير التثبيت بشكل مميز
                if "Detected required libraries" in exec_res:
                    st.markdown(f"<div class='install-box'>{exec_res.split('✅ Execution Output')[0]}</div>", unsafe_allow_html=True)
                    output_only = exec_res.split('✅ Execution Output')[-1] if '✅ Execution Output' in exec_res else exec_res
                    st.markdown(f"<div class='output-box'>Output:\n{output_only}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='output-box'>{exec_res}</div>", unsafe_allow_html=True)

            # 4. التدقيق
            with st.spinner("التدقيق..."):
                final_report = auditor.ask("Analyze result.", context=f"{plan}\n{exec_res}")
                st.markdown(f"<div class='agent-box'><div class='agent-name'>🛡️ Auditor</div>{final_report}</div>", unsafe_allow_html=True)
                
        st.success("✅ تم.")
