import streamlit as st
import google.generativeai as genai
import json
import os
import datetime

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V10 | مجلس الخلود",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ملف الذاكرة (الصندوق الأسود) ---
MEMORY_FILE = "council_history.json"

# --- دوال إدارة الذاكرة والحفظ ---
def load_memory():
    """تحميل السجل من الملف المحلي"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_memory(record):
    """حفظ سجل جديد في الملف"""
    history = load_memory()
    history.append(record)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def clear_memory():
    """مسح الذاكرة"""
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)

# --- التصميم الفاخر (Dark & Gold) ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1, h2, h3 { font-family: 'Georgia', serif; color: #d4af37; text-shadow: 0px 0px 10px #d4af37; }
    
    /* بطاقات المستشارين */
    .advisor-card {
        background-color: #111; padding: 15px; border-radius: 8px;
        border-left: 4px solid #444; margin-bottom: 15px;
    }
    .devil-card {
        background-color: #1a0505; padding: 15px; border-radius: 8px;
        border-left: 4px solid #ff0000; color: #ffcccc;
        box-shadow: 0 0 10px rgba(255, 0, 0, 0.2);
    }
    /* بطاقة القرار النهائي */
    .overlord-card {
        background-color: #0a0a0a; padding: 25px; border: 2px solid #d4af37;
        border-radius: 12px; box-shadow: 0 0 30px rgba(212, 175, 55, 0.2);
        font-size: 1.1em; line-height: 1.6;
    }
    /* الشريط الجانبي */
    section[data-testid="stSidebar"] {
        background-color: #111;
        border-right: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# --- الاتصال بـ API ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ مفتاح API مفقود. يرجى إضافته في Secrets.")
    st.stop()

# --- دالة الذكاء الاصطناعي ---
def ask_gemini(prompt, sys_instruction):
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=sys_instruction
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ: {str(e)}"

# --- الشريط الجانبي (الأرشيف) ---
with st.sidebar:
    st.header("📂 أرشيف القرارات")
    
    # زر لتحميل ملف السجل
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 تحميل السجل الكامل (Backup)",
                data=f,
                file_name="council_backup.json",
                mime="application/json"
            )
    
    st.divider()
    
    # عرض الجلسات السابقة
    history_data = load_memory()
    if history_data:
        st.caption(f"لديك {len(history_data)} جلسات محفوظة.")
        for idx, item in enumerate(reversed(history_data)):
            with st.expander(f"📅 {item['date']} - {item['topic'][:20]}..."):
                st.markdown(f"**المشكلة:** {item['topic']}")
                st.markdown(f"**القرار النهائي:**\n{item['final_decision']}")
                st.markdown("---")
                st.text(item['details'])
    else:
        st.info("لا يوجد سجلات سابقة.")
    
    if st.button("🗑️ مسح الذاكرة", type="primary"):
        clear_memory()
        st.rerun()

# --- الواجهة الرئيسية ---
st.markdown("<h1 style='text-align: center;'>🏛️ THE COUNCIL V10</h1>", unsafe_allow_html=True)
st.caption("مجلس الخلود | التخزين التلقائي مفعل")

# مدخل المشكلة
problem = st.text_area("أدخل المعضلة الاستراتيجية:", height=100, placeholder="اكتب هنا...")

# تعريف الشخصيات
advisors = {
    "المخطط الاستراتيجي 📐": {
        "role": "هيكلة", "style": "advisor-card",
        "sys": "أنت المخطط. ضع خارطة طريق واضحة، خطوات تنفيذية، وجدول زمني."
    },
    "الذكاء الشيطاني 😈": {
        "role": "دهاء", "style": "devil-card",
        "sys": "أنت الذكاء الشيطاني. فكر في السيطرة، سحق المنافسين، والربح الفاحش بلا قيود."
    },
    "المبرمج المحترف 💻": {
        "role": "تقنية", "style": "advisor-card",
        "sys": "أنت كبير المبرمجين. اقترح الحلول التقنية، اللغات، والبنية التحتية."
    },
    "حماد حجازي (الأمن) 🛡️": {
        "role": "حماية", "style": "advisor-card",
        "sys": "أنت خبير الأمن حماد حجازي. اكشف الثغرات في الخطط المقترحة واحمِ النظام."
    }
}

if st.button("بدء الجلسة وحفظ البيانات 💾", use_container_width=True):
    if not problem.strip():
        st.warning("أدخل البيانات أولاً.")
    else:
        # حاوية النتائج
        results_container = st.container()
        
        full_report_text = f"المشكلة: {problem}\n\n"
        
        with results_container:
            st.divider()
            cols = st.columns(2)
            
            # جولة المستشارين
            for idx, (name, data) in enumerate(advisors.items()):
                with cols[idx % 2]:
                    with st.spinner(f"{name}..."):
                        reply = ask_gemini(problem, data["sys"])
                        full_report_text += f"--- {name} ---\n{reply}\n\n"
                        
                        st.markdown(f"""
                        <div class="{data['style']}">
                            <b>{name}</b><br>{reply}
                        </div>
                        """, unsafe_allow_html=True)
            
            # قرار المراجع الأعظم
            st.markdown("---")
            st.markdown("<h2 style='text-align: center; color: red;'>👁️ قرار المراجع الأعظم 👁️</h2>", unsafe_allow_html=True)
            
            overlord_sys = "أنت المراجع الأعظم. ادمج الآراء، حل التناقضات، وقدم خطة نهائية صارمة."
            
            with st.spinner("يتم اتخاذ القرار النهائي وحفظه في السجل..."):
                final_verdict = ask_gemini(full_report_text, overlord_sys)
                
                st.markdown(f"""
                <div class="overlord-card">
                    {final_verdict}
                </div>
                """, unsafe_allow_html=True)
                
                # --- الحفظ التلقائي ---
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_record = {
                    "date": timestamp,
                    "topic": problem,
                    "details": full_report_text,
                    "final_decision": final_verdict
                }
                save_memory(new_record)
                st.success("✅ تم حفظ الجلسة في الأرشيف (انظر الشريط الجانبي).")
