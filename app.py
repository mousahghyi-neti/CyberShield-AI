import streamlit as st
import google.generativeai as genai
import time

# --- إعداد الصفحة لتكون احترافية وغامضة ---
st.set_page_config(page_title="CyberShield AI | حماد حجازي", page_icon="🛡️", layout="centered")

# --- التصميم البصري (Dark & Professional) ---
st.markdown("""
<style>
    .main {background-color: #0e1117; color: #ffffff;}
    .stTextArea textarea {font-size: 16px; background-color: #262730; color: white;}
    h1 {color: #00ff41; text-align: center; font-family: 'Courier New', monospace;}
    .stButton button {width: 100%; background-color: #ff4b4b; color: white; font-weight: bold;}
    .report-box {border: 1px solid #444; padding: 20px; border-radius: 10px; background-color: #1e1e1e;}
</style>
""", unsafe_allow_html=True)

# --- العنوان ---
st.title("👁️ كاشف النوايا الخبيثة")
st.caption("Powered by Hammad Hijazi's Security Logic")

# --- إعداد مفتاح API (المستخدم يدخل مفتاحه الخاص أو نضع مفتاحاً عاماً لاحقاً) ---
# ملاحظة للخبراء: يمكن الحصول على المفتاح مجاناً من Google AI Studio
api_key = st.secrets.get("GEMINI_API_KEY") # أو يمكن وضعه مباشرة للتجربة

if not api_key:
    api_key = st.text_input("أدخل مفتاح Google Gemini API (مجاني):", type="password")

# --- المنطق البرمجي ---
def analyze_text(text):
    if not api_key:
        return "الرجاء إدخال مفتاح API."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # هنا يكمن السحر: هندسة الأوامر (Prompt Engineering) لتقمص شخصيتك
    prompt = f"""
    أنت خبير أمن سيبراني عالمي (Hammad Hijazi). مهمتك تحليل النص التالي الذي وصل للمستخدم.
    لا تبحث عن فيروسات، بل ابحث عن "الهندسة الاجتماعية".
    
    النص المراد تحليله:
    "{text}"
    
    المطلوب منك تقديم تقرير بصيغة JSON يحتوي على:
    1. "risk_score": نسبة الخطر من 0 إلى 100.
    2. "verdict": حكم نهائي (آمن، مريب، احتيال مؤكد).
    3. "psychological_trigger": ما هي الحيلة النفسية المستخدمة؟ (مثلاً: الاستعجال، الخوف من ضياع الفرصة، انتحال السلطة).
    4. "expert_advice": نصيحة واحدة قاتلة للمستخدم.
    
    اجعل الإجابة بالعربية، احترافية، ومباشرة.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"حدث خطأ في التحليل: {e}"

# --- واجهة المستخدم ---
user_input = st.text_area("أدخل نص الرسالة، الإيميل، أو الرابط المشبوه هنا:", height=150)

if st.button("🚀 كشف الحقيقة"):
    if user_input:
        with st.spinner('جاري استدعاء الذكاء الاصطناعي وتحليل الثغرات النفسية...'):
            # محاكاة وقت المعالجة لزيادة التشويق
            time.sleep(1.5)
            result = analyze_text(user_input)
            
            st.markdown("---")
            st.markdown(f"""
            <div class="report-box">
            {result}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("يرجى إدخال نص للتحليل.")

# --- تذييل الصفحة ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>© 2025 Hammad Hijazi - Digital Sovereignty</p>", unsafe_allow_html=True)
