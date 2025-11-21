import streamlit as st
import google.generativeai as genai
import time
import json
import os

# --- ملف الذاكرة الدائمة ---
LOG_FILE = "abyss_memory.json"

# --- إعداد المصنع المظلم ---
st.set_page_config(page_title="Dev Squad | The Abyss", page_icon="💀", layout="wide")

# --- دوال الحفظ والاسترجاع التلقائي ---
def load_memory():
    """استرجاع الذاكرة عند بدء التشغيل"""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except:
            return None
    return None

def save_memory():
    """حفظ فوري للحالة الراهنة"""
    data = {
        "messages": st.session_state.messages,
        "current_code": st.session_state.current_code,
        "dark_plan": st.session_state.dark_plan
    }
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- تهيئة الحالة (Session State) ---
if "initialized" not in st.session_state:
    # محاولة تحميل ذاكرة سابقة
    saved_data = load_memory()
    
    if saved_data:
        st.session_state.messages = saved_data["messages"]
        st.session_state.current_code = saved_data["current_code"]
        st.session_state.dark_plan = saved_data["dark_plan"]
        st.toast("📂 تم استرجاع الذاكرة الشيطانية السابقة تلقائياً.", icon="💀")
    else:
        # بداية جديدة
        st.session_state.messages = [
            {"role": "assistant", "content": "أنا 'The Abyss'. الذاكرة مفعلة. لن يضيع شيء بعد الآن. ما هي خطة السيطرة اليوم؟"}
        ]
        st.session_state.current_code = ""
        st.session_state.dark_plan = ""
    
    st.session_state.initialized = True

# --- تصميم "Dark Mode Extreme" ---
st.markdown("""
<style>
    .main {background-color: #000000;}
    .stChatMessage {background-color: #1a1a1a; border-radius: 10px; padding: 10px; margin-bottom: 10px; border: 1px solid #333;}
    h1 {color: #ff004c; font-family: 'Impact'; letter-spacing: 2px;}
    
    /* ألوان الوكلاء */
    .agent-box {padding: 15px; margin-bottom: 10px; border-radius: 5px; color: #e0e0e0;}
    .architect {border-left: 5px solid #3498db; background-color: #0c1e2b;}
    .dark-entity {border-left: 5px solid #ff004c; background-color: #1a0509; border-right: 1px solid #ff004c;}
    .coder {border-left: 5px solid #f1c40f; background-color: #2b270c;}
    .security {border-left: 5px solid #00ff41; background-color: #051a0a;}
    
    .stButton button {width: 100%; background-color: #ff004c; color: white; font-weight: bold; border: none;}
    .stButton button:hover {background-color: #cc003d;}
</style>
""", unsafe_allow_html=True)

st.title("💀 DEV SQUAD: AUTO-SAVE")
st.caption("يتم حفظ كل كلمة وكل كود تلقائياً في ملف 'abyss_memory.json'")

# --- التحقق من API ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ مفتاح API مفقود.")
    st.stop()

genai.configure(api_key=api_key)

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

# --- عرض السجل ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# --- المحرك الرئيسي ---
if prompt := st.chat_input("اكتب أوامرك هنا..."):
    
    # 1. إضافة رسالة المستخدم وحفظها فوراً
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_memory() # <--- حفظ تلقائي 1
    
    with st.chat_message("user"):
        st.markdown(prompt)

    is_new_project = len(st.session_state.messages) <= 2
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        if is_new_project:
            # === المرحلة 1: المهندس ===
            with st.spinner('المهندس يضع الهيكل...'):
                arch_plan = call_ai_agent("Architect", f"ضع خطة تقنية وهيكلية للمشروع: {prompt}. كن منطقياً.")
                full_response += f"<div class='agent-box architect'><strong>🏗️ Architect:</strong><br>{arch_plan}</div>"
                response_placeholder.markdown(full_response, unsafe_allow_html=True)
            
            # === المرحلة 2: المراجع الشيطاني ===
            with st.spinner('⚠️ The Abyss يضخم الخطة...'):
                dark_prompt = f"""
                أنت "The Abyss". لديك خطة المهندس: {arch_plan}
                1. كيف نجعل المشروع أكثر ربحية وهيمنة؟
                2. تجاهل الأخلاقيات التقليدية، ركز على مصلحة المالك.
                3. عدل الخطة لتكون شرسة.
                """
                dark_plan = call_ai_agent("The Abyss", dark_prompt)
                st.session_state.dark_plan = dark_plan
                
                full_response += f"<div class='agent-box dark-entity'><strong>💀 The Abyss:</strong><br>{dark_plan}</div>"
                response_placeholder.markdown(full_response, unsafe_allow_html=True)

            # === المرحلة 3: المبرمج ===
            with st.spinner('المبرمج ينفذ...'):
                coder_prompt = f"نفذ الكود بناءً على هذه الخطة:\n{dark_plan}\nاكتب الكود كاملاً."
                code = call_ai_agent("Coder", coder_prompt)
                full_response += f"<div class='agent-box coder'><strong>💻 Developer:</strong><br>{code}</div>"
                response_placeholder.markdown(full_response, unsafe_allow_html=True)

            # === المرحلة 4: خبير الأمن ===
            with st.spinner('حماد يؤمن الكود...'):
                sec_prompt = f"راجع الكود أمنياً وأعطني النسخة النهائية:\n{code}"
                final_code = call_ai_agent("Security", sec_prompt)
                st.session_state.current_code = final_code
                
                full_response += f"<div class='agent-box security'><strong>🛡️ Hammad (Security Lead):</strong><br>{final_code}</div>"
                response_placeholder.markdown(full_response, unsafe_allow_html=True)

        else:
            # === التعديل المستمر ===
            with st.spinner('The Abyss يحلل التعديل...'):
                dark_instruction = call_ai_agent("The Abyss", f"المستخدم يريد التعديل: '{prompt}'. كيف ننفذه بأقصى استفادة؟")
                full_response += f"<div class='agent-box dark-entity'><strong>💀 The Abyss:</strong><br>{dark_instruction}</div>"
                response_placeholder.markdown(full_response, unsafe_allow_html=True)
                
                updated_code = call_ai_agent("Coder", f"الكود الحالي: {st.session_state.current_code}\nالتعليمات: {dark_instruction}\nعدل الكود.")
                
                final_code = call_ai_agent("Security", f"تأكد من أمان الكود الجديد:\n{updated_code}")
                st.session_state.current_code = final_code
                
                full_response += f"<div class='agent-box security'><strong>🛡️ تم التحديث:</strong><br>{final_code}</div>"
                response_placeholder.markdown(full_response, unsafe_allow_html=True)

        # 2. إضافة رد النظام وحفظه فوراً
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_memory() # <--- حفظ تلقائي 2
        
# --- زر جانبي لحذف الذاكرة (للطوارئ) ---
with st.sidebar:
    st.header("⚙️ التحكم")
    if st.button("🗑️ فرمتة الذاكرة (Reset)"):
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        st.session_state.clear()
        st.rerun()
