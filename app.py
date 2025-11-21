import streamlit as st
import google.generativeai as genai
import time

# --- إعداد المصنع ---
st.set_page_config(page_title="Dev Squad AI | Interactive", page_icon="👨‍💻", layout="wide")

# --- تنسيق CSS ---
st.markdown("""
<style>
    .main {background-color: #0e1117;}
    .stChatMessage {background-color: #262730; border-radius: 10px; padding: 10px; margin-bottom: 10px;}
    .stMarkdown code {background-color: #1e1e1e !important; color: #00ff41 !important;}
    h1 {color: #00ff41; font-family: 'Courier New';}
</style>
""", unsafe_allow_html=True)

st.title("👨‍💻 THE DEV SQUAD (Interactive Mode)")
st.caption("فريقك البرمجي الخاص: اطلب، عدّل، وطور بلا حدود.")

# --- التحقق من API ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ مفتاح API مفقود.")
    st.stop()

genai.configure(api_key=api_key)

# --- تهيئة الذاكرة (Session State) ---
if "messages" not in st.session_state:
    # رسالة ترحيبية من النظام
    st.session_state.messages = [
        {"role": "assistant", "content": "أهلاً بك يا قائد. أنا جاهز لبدء المشروع. صف لي ماذا تريد أن نبني؟"}
    ]
if "current_code" not in st.session_state:
    st.session_state.current_code = "" # نحتفظ بآخر نسخة من الكود هنا

# --- دالة الاتصال الذكية ---
def call_ai_agent(agent_role, prompt_text):
    models_priority = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']
    for model_name in models_priority:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt_text)
            return response.text
        except:
            continue
    return "Error: Connection failed."

# --- عرض سجل المحادثة السابق ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- استقبال طلبات المستخدم (الحوار المستمر) ---
if prompt := st.chat_input("اكتب طلبك الجديد أو التعديل هنا..."):
    
    # 1. عرض رسالة المستخدم
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. تحديد نوع العمل (هل هو مشروع جديد أم تعديل؟)
    is_new_project = len(st.session_state.messages) <= 2
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        if is_new_project:
            # === المسار 1: مشروع جديد (Architect -> Coder -> Security) ===
            with st.spinner('جاري تخطيط وبناء المشروع من الصفر...'):
                
                # المهندس
                arch_plan = call_ai_agent("Architect", f"ضع خطة هيكلية لطلب المستخدم: {prompt}")
                full_response += f"### 🏗️ خطة المهندس:\n{arch_plan}\n\n---\n"
                response_placeholder.markdown(full_response)
                
                # المبرمج
                coder_prompt = f"اكتب كود المشروع بناءً على الخطة: {arch_plan}. اجعل الكود كاملاً."
                code = call_ai_agent("Coder", coder_prompt)
                full_response += f"### 💻 كود المبرمج:\n{code}\n\n---\n"
                response_placeholder.markdown(full_response)
                
                # الحماية (أنت)
                sec_prompt = f"راجع هذا الكود أمنياً وأصلحه: \n{code}"
                final_code = call_ai_agent("Security", sec_prompt)
                full_response += f"### 🛡️ المراجعة الأمنية (Hammad):\n{final_code}"
                
                # حفظ الكود في الذاكرة
                st.session_state.current_code = final_code

        else:
            # === المسار 2: تعديل وتطوير (Coder -> Security) ===
            # هنا لا نحتاج المهندس، نحتاج المبرمج يعدل الكود الموجود
            with st.spinner('جاري تطبيق التعديلات على الكود الحالي...'):
                
                update_prompt = f"""
                لديك الكود الحالي التالي:
                {st.session_state.current_code}
                
                طلب المستخدم للتعديل:
                "{prompt}"
                
                المهمة:
                1. قم بتعديل الكود لتلبية الطلب.
                2. حافظ على الأجزاء السليمة.
                3. أعطني الكود الجديد كاملاً.
                """
                updated_code = call_ai_agent("Coder", update_prompt)
                
                # فحص أمني سريع للتعديل
                sec_check_prompt = f"تأكد أن التعديل الجديد لم يكسر الأمان في هذا الكود:\n{updated_code}"
                final_code = call_ai_agent("Security", sec_check_prompt)
                
                full_response += f"### ✅ تم التحديث:\n{final_code}"
                
                # تحديث الذاكرة
                st.session_state.current_code = final_code

        # عرض النتيجة النهائية وحفظها في السجل
        response_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
