import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- إعداد الصفحة ---
st.set_page_config(page_title="CyberShield Pro", page_icon="🛡️", layout="centered")

# --- التصميم ---
st.markdown("""
<style>
    .main {background-color: #0e1117; color: #fff;}
    h1 {color: #00ff41; text-align: center;}
    .stButton button {width: 100%; background-color: #28a745; color: white; font-weight: bold;}
    .report {background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-left: 5px solid #00ff41;}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ كاشف الاحتيال الشامل")
st.caption("Powered by Hammad Hijazi | Supports Text & Screenshots")

# --- الاتصال بالمحرك ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ مفتاح API مفقود.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- خيارات الإدخال ---
option = st.radio("ماذا تريد أن تفحص؟", ("نص مشبوه", "صورة / لقطة شاشة"))

user_input = None
image_input = None

if option == "نص مشبوه":
    user_input = st.text_area("انسخ الرسالة هنا:", height=150)
else:
    image_upload = st.file_uploader("ارفع صورة المحادثة أو البريد الإلكتروني", type=["jpg", "png", "jpeg"])
    if image_upload:
        image_input = Image.open(image_upload)
        st.image(image_input, caption="الصورة المرفقة", use_column_width=True)

if st.button("🔍 فحص أمني فوري"):
    if not user_input and not image_input:
        st.warning("الرجاء إدخال بيانات للتحليل.")
    else:
        try:
            with st.spinner('جاري تحليل الأدلة الجنائية...'):
                
                # هندسة الأوامر للنص أو الصورة
                prompt = """
                أنت خبير أمن سيبراني (Hammad Hijazi). 
                حلل هذا المحتوى (سواء كان نصاً أو صورة).
                استخرج النصوص من الصورة إن وجدت وحللها.
                
                1. هل هذا احتيال؟ (نعم/لا)
                2. ما هي العلامات الحمراء؟
                3. النصيحة الذهبية للمستخدم؟
                
                اجعل الإجابة بالعربية ومنسقة.
                """
                
                if image_input:
                    # إرسال الصورة والبرومبت معاً
                    response = model.generate_content([prompt, image_input])
                else:
                    # إرسال النص والبرومبت
                    response = model.generate_content(f"{prompt}\nالنص للتحليل: {user_input}")
                
                # عرض النتيجة
                st.markdown("---")
                st.markdown(f"""
                <div class="report">
                {response.text}
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
