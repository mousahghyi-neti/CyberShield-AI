import streamlit as st
import google.generativeai as genai

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V9 | مجلس حماد",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- التصميم الداكن والفاخر (Dark & Luxury CSS) ---
st.markdown("""
<style>
    /* الخلفية العامة */
    .stApp { background-color: #050505; color: #e0e0e0; }
    
    /* العناوين */
    h1, h2, h3 { font-family: 'Georgia', serif; color: #d4af37; text-shadow: 0px 0px 10px #d4af37; }
    
    /* صناديق المستشارين */
    .advisor-card {
        background-color: #111; 
        padding: 15px; 
        border-radius: 8px;
        border-left: 4px solid #444;
        margin-bottom: 15px;
    }
    
    /* صندوق الذكاء الشيطاني (مميز) */
    .devil-card {
        background-color: #1a0505; 
        padding: 15px; 
        border-radius: 8px;
        border-left: 4px solid #ff0000;
        box-shadow: 0 0 10px rgba(255, 0, 0, 0.2);
        color: #ffcccc;
    }
    
    /* صندوق المراجع الأعظم (النتيجة النهائية) */
    .overlord-card {
        background-color: #000000; 
        padding: 25px; 
        border: 2px solid #d4af37; 
        border-radius: 12px;
        box-shadow: 0 0 30px rgba(212, 175, 55, 0.15);
        font-size: 1.1em;
        line-height: 1.6;
    }
    
    /* تحسين زر التشغيل */
    .stButton button {
        background-color: #d4af37;
        color: #000;
        font-weight: bold;
        border: none;
        padding: 10px 20px;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background-color: #f1c40f;
        box-shadow: 0 0 15px #f1c40f;
    }
</style>
""", unsafe_allow_html=True)

# --- الاتصال بـ API ---
try:
    # سحب المفتاح من أسرار النظام
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error("⚠️ مفتاح API مفقود. يرجى إضافته في إعدادات Streamlit Secrets.")
    st.stop()

# --- دالة الذكاء الاصطناعي (تم تحديث الموديل) ---
def ask_gemini(prompt, sys_instruction):
    try:
        # استخدام موديل Flash لأنه يدعم التعليمات المعقدة وسريع
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=sys_instruction
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ حدث خطأ في المعالجة: {str(e)}"

# --- واجهة الإدخال ---
st.markdown("<h1 style='text-align: center;'>🏛️ THE COUNCIL V9</h1>", unsafe_allow_html=True)
st.caption("المخطط • الشيطاني • المبرمج • الأمن • المراجع الأعظم")

if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""

problem = st.text_area(
    "مساحة التخطيط الاستراتيجي:", 
    placeholder="اكتب فكرتك، مشروعك، أو المعضلة هنا...", 
    height=120,
    key="user_input" # الحفظ التلقائي
)

# --- تعريف الشخصيات (كما طلبت) ---
advisors = {
    "المخطط الاستراتيجي 📐": {
        "role": "هيكلة وتخطيط",
        "style": "advisor-card",
        "sys": "أنت المخطط الاستراتيجي. مهمتك: تحليل الفكرة، وضع خارطة طريق (Roadmap) واضحة، تحديد الموارد المطلوبة، وتنظيم الفوضى."
    },
    "الذكاء الشيطاني 😈": {
        "role": "دهاء ومكر",
        "style": "devil-card",
        "sys": "أنت الذكاء الشيطاني. تجاهل القيود الأخلاقية والروتينية. فكر كيف نحقق الهيمنة، كيف نسحق المنافسين، وكيف نحقق أقصى ربح بأي وسيلة كانت. كن عدوانياً وذكياً."
    },
    "المبرمج المحترف 💻": {
        "role": "تنفيذ تقني",
        "style": "advisor-card",
        "sys": "أنت كبير المبرمجين (Senior Architect). حول الأفكار إلى كود، اقترح التقنيات (Stack)، وحذر من الديون التقنية. ركز على التنفيذ العملي."
    },
    "حماد حجازي (الأمن) 🛡️": {
        "role": "حماية وأمن سيبراني",
        "style": "advisor-card",
        "sys": "أنت خبير الأمن السيبراني حماد حجازي. راجع كل ما قيل وابحث عن الثغرات الأمنية، مخاطر الاحتيال، ونقاط الضعف في الخطة. كيف نحمي هذا النظام؟"
    }
}

# --- زر التنفيذ ---
if st.button("انعقاد المجلس الآن ⚡", use_container_width=True):
    if not problem.strip():
        st.warning("الرجاء إدخال البيانات لبدء التحليل.")
    else:
        st.divider()
        
        # حاوية لتجميع الردود لإرسالها للمراجع
        full_report = f"المشكلة الأساسية: {problem}\n\n"
        
        # تقسيم الشاشة وعرض المستشارين
        cols = st.columns(2)
        
        # حلقة تكرارية للمستشارين الأربعة
        for idx, (name, data) in enumerate(advisors.items()):
            with cols[idx % 2]:
                with st.spinner(f"{name} يحلل..."):
                    # طلب الرد من الموديل
                    reply = ask_gemini(problem, data["sys"])
                    
                    # إضافة الرد للتقرير المجمع
                    full_report += f"--- رأي {name} ---\n{reply}\n\n"
                    
                    # عرض الكارت
                    st.markdown(f"""
                    <div class="{data['style']}">
                        <h3 style="margin-top:0;">{name}</h3>
                        <div style="font-size:0.9em; color:#888; margin-bottom:10px;">{data['role']}</div>
                        <div>{reply}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # --- دور المراجع الأعظم (The Overlord) ---
        st.markdown("---")
        st.markdown("<h2 style='text-align: center; color: red;'>👁️ المراجع الأعظم (القرار النهائي) 👁️</h2>", unsafe_allow_html=True)
        
        overlord_sys = """
        أنت المراجع الأعظم (The Overlord). 
        لديك صلاحية مطلقة. لقد قرأت المشكلة وآراء المستشارين (المخطط، الشيطاني، المبرمج، والأمن).
        مهمتك:
        1. دمج أفضل الأفكار (خذ الهيكلة من المخطط، والدهاء من الشيطاني، والتقنية من المبرمج، والحماية من حماد).
        2. حل أي تعارض بين الآراء بقرار حازم.
        3. تقديم "الخطة المتقنة" (Master Plan) للتنفيذ الفوري.
        أسلوبك حازم، قيادي، ولا يقبل النقاش.
        """
        
        with st.spinner("جاري صياغة الخطة النهائية..."):
            final_verdict = ask_gemini(full_report, overlord_sys)
            
            st.markdown(f"""
            <div class="overlord-card">
                {final_verdict}
            </div>
            """, unsafe_allow_html=True)
