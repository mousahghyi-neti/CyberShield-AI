import streamlit as st
import google.generativeai as genai
import json
import os
import datetime
import time
import zipfile
import io
import re
from duckduckgo_search import DDGS  # <--- عين المجلس على الإنترنت

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE OMNIPOTENT COUNCIL | V14",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ملف الذاكرة ---
MEMORY_FILE = "council_history.json"

# --- دوال إدارة الذاكرة (المطورة - Feature 2) ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_memory(record):
    history = load_memory()
    history.append(record)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def clear_memory():
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)

def get_relevant_context(query):
    """
    (Feature 2: RAG Lite)
    يبحث في الذاكرة عن آخر 3 قرارات لتزويد المجلس بسياق تاريخي.
    """
    history = load_memory()
    if not history:
        return "لا توجد سجلات سابقة."
    
    # نأخذ آخر 3 قرارات كـ "سياق قصير المدى"
    recent = history[-3:]
    context_text = ""
    for item in recent:
        context_text += f"- في تاريخ {item['date']} ناقشنا '{item.get('topic', 'N/A')}' وكان القرار: {item.get('summary', 'N/A')}\n"
    return context_text

# --- دالة البحث عبر الإنترنت (Feature 4) ---
def search_web(query):
    """
    (Feature 4: Internet Access)
    تستخدم DuckDuckGo للبحث عن معلومات حية.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                summary = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
                return summary
            return "لم يتم العثور على نتائج."
    except Exception as e:
        return f"تعذر الاتصال بالإنترنت: {str(e)}"

# --- دالة ضغط الملفات (من الإصدار السابق) ---
def create_zip_from_response(text):
    zip_buffer = io.BytesIO()
    code_blocks = re.findall(r"```(\w+)?\n(.*?)```", text, re.DOTALL)
    
    if not code_blocks:
        return None

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i, (lang, code) in enumerate(code_blocks):
            lang = lang.lower().strip() if lang else "txt"
            ext = "txt"
            if "python" in lang or "py" in lang: ext = "py"
            elif "html" in lang: ext = "html"
            elif "css" in lang: ext = "css"
            elif "javascript" in lang or "js" in lang: ext = "js"
            elif "json" in lang: ext = "json"
            
            filename_match = re.search(r"filename:\s*([\w\-\.]+)", code)
            if filename_match:
                filename = filename_match.group(1)
            else:
                filename = f"file_{i+1}_{lang}.{ext}"
            
            zip_file.writestr(filename, code)
            
    zip_buffer.seek(0)
    return zip_buffer

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    h1, h2, h3 { font-family: 'Georgia', serif; color: #d4af37; }
    .advisor-card { background-color: #111; padding: 15px; border-radius: 8px; border-left: 4px solid #444; margin-bottom: 15px; }
    .devil-card { background-color: #1a0505; padding: 15px; border-radius: 8px; border-left: 4px solid #ff0000; color: #ffcccc; box-shadow: 0 0 10px rgba(255,0,0,0.2); }
    .overlord-card { background-color: #000; padding: 25px; border: 2px solid #d4af37; border-radius: 12px; font-size: 1.1em; box-shadow: 0 0 20px rgba(212, 175, 55, 0.2); }
    .agent-step { color: #00ff00; font-family: 'Courier New', monospace; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

# --- API Setup ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    available_models = ["models/gemini-1.5-flash", "models/gemini-pro"]
except Exception as e:
    st.error(f"⚠️ Error: {str(e)}")
    st.stop()

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ غرفة التحكم")
    selected_model = st.selectbox("المحرك:", available_models, index=0)
    
    st.divider()
    st.markdown("### 🌐 قدرات الشبكة")
    enable_internet = st.checkbox("تفعيل البحث المباشر (Internet)", value=True)
    enable_memory = st.checkbox("تفعيل الذاكرة السياقية (RAG)", value=True)
    
    st.divider()
    if st.button("🗑️ فرمتة الذاكرة"):
        clear_memory()
        st.rerun()

# --- AI Function ---
def ask_gemini(prompt, sys_instruction, model_name):
    try:
        model = genai.GenerativeModel(model_name)
        full_payload = f"System Role: {sys_instruction}\n\nTask: {prompt}"
        response = model.generate_content(full_payload)
        return response.text
    except Exception as e:
        if "429" in str(e): return "⚠️ تجاوز السرعة (استخدم Flash)."
        return f"Error: {str(e)}"

# --- Main UI ---
st.markdown("<h1 style='text-align: center;'>👁️ THE OMNIPOTENT COUNCIL V14</h1>", unsafe_allow_html=True)
st.caption("Agents (1) + Infinite Memory (2) + Internet Access (4)")

problem = st.text_area("أدخل المهمة أو الهدف:", height=100)

# --- تعريف الوكلاء (Agents) ---
advisors = {
    "المخطط 📐": { "sys": "أنت المخطط. استخدم البيانات المتاحة لوضع خطة عمل دقيقة." },
    "الشيطاني 😈": { "sys": "أنت الذكاء الشيطاني. استخدم معلومات المنافسين (من البحث) والذاكرة لسحقهم." },
    "المبرمج 💻": { "sys": "أنت المبرمج. اكتب الأكواد. ضع تعليق # filename: name.ext في البداية." },
    "الأمن 🛡️": { "sys": "أنت الأمن. افحص الخطة والكود." }
}

if st.button("تشغيل البروتوكول ⚡", use_container_width=True):
    if not problem:
        st.warning("أدخل البيانات.")
    else:
        results = st.container()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # --- المرحلة 1: جمع المعلومات (Agents Logic) ---
        collected_data = f"المشكلة الأساسية: {problem}\n\n"
        
        # 1. وكيل الإنترنت (The Spy)
        if enable_internet:
            status_text.markdown("🌐 **الجاسوس (The Spy):** يجوب الإنترنت بحثاً عن معلومات...")
            web_results = search_web(problem)
            collected_data += f"--- نتائج البحث المباشر (Live Internet Data) ---\n{web_results}\n\n"
            with results:
                with st.expander("🌐 تقرير الاستخبارات (من الإنترنت)", expanded=False):
                    st.write(web_results)
        
        # 2. وكيل الذاكرة (The Historian)
        if enable_memory:
            status_text.markdown("📚 **المؤرخ (The Historian):** يسترجع ملفات الماضي...")
            past_context = get_relevant_context(problem)
            collected_data += f"--- سياق من الذاكرة السابقة (Memory Context) ---\n{past_context}\n\n"
        
        # --- المرحلة 2: انعقاد المجلس ---
        full_report_for_overlord = collected_data
        
        with results:
            cols = st.columns(2)
            total_steps = len(advisors) + 2 # +2 للبحث والمراجع
            current_step = 1 # بدأنا بعد البحث
            
            for idx, (name, data) in enumerate(advisors.items()):
                status_text.text(f"جاري استشارة {name} بناءً على البيانات الجديدة...")
                
                with cols[idx % 2]:
                    time.sleep(1)
                    # نمرر البيانات المجمعة (بحث + ذاكرة) للمستشار
                    advisor_prompt = f"البيانات المتاحة:\n{collected_data}\n\nمطلوب رأيك في المشكلة."
                    reply = ask_gemini(advisor_prompt, data["sys"], selected_model)
                    
                    full_report_for_overlord += f"--- رأي {name} ---\n{reply}\n\n"
                    
                    st.markdown(f"""
                    <div class="advisor-card">
                        <b style="color:#d4af37">{name}</b><br>{reply}
                    </div>
                    """, unsafe_allow_html=True)
                
                current_step += 1
                progress_bar.progress(current_step / total_steps)

            # --- المرحلة 3: المراجع الأعظم (Overlord) ---
            st.markdown("---")
            status_text.text("👁️ المراجع الأعظم يدمج البيانات (بحث + ذاكرة + آراء) لاتخاذ القرار...")
            
            overlord_sys = """
            أنت المراجع الأعظم.
            لديك صلاحية الوصول للإنترنت (تم البحث)، وللذاكرة (تم الاسترجاع)، ولآراء الخبراء.
            1. اصنع الخطة النهائية (Master Plan).
            2. اكتب أي كود برمجي مطلوب (بشكل كامل).
            3. ضع تعليق # filename: example.py في بداية كل ملف كود.
            """
            
            final_verdict = ask_gemini(full_report_for_overlord, overlord_sys, selected_model)
            
            st.markdown(f"<div class='overlord-card'>{final_verdict}</div>", unsafe_allow_html=True)
            
            # استخراج الملفات
            zip_bytes = create_zip_from_response(final_verdict)
            if zip_bytes:
                st.download_button("📦 تحميل ملفات المشروع (ZIP)", zip_bytes, "project_v14.zip", "application/zip")
            
            # الحفظ في الذاكرة
            save_memory({
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "topic": problem[:50],
                "summary": final_verdict[:200] + "..."
            })
            
            progress_bar.progress(1.0)
            status_text.text("✅ تمت المهمة بنجاح.")
