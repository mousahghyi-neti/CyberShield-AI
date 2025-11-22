import streamlit as st
import os
import sys
import io
from contextlib import redirect_stdout

# --- 1. ضبط البيئة (أهم خطوة) ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        # CrewAI و LiteLLM يحتاجان لهذه التسميات تحديداً
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
        os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("⚠️ مفتاح API مفقود.")
        st.stop()
except:
    st.stop()

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V23 | Flash Force",
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
    .result-box { background-color: #220000; color: #ffcccc; padding: 15px; border-radius: 5px; border: 1px solid red; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 2. تحديد الموديل (الثابت والآمن) ---
# لا بحث ديناميكي بعد الآن. نستخدم الفلاش لأنه الأضمن.
# الصيغة: provider/model
ACTIVE_MODEL = "gemini/gemini-1.5-flash"

# --- تعريف الأداة (Tool) ---
class DevTools:
    @tool("Python Executor")
    def execute_code(code: str):
        """
        Executes Python code securely. Input must be a clean python code string.
        Returns the output (stdout) or error message.
        """
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
st.markdown("<h1>💀 THE COUNCIL V23</h1>", unsafe_allow_html=True)
st.caption(f"System Locked on: **{ACTIVE_MODEL}** (Guaranteed Access)")

mission = st.text_area("أدخل المهمة التقنية:", height=100, placeholder="مثال: اكتب كود بايثون لاكتشاف المنافذ المفتوحة (Port Scanner) واختبره.")

if st.button("تنفيذ الهجوم البرمجي ⚡"):
    if not mission:
        st.warning("أدخل المهمة.")
    else:
        status_area = st.empty()
        status_area.info("⏳ جاري تجنيد الوكلاء...")

        try:
            # --- بناء الوكلاء ---
            # نمرر ACTIVE_MODEL مباشرة لكل وكيل
            
            planner = Agent(
                role='Strategist',
                goal='Plan execution steps.',
                backstory="أنت المخطط الاستراتيجي.",
                allow_delegation=False,
                verbose=True,
                llm=ACTIVE_MODEL
            )

            coder = Agent(
                role='Python Developer',
                goal='Write and RUN code.',
                backstory="أنت مبرمج محترف. استخدم الأداة لتشغيل الكود.",
                tools=[DevTools.execute_code],
                allow_delegation=False,
                verbose=True,
                llm=ACTIVE_MODEL
            )

            reviewer = Agent(
                role='Reviewer',
                goal='Validate output.',
                backstory="أنت المسؤول عن الجودة.",
                allow_delegation=False,
                verbose=True,
                llm=ACTIVE_MODEL
            )

            # --- المهام ---
            task1 = Task(
                description=f"Plan steps for: {mission}",
                agent=planner,
                expected_output="Plan steps."
            )

            task2 = Task(
                description="Write python code based on plan AND execute it using 'Python Executor'. Return code and result.",
                agent=coder,
                expected_output="Code and execution result."
            )

            task3 = Task(
                description="Review results and summarize.",
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
            
            status_area.success("✅ تمت المهمة.")
            st.markdown("### 📝 التقرير النهائي:")
            st.markdown(f"<div class='result-box'>{result}</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error Details: {str(e)}")
            st.info("تأكد من أنك تستخدم gemini-1.5-flash لأنه الأحدث.")
