import streamlit as st
import google.generativeai as genai
import json
import os
import datetime
import time  # <--- الإضافة الجوهرية للتحكم في الزمن

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V12 | Anti-Limit",
    page_icon="🏛️",
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

# --- التصميم (Dark & Gold) ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1, h2, h3 { font-family: 'Georgia', serif; color: #d4af37; }
    .advisor-card { background-color: #111; padding: 15px; border-radius: 8px; border-left: 4px solid #444; margin-bottom: 15px; }
    .devil-card { background-color: #1a0505; padding: 15px; border-radius: 8px; border-left: 4px solid #ff0000; color: #ffcccc; box-shadow: 0 0 10px rgba(255,0,0,0.2); }
    .overlord-card { background-color: #0a0a0a; padding: 25px; border: 2px solid #d4af37; border-radius: 12px; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# --- الاتصال بـ API وجلب الموديلات ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    
    available_models = []
    try:
        # محاولة جلب الموديلات، مع تفضيل الفلاش لأنه الأسرع
        models = genai.list_models()
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        # ترتيب القائمة لوضع الفلاش في البداية
        available_models.sort(key=lambda x: 'flash' not in x) 
    except:
        available_models = ["models/gemini-1.5-flash", "models/gemini-pro"]
        
except Exception as e:
    st.error(f"⚠️ خطأ API: {str(e)}")
    st.stop()

# --- الشريط الجانبي ---
with st.sidebar:
    st.header("⚙️ المحرك")
    selected_model = st.selectbox("الموديل:", available_models, index=0)
    st.info("نصيحة: استخدم gemini-1.5-flash للسرعة وتجنب الأخطاء.")
    
    st.divider()
    if st.button("🗑️ مسح الذاكرة"):
        clear_memory()
        st.rerun()
        
    history_data = load_memory()
    if history_data:
        st.caption(f"الجلسات: {len(history_data)}")
        for item in reversed(history_data):
            with st.expander(f"📅 {item['date']}"):
                st.write(item['final_decision'])

# --- دالة الذكاء الاصطناعي (مع إعادة المحاولة) ---
def ask_gemini(prompt, sys_instruction, model_name):
    try:
        model = genai.GenerativeModel(model_name)
        full_payload = f"System Role: {sys_instruction}\n\nTask: {prompt}"
        response = model.generate_content(full_payload)
        return response.text
    except Exception as e:
        # إذا حدث خطأ 429، نعيد رسالة توضيحية
        if "429" in str(e):
            return "⚠️ (تجاوزت السرعة) - الموديل مشغول، يرجى استخدام موديل Flash."
        return f"خطأ: {str(e)}"

# --- الواجهة الرئيسية ---
st.markdown("<h1 style='text-align: center;'>🏛️ THE COUNCIL V12</h1>", unsafe_allow_html=True)

problem = st.text_area("المعضلة:", height=100, key="main_input")

advisors = {
    "المخطط 📐": { "role": "هيكلة", "style": "advisor-card", "sys": "أنت المخطط. ضع خطة عمل." },
    "الشيطاني 😈": { "role": "دهاء", "style": "devil-card", "sys": "أنت الذكاء الشيطاني. فكر بربحية وقسوة." },
    "المبرمج 💻": { "role": "تقنية", "style": "advisor-card", "sys": "أنت المبرمج. اقترح الكود." },
    "الأمن 🛡️": { "role": "حماية", "style": "advisor-card", "sys": "أنت الأمن. اكشف الثغرات." }
}

if st.button("بدء الاجتماع ⚡", use_container_width=True):
    if not problem:
        st.warning("أدخل البيانات.")
    else:
        results = st.container()
        full_report = f"المشكلة: {problem}\n\n"
        
        # شريط التقدم (لتبرير الانتظار)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with results:
            cols = st.columns(2)
            total_steps = len(advisors) + 1
            current_step = 0
            
            for idx, (name, data) in enumerate(advisors.items()):
                # تحديث الحالة
                status_text.text(f"جاري استشارة {name}...")
                
                with cols[idx % 2]:
                    # --- الخدعة هنا: التمهل ---
                    time.sleep(1.5) # انتظار 1.5 ثانية بين كل طلب
                    
                    reply = ask_gemini(problem, data["sys"], selected_model)
                    full_report += f"--- {name} ---\n{reply}\n\n"
                    st.markdown(f"<div class='{data['style']}'><b>{name}</b><br>{reply}</div>", unsafe_allow_html=True)
                
                current_step += 1
                progress_bar.progress(current_step / total_steps)

            st.markdown("---")
            status_text.text("المراجع الأعظم يصوغ القرار النهائي...")
            
            # انتظار أخير قبل المراجع الأعظم
            time.sleep(2)
            overlord_sys = "أنت المراجع الأعظم. ادمج الآراء وقدم خطة نهائية."
            final = ask_gemini(full_report, overlord_sys, selected_model)
            
            st.markdown(f"<div class='overlord-card'>{final}</div>", unsafe_allow_html=True)
            
            # اكتمال
            progress_bar.progress(1.0)
            status_text.text("✅ اكتملت الجلسة")
            
            # الحفظ
            save_memory({
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "final_decision": final
            })
