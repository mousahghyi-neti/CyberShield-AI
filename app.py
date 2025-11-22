import streamlit as st
import os
import sys
import io
from contextlib import redirect_stdout

# --- 1. ضبط البيئة (أخطر مرحلة) ---
# يجب ضبط المفاتيح قبل استيراد CrewAI لضمان عمل LiteLLM
try:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
        os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("⚠️ مفتاح GEMINI_API_KEY مفقود في Secrets.")
        st.stop()
except Exception as e:
    st.error(f"خطأ في إعداد المفاتيح: {e}")
    st.stop()

# --- استيراد المكتبات بعد ضبط المفاتيح ---
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
import google.generativeai as genai

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V22 | Bulletproof",
    page_icon="💀",
    layout="wide"
)

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #050000; color: #e0e0e0; }
    h1 { color: #ff3333; font-family: 'Courier New', monospace; text-shadow: 0 0 10px #ff0000; text-align:center; }
    .stButton button { background-color: #990000; color: white; border: 1px solid red; width: 100%; }
    .stButton button:hover { background-color: #ff0000; box-shadow: 0 0 15px red; }
    .console-box { background-color: #111; color: #00ff00; padding: 15px; border-radius: 5px; font-family: monospace; border-left: 5px solid #00ff00; }
    .result-box { background-color: #220000; color: #ffcccc; padding: 15px; border-radius: 5px; border: 1px solid red; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# --- دالة اختيار الموديل الذكي ---
def get_smart_model_string():
    """
    تعيد اسم الموديل بصيغة نصية تفهمها CrewAI مباشرة.
    """
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # الأفضلية للموديلات القوية
        if any("gemini-1.5-pro" in m for m in models):
            return "gemini/gemini-1.5-pro"
        elif any("gemini-1.5-flash" in m for m in models):
            return "gemini/gemini-1.5-flash"
        else:
            return "gemini/gemini-pro"
    except:
        # الخيار الآمن جداً في حال فشل البحث
        return "gemini/gemini-1.5-flash"

# --- تعريف الأداة (Tool) ---
# نستخدم Decorator الخاص بـ CrewAI مباشرة لتجنب مشاكل LangChain
class DevTools:
    @tool("Python Executor")
    def execute_code(code: str):
        """
        Executes Python code securely. Input must be a clean python code string.
        Returns the output (stdout) or error message.
        """
        # تنظيف الكود من علامات الماركداون
        cleaned_code = code.replace("```python", "").replace("```", "").strip()
        
        buffer = io.StringIO()
        try:
            with redirect_stdout(buffer):
                exec(cleaned_code, globals())
            output = buffer.getvalue()
            return f"✅ Output:\n{output}" if output else "✅ Code executed (No Output)"
        except Exception as e:
            return f"❌ Error:\n{str(e)}"

# --- الواجهة الرئيسية ---
st.markdown("<h1>💀 THE COUNCIL V22</h1>", unsafe_allow_html=True)

# تحديد الموديل مرة واحدة عند التحميل
if 'model_name' not in st.session_state:
    with st.spinner("جاري تأمين الاتصال بالمحرك..."):
        st.session_state['model_name'] = get_smart_model_string()

st.caption(f"System Active using: **{st.session_state['model_name']}**")

mission = st.text_area("أدخل المهمة التقنية:", height=100, placeholder="مثال: اكتب كود بايثون لإنشاء كلمة مرور قوية واختبرها.")

if st.button("تنفيذ الهجوم البرمجي ⚡"):
    if not mission:
        st.warning("أدخل المهمة.")
    else:
        status_area = st.empty()
        status_area.info("⏳ جاري تجنيد الوكلاء وبدء العمليات...")

        try:
            # --- بناء الوكلاء (داخل الزر لتجنب مشاكل الذاكرة) ---
            # ملاحظة: نمرر اسم الموديل كنص (String) وهذا هو الحل السحري للخطأ السابق
            
            planner = Agent(
                role='Strategist',
                goal='Plan the execution steps.',
                backstory="أنت المخطط الاستراتيجي.",
                allow_delegation=False,
                verbose=True,
                llm=st.session_state['model_name']
            )

            coder = Agent(
                role='Python Developer',
                goal='Write and RUN code using the tool.',
                backstory="أنت مبرمج محترف. لا تسلم كوداً قبل تجربته.",
                tools=[DevTools.execute_code], # تمرير الأداة
                allow_delegation=False,
                verbose=True,
                llm=st.session_state['model_name']
            )

            reviewer = Agent(
                role='Reviewer',
                goal='Validate the output.',
                backstory="أنت المسؤول عن الجودة.",
                allow_delegation=False,
                verbose=True,
                llm=st.session_state['model_name']
            )

            # --- المهام ---
            task1 = Task(
                description=f"Plan steps for: {mission}",
                agent=planner,
                expected_output="A step-by-step plan."
            )

            task2 = Task(
                description="Write the python code based on the plan AND execute it using 'Python Executor'. Return the code and the execution output.",
                agent=coder,
                expected_output="Source code and its execution result."
            )

            task3 = Task(
                description="Review the code and the result. Provide a final summary.",
                agent=reviewer,
                expected_output="Final Report."
            )

            # --- الطاقم ---
            crew = Crew(
                agents=[planner, coder, reviewer],
                tasks=[task1, task2, task3],
                verbose=True,
                process=Process.sequential
            )

            # --- التشغيل ---
            result = crew.kickoff()
            
            status_area.success("✅ تمت المهمة بنجاح.")
            
            st.markdown("### 📝 التقرير النهائي:")
            st.markdown(f"<div class='result-box'>{result}</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"حدث خطأ فني: {str(e)}")
            st.warning("تأكد من أن requirements.txt يحتوي على: crewai, litellm, google-generativeai")
