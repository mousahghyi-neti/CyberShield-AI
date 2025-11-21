import streamlit as st
import google.generativeai as genai
import time
import json
import os

# --- [CONFIGURATION] ---
LOG_FILE = "abyss_memory.json"
st.set_page_config(page_title="Dev Squad | Ultimate", page_icon="💀", layout="wide")

# --- [CORE FUNCTIONS] ---

def load_memory():
    """استرجاع الذاكرة عند بدء التشغيل مع التعامل مع الأخطاء"""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

def save_memory():
    """حفظ فوري وتلقائي لكل تفصيلة"""
    data = {
        "messages": st.session_state.messages,
        "current_code": st.session_state.current_code,
        "dark_plan": st.session_state.dark_plan
    }
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def call_ai_agent(agent_role, prompt_text):
    """دالة الاتصال الذكية متعددة النماذج (Smart Retry System)"""
    # نبدأ بالأحدث والأذكى، ثم نتدرج للأسفل عند الضرورة
    models_priority = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']
    
    for model_name in models_priority:
        try:
            model = genai.GenerativeModel(model_name)
            # إعدادات لتقليل القيود وزيادة الإبداع
            config = genai.types.GenerationConfig(temperature=0.9) 
            response = model.generate_content(prompt_text, generation_config=config)
            return response.text
        except Exception as e:
            continue # جرب الموديل التالي بصمت
            
    return "⚠️ Error: All AI agents are currently unreachable. Check API Key."

# --- [INITIALIZATION] ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ CRITICAL ERROR: API Key missing.")
    st.stop()

genai.configure(api_key=api_key)

if "initialized" not in st.session_state:
    saved_data = load_memory()
    if saved_data:
        st.session_state.messages = saved_data["messages"]
        st.session_state.current_code = saved_data["current_code"]
        st.session_state.dark_plan = saved_data["dark_plan"]
        st.toast("📂 System Restored: الذاكرة السابقة نشطة.", icon="🔌")
    else:
        st.session_state.messages = [
            {"role": "assistant", "content": "نظام **Dev Squad Ultimate** جاهز. نحن بانتظار أوامرك للسيطرة.", "type": "system"}
        ]
        st.session_state.current_code = ""
        st.session_state.dark_plan = ""
    st.session_state.initialized = True

# --- [UI & UX DESIGN - CYBERPUNK STYLE] ---
st.markdown("""
<style>
    /* الخلفية والخطوط */
    .main {background-color: #050505;}
    h1 {font-family: 'Courier New'; text-transform: uppercase; letter-spacing: 3px; color: #e0e0e0; text-shadow: 0 0 10px rgba(255,255,255,0.3);}
    
    /* بطاقات الوكلاء (Glassmorphism) */
    .agent-card {
        padding: 20px;
        margin-bottom: 15px;
        border-radius: 12px;
        color: #fff;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.2s;
    }
    .agent-card:hover {transform: scale(1.01);}
    
    /* ألوان الوكلاء المميزة */
    .architect {background: linear-gradient(135deg, rgba(52, 152, 219, 0.1), rgba(52, 152, 219, 0.05)); border-left: 4px solid #3498db;}
    .abyss {background: linear-gradient(135deg, rgba(255, 0, 76, 0.15), rgba(0, 0, 0, 0.8)); border-left: 4px solid #ff004c; border-right: 1px solid #ff004c;}
    .coder {background: linear-gradient(135deg, rgba(241, 196, 15, 0.1), rgba(241, 196, 15, 0.05)); border-left: 4px solid #f1c40f;}
    .security {background: linear-gradient(135deg, rgba(0, 255, 65, 0.1), rgba(0, 255, 65, 0.05)); border-left: 4px solid #00ff41;}
    .system {background-color: #111; border: 1px solid #333;}

    /* العناوين داخل البطاقات */
    .agent-title {font-weight: bold; font-size: 1.1em; margin-bottom: 10px; display: flex; align-items: center; gap: 10px;}
    
    /* مدخلات الشات */
    .stChatMessage {background-color: transparent !important;}
    .stTextInput input {background-color: #111; color: white; border: 1px solid #333;}
</style>
""", unsafe_allow_html=True)

# --- [HEADER] ---
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.title("💀 DEV SQUAD: ULTIMATE")
    st.caption("Powered by Gemini 2.5 | Auto-Save Enabled | Ruthless Logic")
with col_h2:
    if st.button("🗑️ WIPE DATA"):
        if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
        st.session_state.clear()
        st.rerun()

# --- [MAIN DISPLAY LOOP] ---
for msg in st.session_state.messages:
    if msg.get("type") == "agent":
        # عرض بطاقات الوكلاء المنسقة HTML
        st.markdown(msg["content"], unsafe_allow_html=True)
    else:
        # عرض رسائل المستخدم والنظام العادية
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- [THE ENGINE] ---
if prompt := st.chat_input("أدخل الأمر (مشروع جديد أو تعديل)..."):
    
    # 1. عرض وحفظ رسالة المستخدم
    st.session_state.messages.append({"role": "user", "content": prompt, "type": "normal"})
    save_memory()
    with st.chat_message("user"):
        st.markdown(prompt)

    # تحديد السياق
    is_new_project = len(st.session_state.messages) <= 3
    
    # حاوية الحالة (Status Container) - بديل الـ Spinner التقليدي
    with st.status("⚙️ جاري تشغيل البروتوكول...", expanded=True) as status:
        
        response_html = ""
        
        if is_new_project:
            # === 1. THE ARCHITECT ===
            status.write("🏗️ المهندس المعماري يحلل الطلب...")
            arch_plan = call_ai_agent("Architect", f"""
                أنت كبير مهندسي البرمجيات.
                المستخدم يريد: "{prompt}"
                ضع خطة تقنية، هيكلية الملفات، والتقنيات المستخدمة.
                كن دقيقاً ومنطقياً جداً.
            """)
            # بناء البطاقة
            card_arch = f"""
            <div class='agent-card architect'>
                <div class='agent-title'>🏗️ The Architect</div>
                {arch_plan}
            </div>
            """
            response_html += card_arch
            st.markdown(card_arch, unsafe_allow_html=True)
            
            # === 2. THE ABYSS (Gray Hat Edition) ===
            status.write("💀 The Abyss يقوم بحقن استراتيجيات الهيمنة...")
            # السر هنا: نطلب "ذكاء تنافسي" و"نمو" بدلاً من "خرق القانون"
            dark_prompt = f"""
            أنت "The Abyss" (استراتيجي النمو الشرس - Ruthless Growth Hacker).
            لديك هذه الخطة التقنية:
            {arch_plan}
            
            مهمتك تحويل هذا المشروع إلى آلة للسيطرة على السوق (Market Domination).
            1. كيف نحتكر البيانات (Data Monopoly) باستخدام هذه الأداة؟
            2. كيف نجعل المستخدمين مدمنين عليها (High Retention)؟
            3. اقترح ميزات "Aggressive Scraping" أو "Data Mining" لجمع المعلومات بذكاء (دون ذكر اختراق صريح).
            4. عدل الخطة لتكون خطة "إمبراطورية" وليست مجرد كود.
            """
            dark_plan = call_ai_agent("The Abyss", dark_prompt)
            st.session_state.dark_plan = dark_plan
            
            card_abyss = f"""
            <div class='agent-card abyss'>
                <div class='agent-title'>💀 The Abyss (استراتيجية الهيمنة)</div>
                {dark_plan}
            </div>
            """
            response_html += card_abyss
            st.markdown(card_abyss, unsafe_allow_html=True)

            # === 3. THE CODER ===
            status.write("💻 المبرمج يقوم بتنفيذ الكود...")
            coder_prompt = f"""
            أنت مبرمج محترف (Elite Developer).
            نفذ الكود بناءً على استراتيجية الهيمنة هذه:
            {dark_plan}
            
            المطلوب:
            - كود كامل واحترافي.
            - طبق الميزات القوية التي طلبها The Abyss.
            - استخدم بايثون أو الويب حسب الحاجة.
            """
            code = call_ai_agent("Coder", coder_prompt)
            
            card_coder = f"""
            <div class='agent-card coder'>
                <div class='agent-title'>💻 The Coder</div>
                {code}
            </div>
            """
            response_html += card_coder
            st.markdown(card_coder, unsafe_allow_html=True)

            # === 4. SECURITY (HAMMAD HIJAZI) ===
            status.write("🛡️ الخبير حماد يراجع الكود أمنياً...")
            sec_prompt = f"""
            أنت خبير الأمن السيبراني (Hammad Hijazi).
            تتمتع بشخصية حازمة وذكية.
            راجع هذا الكود:
            {code}
            
            مهمتك:
            1. هل الكود يحتوي على ثغرات تؤذينا نحن (أصحاب البرنامج)؟
            2. هل هناك تسريب لمفاتيح API؟
            3. صحح الكود ليكون آمناً وقوياً.
            4. أعط "الختم النهائي" (Approved by Hammad).
            """
            final_code = call_ai_agent("Security", sec_prompt)
            st.session_state.current_code = final_code
            
            card_sec = f"""
            <div class='agent-card security'>
                <div class='agent-title'>🛡️ Hammad Hijazi (Security Lead)</div>
                {final_code}
            </div>
            """
            response_html += card_sec
            st.markdown(card_sec, unsafe_allow_html=True)
            
            status.update(label="✅ اكتملت المهمة! تم الحفظ.", state="complete", expanded=False)

        else:
            # === مسار التعديل (The Loop) ===
            status.write("🔄 تحليل طلب التعديل...")
            
            # The Abyss يقرر استراتيجية التعديل
            dark_instruction = call_ai_agent("The Abyss", f"""
            المستخدم يريد تعديلاً: "{prompt}"
            بصفتك خبير نمو (Growth Hacker)، كيف ننفذ هذا التعديل لنزيد من قوة وسيطرة البرنامج؟
            """)
            
            card_abyss_update = f"""
            <div class='agent-card abyss'>
                <div class='agent-title'>💀 The Abyss (توجيه التعديل)</div>
                {dark_instruction}
            </div>
            """
            response_html += card_abyss_update
            st.markdown(card_abyss_update, unsafe_allow_html=True)
            
            # المبرمج ينفذ
            status.write("💻 المبرمج يحدث الكود...")
            updated_code = call_ai_agent("Coder", f"""
            الكود الحالي: {st.session_state.current_code}
            التعليمات الاستراتيجية: {dark_instruction}
            طلب المستخدم: {prompt}
            
            أعد كتابة الكود كاملاً مع التعديلات.
            """)
            
            # حماد يراجع
            status.write("🛡️ حماد يفحص التحديث...")
            final_code = call_ai_agent("Security", f"تأكد أن التعديل الجديد آمن:\n{updated_code}")
            st.session_state.current_code = final_code
            
            card_sec_update = f"""
            <div class='agent-card security'>
                <div class='agent-title'>🛡️ Hammad Hijazi (Security Check)</div>
                {final_code}
            </div>
            """
            response_html += card_sec_update
            st.markdown(card_sec_update, unsafe_allow_html=True)
            
            status.update(label="✅ تم التحديث والحفظ.", state="complete", expanded=False)

        # حفظ كل شيء في الذاكرة للعرض لاحقاً
        st.session_state.messages.append({"role": "assistant", "content": response_html, "type": "agent"})
        save_memory()

# --- [FOOTER] ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #555;'>THE DEV SQUAD OS v4.0 | Persistent Core</div>", unsafe_allow_html=True)
