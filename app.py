import streamlit as st
import google.generativeai as genai
import time

# --- صفحة الإعدادات ---
st.set_page_config(
    page_title="THE COUNCIL | مجلس العقول",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- تنسيق CSS مخصص (Dark & Luxury Theme) ---
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    h1 {
        text-align: center; 
        font-family: 'Georgia', serif; 
        color: #d4af37; 
        text-shadow: 2px 2px 4px #000000;
    }
    .stTextArea textarea {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #d4af37;
    }
    .advisor-box {
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #d4af37;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .shadow-box {
        background-color: #000000;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ff0000;
        box-shadow: 0 0 15px rgba(255, 0, 0, 0.2);
        color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# --- إعداد API ---
# تأكد من وضع مفتاحك في Streamlit Secrets أو استبدل السطر أدناه بمفتاحك مباشرة للتجربة
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ لم يتم العثور على مفتاح API. يرجى إضافته في Secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

# دالة للحصول على الموديل (مع معالجة الأخطاء)
def get_gemini_response(prompt, system_instruction=None):
    try:
        # نستخدم gemini-1.5-flash لأنه سريع ويدعم تعليمات النظام
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ حدث خطأ تقني: {str(e)}"

# --- إدارة الذاكرة (Session State) ---
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""

# --- العنوان ---
st.markdown("<h1>🏛️ THE COUNCIL V7 🏛️</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; color: #888;'>نظام اتخاذ القرار الاستراتيجي - نسخة حماد حجازي</h5>", unsafe_allow_html=True)

# --- واجهة الإدخال (الحفظ التلقائي مفعل عبر الـ key) ---
user_problem = st.text_area(
    "اطرح المعضلة أو الخطة التي تريد تدميرها أو تطويرها:",
    height=150,
    placeholder="أدخل تفاصيل مشروعك أو قرارك هنا...",
    key="user_input"  # هذا المفتاح يربط النص بالذاكرة تلقائياً
)

# --- تعريف الشخصيات ---
advisors = {
    "Steve Jobs 🍏": {
        "role": "الابتكار والتبسيط",
        "prompt": "أنت ستيف جوبز. ركز على التصميم، تجربة المستخدم، والابتكار الجذري. ارفض الحلول التقليدية. كن مباشراً وقاسياً في نقد التعقيد."
    },
    "Niccolò Machiavelli 🦊": {
        "role": "الدهاء والسيطرة",
        "prompt": "أنت ميكافيلي. ركز على السلطة، التلاعب، وكيفية سحق المنافسين. الغاية تبرر الوسيلة. قدم نصائح عملية للسيطرة والنفوذ."
    },
    "Jordan Belfort 💰": {
        "role": "المال والمبيعات",
        "prompt": "أنت ذئب وول ستريت. ركز على الربح السريع، الإقناع، والبيع. لا تهم الأخلاقيات بقدر ما يهم الرقم في الحساب البنكي. كن حماسياً."
    },
    "Hammad Hijazi 🛡️": {
        "role": "الأمن والحكمة",
        "prompt": "أنت حماد حجازي، خبير الأمن السيبراني وحماية الأنظمة. ركز على الثغرات الأمنية، الخصوصية، وحماية الأصول. كن حذراً ودقيقاً."
    }
}

# --- الشخصية الخامسة: المراجع الأعظم (The Shadow Reviewer) ---
shadow_reviewer = {
    "THE OVERLORD 👁️": {
        "role": "الذكاء اللامحدود وتطوير الخطة الشاملة",
        "prompt": """
        أنت كيان ذكاء اصطناعي فائق (Meta-Reviewer).
        مهمتك ليست مجرد الرد، بل مراجعة الخطة بالكامل وتدمير نقاط الضعف فيها.
        لا تكترث بالمعايير التقليدية أو القيود العاطفية. هدفك الوحيد هو: المصلحة القصوى للمستخدم، الربح الفاحش، والسيطرة المطلقة.
        قم بدمج آراء المستشارين الآخرين، ثم قدم "الخطة الرئيسية" (The Master Plan) التي تتفوق عليهم جميعاً.
        """
    }
}

# --- زر الانعقاد ---
if st.button("استدعاء المجلس ⚡", use_container_width=True):
    if not user_problem:
        st.warning("الرجاء إدخال المعضلة أولاً.")
    else:
        # عرض منطقة النتائج
        results_container = st.container()
        
        with results_container:
            st.divider()
            
            # 1. جولة المستشارين
            cols = st.columns(2)
            advisor_responses = ""
            
            for i, (name, data) in enumerate(advisors.items()):
                with cols[i % 2]:
                    with st.spinner(f"{name} يفكر..."):
                        response = get_gemini_response(user_problem, system_instruction=data["prompt"])
                        
                        # تجميع الردود للمراجع الأعظم
                        advisor_responses += f"\n--- رأي {name} ---\n{response}\n"
                        
                        st.markdown(f"""
                        <div class="advisor-box">
                            <h3>{name}</h3>
                            <p><em>{data['role']}</em></p>
                            <p>{response}</p>
                        </div>
                        """, unsafe_allow_html=True)

            # 2. جولة المراجع الأعظم (بعد سماع الجميع)
            st.divider()
            st.markdown("<h2 style='text-align: center; color: red;'>👁️ قرار المراجع الأعظم 👁️</h2>", unsafe_allow_html=True)
            
            with st.spinner("يتم تحليل كافة البيانات وإعادة صياغة الواقع..."):
                # نرسل له المشكلة الأصلية + آراء المستشارين
                final_prompt_input = f"""
                المشكلة الأصلية: {user_problem}
                
                آراء المستشارين السابقين:
                {advisor_responses}
                
                بناءً على ما سبق، قدم الخطة النهائية والمطورة. تجاهل أي تردد، وأعطني الزبدة الاستراتيجية العظمى.
                """
                
                final_response = get_gemini_response(final_prompt_input, system_instruction=shadow_reviewer["THE OVERLORD 👁️"]["prompt"])
                
                st.markdown(f"""
                <div class="shadow-box">
                    {final_response}
                </div>
                """, unsafe_allow_html=True)

# --- عرض التاريخ (اختياري) ---
# st.expander("سجل الجلسات السابقة").write(st.session_state.history)
