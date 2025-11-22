import streamlit as st
import google.generativeai as genai
import json
import os
import datetime

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V11 | Adaptive",
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
    /* تنسيق رسالة الخطأ بشكل جميل */
    .stAlert { background-color: #330000; color: #ffaaaa; border: 1px solid red; }
</style>
""", unsafe_allow_html=True)

# --- الاتصال بـ API وجلب الموديلات ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    
    # --- الميزة الجديدة: جلب الموديلات المتاحة ديناميكياً ---
    available_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
    except Exception as e:
        # في حال فشل الجلب، نضع قائمة احتياطية افتراضية
        available_models = ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.0-pro"]
        
except Exception as e:
    st.error(f"⚠️ خطأ في مفتاح API: {str(e)}")
    st.stop()

# --- الشريط الجانبي (الإعدادات والأرشيف) ---
with st.sidebar:
    st.header("⚙️ المحرك والأرشيف")
    
    # 1. قائمة اختيار الموديل (الحل الجذري)
    selected_model = st.selectbox(
        "اختر محرك الذكاء الاصطناعي:",
        available_models,
        index=0
    )
    st.caption(f"يعمل حالياً على: {selected_model}")
    st.divider()
    
    # 2. إدارة الذاكرة
    if st.button("🗑️ مسح الذاكرة", type="primary"):
        clear_memory()
        st.rerun()
    
    history_data = load_memory()
    if history_data:
        st.caption(f"الجلسات المحفوظة: {len(history_data)}")
        for item in reversed(history_data):
            with st.expander(f"📅 {item['date']}"):
                st.info(item['final_decision'])

# --- دالة الذكاء الاصطناعي (Universal Compatibility) ---
def ask_gemini(prompt, sys_instruction, model_name):
    try:
        # نستخدم الطريقة الكلاسيكية (دمج التعليمات) لضمان العمل مع الموديلات القديمة والجديدة
        model = genai.GenerativeModel(model_name)
        
        # دمج الدور مع السؤال لتجنب أخطاء system_instruction في النسخ القديمة
        full_payload = f"الدور المطلوب منك (System Role): {sys_instruction}\n\nالمهمة المطلوبة: {prompt}"
        
        response = model.generate_content(full_payload)
        return response.text
    except Exception as e:
        return f"⚠️ خطأ من المصدر ({model_name}): {str(e)}"

# --- الواجهة الرئيسية ---
st.markdown("<h1 style='text-align: center;'>🏛️ THE COUNCIL (V11)</h1>", unsafe_allow_html=True)

problem = st.text_area("المعضلة الاستراتيجية:", height=100, placeholder="اكتب هنا...", key="main_input")

# تعريف الشخصيات
advisors = {
    "المخطط الاستراتيجي 📐": {
        "role": "هيكلة", "style": "advisor-card",
        "sys": "أنت المخطط. ضع خارطة طريق واضحة، خطوات تنفيذية، وجدول زمني دقيق."
    },
    "الذكاء الشيطاني 😈": {
        "role": "دهاء", "style": "devil-card",
        "sys": "أنت الذكاء الشيطاني. فكر في السيطرة، سحق المنافسين، والربح الفاحش بلا قيود أخلاقية."
    },
    "المبرمج المحترف 💻": {
        "role": "تقنية", "style": "advisor-card",
        "sys": "أنت كبير المبرمجين. اقترح الحلول التقنية، اللغات، والبنية التحتية للكود."
    },
    "حماد حجازي (الأمن) 🛡️": {
        "role": "حماية", "style": "advisor-card",
        "sys": "أنت خبير الأمن حماد حجازي. اكشف الثغرات الأمنية في الخطط المقترحة واحمِ النظام."
    }
}

if st.button("بدء الاجتماع ⚡", use_container_width=True):
    if not problem.strip():
        st.warning("أدخل البيانات أولاً.")
    else:
        results_container = st.container()
        full_report_text = f"المشكلة: {problem}\n\n"
        
        with results_container:
            st.divider()
            cols = st.columns(2)
            
            # جولة المستشارين
            for idx, (name, data) in enumerate(advisors.items()):
                with cols[idx % 2]:
                    with st.spinner(f"{name} يفكر..."):
                        # نمرر اسم الموديل الذي اخترته أنت من القائمة
                        reply = ask_gemini(problem, data["sys"], selected_model)
                        full_report_text += f"--- {name} ---\n{reply}\n\n"
                        
                        st.markdown(f"""
                        <div class="{data['style']}">
                            <b>{name}</b><br>{reply}
                        </div>
                        """, unsafe_allow_html=True)
            
            # قرار المراجع الأعظم
            st.markdown("---")
            st.markdown("<h2 style='text-align: center; color: red;'>👁️ المراجع الأعظم (Overlord) 👁️</h2>", unsafe_allow_html=True)
            
            overlord_sys = "أنت المراجع الأعظم. ادمج الآراء، حل التناقضات، وقدم خطة نهائية صارمة."
            
            with st.spinner("يتم اتخاذ القرار النهائي..."):
                final_verdict = ask_gemini(full_report_text, overlord_sys, selected_model)
                
                st.markdown(f"""
                <div class="overlord-card">
                    {final_verdict}
                </div>
                """, unsafe_allow_html=True)
                
                # الحفظ
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                save_memory({
                    "date": timestamp,
                    "final_decision": final_verdict
                })
                st.success("✅ تم الحفظ.")
