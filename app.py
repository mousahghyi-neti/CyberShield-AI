import streamlit as st
import google.generativeai as genai
import json
import os
import datetime
import time
import zipfile
import io
import re
from duckduckgo_search import DDGS

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V15 | Smart Selection",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ملف الذاكرة ---
MEMORY_FILE = "council_history.json"

# --- دوال إدارة الذاكرة ---
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
    history = load_memory()
    if not history: return ""
    recent = history[-3:]
    context_text = ""
    for item in recent:
        context_text += f"- {item['date']}: {item.get('summary', 'N/A')}\n"
    return context_text

# --- دالة الإنترنت ---
def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
            return "لا توجد نتائج."
    except Exception as e:
        return f"خطأ إنترنت: {str(e)}"

# --- دالة ضغط الملفات ---
def create_zip_from_response(text):
    zip_buffer = io.BytesIO()
    code_blocks = re.findall(r"```(\w+)?\n(.*?)```", text, re.DOTALL)
    if not code_blocks: return None
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
            filename = filename_match.group(1) if filename_match else f"file_{i+1}.{ext}"
            zip_file.writestr(filename, code)
    zip_buffer.seek(0)
    return zip_buffer

# --- دالة جلب الموديلات الذكية (التحديث الجديد) ---
def get_clean_model_list():
    """
    تعيد قائمة نظيفة بالموديلات المتاحة فعلياً فقط،
    مع إعطاء الأولوية للموديلات المستقرة (Flash/Pro).
    """
    # القائمة الذهبية (الموديلات التي نريدها دائماً في المقدمة)
    priority_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    try:
        fetched_models = []
        for m in genai.list_models():
            # نأخذ فقط الموديلات التي تولد نصوصاً
            if 'generateContent' in m.supported_generation_methods:
                # تنظيف الاسم (حذف models/)
                clean_name = m.name.replace("models/", "")
                fetched_models.append(clean_name)
        
        # دمج القوائم: ابدأ بالأولوية، ثم أضف الباقي إذا لم يكن مكرراً
        final_list = priority_models.copy()
        for m in fetched_models:
            if m not in final_list:
                final_list.append(m)
                
        return final_list
    except:
        # في حال فشل الاتصال، نعود للقائمة اليدوية الآمنة
        return priority_models

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    h1, h2, h3 { font-family: 'Georgia', serif; color: #d4af37; }
    .advisor-card { background-color: #111; padding: 15px; border-radius: 8px; border-left: 4px solid #444; margin-bottom: 15px; }
    .devil-card { background-color: #1a0505; padding: 15px; border-radius: 8px; border-left: 4px solid #ff0000; color: #ffcccc; }
    .overlord-card { background-color: #000; padding: 25px; border: 2px solid #d4af37; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# --- التهيئة ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ مفتاح API مفقود.")
    st.stop()

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ الإعدادات")
    
    # --- قائمة الموديلات المطورة ---
    clean_models = get_clean_model_list()
    selected_model_name = st.selectbox("اختر المحرك (الأسرع أولاً):", clean_models, index=0)
    
    # إعادة إضافة بادئة models/ لأن API يحتاجها برمجياً
    # إذا كان الاسم لا يحتوي عليها أصلاً
    final_model_id = selected_model_name if selected_model_name.startswith("models/") else f"models/{selected_model_name}"
    
    st.caption(f"المعرف التقني: `{final_model_id}`")
    
    st.divider()
    enable_internet = st.checkbox("بحث الإنترنت (Web)", value=True)
    enable_memory = st.checkbox("الذاكرة (History)", value=True)
    
    st.divider()
    if st.button("🗑️ مسح الذاكرة"):
        clear_memory()
        st.rerun()

# --- AI Engine ---
def ask_gemini(prompt, sys_instruction, model_id):
    try:
        model = genai.GenerativeModel(model_id)
        full_payload = f"System Role: {sys_instruction}\n\nTask: {prompt}"
        response = model.generate_content(full_payload)
        return response.text
    except Exception as e:
        if "429" in str(e): return "⚠️ الموديل مشغول (تجاوزت الحد). جرب Flash."
        if "404" in str(e): return "⚠️ الموديل غير مدعوم في منطقتك، اختر غيره."
        return f"Error: {str(e)}"

# --- Main UI ---
st.markdown("<h1 style='text-align: center;'>🏛️ THE COUNCIL V15</h1>", unsafe_allow_html=True)

problem = st.text_area("الهدف الاستراتيجي:", height=100)

advisors = {
    "المخطط 📐": { "sys": "أنت المخطط. ضع خطة عمل دقيقة." },
    "الشيطاني 😈": { "sys": "أنت الذكاء الشيطاني. استغل كل ثغرة، اسحق المنافسين، فكر بالربح فقط." },
    "المبرمج 💻": { "sys": "أنت المبرمج. اكتب الكود. ضع تعليق # filename: name.ext أولاً." },
    "الأمن 🛡️": { "sys": "أنت الأمن. افحص الخطة." }
}

if st.button("تنفيذ ⚡", use_container_width=True):
    if not problem:
        st.warning("أدخل البيانات.")
    else:
        results = st.container()
        progress_bar = st.progress(0)
        status = st.empty()
        
        # 1. جمع البيانات
        data_packet = f"المهمة: {problem}\n\n"
        
        if enable_internet:
            status.text("جاري البحث في الشبكة...")
            web_res = search_web(problem)
            data_packet += f"--- بيانات الإنترنت ---\n{web_res}\n\n"
            
        if enable_memory:
            status.text("مراجعة الأرشيف...")
            mem_res = get_relevant_context(problem)
            data_packet += f"--- من الذاكرة ---\n{mem_res}\n\n"
        
        # 2. المستشارين
        with results:
            cols = st.columns(2)
            total = len(advisors) + 1
            curr = 0
            full_report = data_packet
            
            for idx, (name, info) in enumerate(advisors.items()):
                status.text(f"استشارة {name}...")
                with cols[idx % 2]:
                    time.sleep(1) # منع الحظر
                    reply = ask_gemini(data_packet, info["sys"], final_model_id)
                    full_report += f"--- {name} ---\n{reply}\n\n"
                    st.markdown(f"<div class='advisor-card'><b>{name}</b><br>{reply}</div>", unsafe_allow_html=True)
                curr += 1
                progress_bar.progress(curr / total)
            
            # 3. المراجع
            st.markdown("---")
            status.text("المراجع الأعظم يتخذ القرار...")
            overlord_sys = "أنت المراجع الأعظم. ادمج الآراء واكتب الكود النهائي بتعليقات filename."
            final = ask_gemini(full_report, overlord_sys, final_model_id)
            
            st.markdown(f"<div class='overlord-card'>{final}</div>", unsafe_allow_html=True)
            
            # 4. الملفات
            zip_data = create_zip_from_response(final)
            if zip_data:
                st.download_button("📦 تحميل المشروع", zip_data, "project.zip", "application/zip")
            
            # 5. الحفظ
            save_memory({"date": str(datetime.datetime.now()), "summary": final[:100] + "..."})
            progress_bar.progress(1.0)
            status.text("✅ تم.")
