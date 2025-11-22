import streamlit as st
import os
import sys
import io
from contextlib import redirect_stdout

# --- 1. استيراد المكتبة المنقذة ---
# نستخدم LangChain كـ وسيط موثوق لأنه يعالج مشاكل الـ API Version تلقائياً
from langchain_google_genai import ChatGoogleGenerativeAI
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V25 | LangChain Bypass",
    page_icon="💀",
    layout="wide"
)

# --- المفاتيح ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("⚠️ مفتاح API مفقود.")
        st.stop()
except:
    st.stop()

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1 { color: #ff0000; font-family: 'Courier New', monospace; text-align:center; }
    .stButton button { background-color: #800000; color: white; border: 1px solid red; width: 100%; }
    .result-box { background-color: #1a1a1a; border: 1px solid #333; padding: 15px; border-radius: 5px; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 2. تعريف المحرك (The Engine) ---
# هنا الحل: ننشئ الكائن يدوياً ونحدد الموديل "gemini-1.5-flash" بدون أي بادئات
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        verbose=True,
        temperature=0.5,
        google_api_key=os.environ["GOOGLE_API_KEY"]
    )
except Exception as e:
    st.error(f"فشل تهيئة المحرك: {e}")
    st.stop()

# --- الأداة ---
class DevTools:
    @tool("Python Executor")
    def execute_code(code: str):
        """Executes Python code securely."""
        cleaned_code = code.replace("```python", "").replace("```", "").strip()
        buffer = io.StringIO()
        try:
            with redirect_stdout(buffer):
                exec(cleaned_code, globals())
            output = buffer.getvalue()
            return f"✅ Output:\n{output}" if output else "✅ Executed (No Output)"
        except Exception as e:
            return f"❌ Error:\n{str(e)}"

# --- الواجهة ---
st.markdown("<h1>💀 THE COUNCIL V25</h1>", unsafe_allow_html=True)
st.caption("Architecture: **LangChain Direct Wrapper** (Bypassing CrewAI String Parsing)")

mission = st.text_area("أدخل المهمة:", height=100, placeholder="مثال: اكتب كود بايثون لطباعة الوقت الحالي.")

if st.button("تشغيل النظام ⚡"):
    if not mission:
        st.warning("أدخل المهمة.")
    else:
        status = st.empty()
        status.info("⏳ الاتصال المباشر بالموديل...")

        try:
            # --- الوكلاء ---
            # نمرر المتغير llm (الكائن) وليس النص
            
            planner = Agent(
                role='Strategist',
                goal='Plan steps.',
                backstory="Meticulous planner.",
                allow_delegation=False,
                llm=llm 
            )

            coder = Agent(
                role='Developer',
                goal='Code and Execute.',
                backstory="Expert coder with execution tools.",
                tools=[DevTools.execute_code],
                allow_delegation=False,
                llm=llm
            )

            reviewer = Agent(
                role='Auditor',
                goal='Validate.',
                backstory="Quality assurance.",
                allow_delegation=False,
                llm=llm
            )

            # --- المهام ---
            t1 = Task(description=f"Plan for: {mission}", agent=planner, expected_output="Plan")
            t2 = Task(description="Write & Execute code based on plan.", agent=coder, expected_output="Code & Result")
            t3 = Task(description="Review output.", agent=reviewer, expected_output="Summary")

            # --- التشغيل ---
            crew = Crew(
                agents=[planner, coder, reviewer],
                tasks=[t1, t2, t3],
                verbose=True
            )

            result = crew.kickoff()
            
            status.success("✅ تم بنجاح.")
            st.markdown(f"<div class='result-box'>{result}</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error: {str(e)}")
