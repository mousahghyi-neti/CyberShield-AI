import streamlit as st
import google.generativeai as genai

# --- إعداد الصفحة ---
st.set_page_config(page_title="CyberShield 2025", page_icon="🛡️", layout="centered")

# --- التصميم ---
st.markdown("""
<style>
    .main {background-color: #0e1117; color: #fff;}
    h1 {color: #00ff41; text-align: center;}
    .stButton button {width: 100%; background-color: #28a745; color: white; font-weight: bold;}
    .report {background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-left: 5px solid #00ff41;}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ كاشف الاحتيال (Gen 2.5)")
st.caption("Powered by Hammad Hijazi | Gemini 2.5 Flash Engine")

# --- الاتصال بالمحرك ---
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ مفتاح API مفقود. تأكد من وضعه في Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# --- استخدام الموديل الذي ظهر في قائمتك ---
# اخترنا هذا الموديل لأنه الأسرع والأحدث في قائمتك
model = genai.GenerativeModel('gemini-2.5-flash')

# --- الواجهة ---
user_input = st.text_area("انسخ الرسالة أو الرابط المشبوه هنا:", height=150)

if st.button("🔍 فحص أمني فوري"):
    if not user_input:
        st.warning("الرجاء إدخال نص للتحليل.")
    else:
        try:
            with st.spinner('جاري تحليل النوايا الخبيثة باستخدام Gemini 2.5...'):
                # هندسة الأوامر
                prompt = f"""
                أنت خبير أمن سيبراني. حلل النص التالي:
                "{user_input}"
                
                هل هذا احتيال؟ (نعم/لا)
                ما هي العلامات الحمراء؟
                ما النصيحة للمستخدم؟
                اجعل الإجابة قصيرة، حازمة، وبالعربية.
                """
                response = model.generate_content(prompt)
                
                # عرض النتيجة
                st.markdown("---")
                st.markdown(f"""
                <div class="report">
                {response.text}
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
