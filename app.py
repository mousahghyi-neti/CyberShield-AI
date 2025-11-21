import streamlit as st
import google.generativeai as genai

# إعداد الصفحة
st.set_page_config(page_title="CyberShield", page_icon="🛡️")
st.title("🛡️ كاشف الاحتيال الذكي")

# جلب المفتاح
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("لم يتم العثور على مفتاح API في الأسرار.")
    st.stop()

genai.configure(api_key=api_key)

# استخدام الموديل المستقر
model = genai.GenerativeModel('gemini-pro')

user_input = st.text_area("ضع الرسالة هنا للتحليل:")

if st.button("تحليل"):
    if not user_input:
        st.warning("اكتب شيئاً أولاً.")
    else:
        try:
            with st.spinner('جاري التحليل...'):
                response = model.generate_content(f"حلل هذه الرسالة أمنياً وهل هي احتيال؟: {user_input}")
                st.success("النتيجة:")
                st.write(response.text)
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
            # كود فحص الموديلات المتاحة (للمطورين)
            st.write("---")
            st.info("جاري فحص الموديلات المتاحة في السيرفر...")
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        st.code(m.name)
            except:
                pass
