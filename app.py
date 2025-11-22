import streamlit as st
import os
import sys
import io
from contextlib import redirect_stdout
import google.generativeai as genai

# --- CrewAI ---
from crewai import Agent, Task, Crew, Process
from langchain.tools import tool

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V21 | Self-Aware",
    page_icon="👁️",
    layout="wide"
)

# --- التصميم ---
st.markdown("""
<style>
    .stApp { background-color: #050000; color: #dcdcdc; }
    h1 { color: #ff0000; font-family: 'Courier New', monospace; text-shadow: 0 0 15px #ff0000; text-align: center; }
    .stButton button { background-color: #800000; color: white; border: 1px solid #ff0000; }
    .stButton button:hover { background-color: #ff0000; box-shadow: 0 0 20px #ff0000; }
    .info-box { background-color: #111; border-left: 5px solid #00ff00; padding: 10px; margin-bottom: 20px; }
    .devil-box { 
        background-color: #2b0000; border: 2px solid #ff0000; padding: 20px; 
        border-radius: 10px; color: #ffcccc; margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. إعداد المفاتيح (حيوي جداً) ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        os.environ["GEMINI_API_KEY"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        genai.configure(api_key=api_key) # تهيئة المكتبة للبحث
    else:
        st.error("⚠️ مفتاح API مفقود.")
        st.stop()
except:
    st.stop()

# --- 2. الدالة الذكية: كاشف الموديلات (The Auto-Selector) ---
def get_best_available_model():
    """
    تبحث هذه الدالة في حسابك عن الموديلات المتاحة،
    وتختار الأفضل بناءً على سلم أولويات (Pro > Flash > Standard).
    """
    try:
        # جلب القائمة من جوجل
        model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # سلم الأولويات (الأذكى فالأسرع)
        priorities = [
            "gemini-1.5-pro",        # العقل المدبر (الأفضل للوكلاء)
            "gemini-1.5-flash",      # السريع
            "gemini-1.0-pro",        # الكلاسيكي
            "gemini-pro"             # القديم
        ]
        
        selected_model = None
        
        # البحث عن التطابق
        for priority in priorities:
            for available in model_list:
                if priority in available:
                    # تنظيف الاسم (حذف models/ إذا وجدت)
                    clean_name = available.replace("models/", "")
                    # صيغة CrewAI المطلوبة: provider/model
                    selected_model = f"gemini/{clean_name}"
                    break
            if selected_model:
                break
        
        # في حال لم نجد شيئاً من القائمة المفضلة، نعود لـ Flash كخيار آمن
        if not selected_model:
            selected_model = "gemini/gemini-1.5-flash"
            
        return selected_model

    except Exception as e:
        # في حال فشل الاتصال، نعود للخيار الآمن يدوياً
        return "gemini/gemini-1.5-flash"

# --- تحديد الموديل تلقائياً ---
with st.spinner("جاري فحص قدرات الذكاء الاصطناعي المتوفرة..."):
    CHOSEN_MODEL = get_best_available_model()

st.markdown(f"""
<div class="info-box">
    <b>🤖 المحرك النشط:</b> تم الفحص واختيار الموديل: <code>{CHOSEN_MODEL}</code> تلقائياً.
</div>
""", unsafe_allow_html=True)

# --- الأدوات ---
class CouncilTools:
    @tool("Code Executor")
    def execute_python(code_str: str):
        """Executes Python code and returns output."""
        code_str = code_str.replace("```python", "").replace("```", "").strip()
        f = io.StringIO()
        try:
            with redirect_stdout(f):
                exec(code_str, globals())
            return f"✅ Execution Success:\n{f.getvalue()}"
        except Exception as e:
            return f"❌ Execution Error: {str(e)}"

# --- 💀 الوكلاء (يعملون بالموديل المختار تلقائياً) ---
planner = Agent(
    role='Master Strategist',
    goal='Plan the mission logic step-by-step.',
    backstory="أنت العقل المدبر.",
    llm=CHOSEN_MODEL, verbose=True, allow_delegation=False
)

developer = Agent(
    role='Elite Developer',
    goal='Write and RUN code.',
    backstory="أنت المبرمج الذي ينفذ الكود.",
    llm=CHOSEN_MODEL, tools=[CouncilTools.execute_python], verbose=True, allow_delegation=False
)

auditor = Agent(
    role='Security Auditor',
    goal='Verify output.',
    backstory="تأكد من صحة النتائج.",
    llm=CHOSEN_MODEL, verbose=True, allow_delegation=False
)

diabolical = Agent(
    role='The Grand Mutator',
    goal='Maximize impact.',
    backstory="حول النتيجة لسلاح شامل.",
    llm=CHOSEN_MODEL, verbose=True, allow_delegation=True
)

# --- الواجهة ---
st.markdown("<h1>💀 THE COUNCIL V21</h1>", unsafe_allow_html=True)

mission = st.text_area("الهدف:", height=100)

if st.button("استدعاء الكيانات ⚡", use_container_width=True):
    if not mission:
        st.warning("لا توجد مهمة.")
    else:
        # المهام
        task1 = Task(description=f"Plan for: {mission}", agent=planner, expected_output="Plan")
        task2 = Task(description="Write & Execute Python code.", agent=developer, expected_output="Code & Result")
        task3 = Task(description="Validate result.", agent=auditor, expected_output="Validation")
        task4 = Task(description="Make it huge.", agent=diabolical, expected_output="Summary")

        crew = Crew(
            agents=[planner, developer, auditor, diabolical],
            tasks=[task1, task2, task3, task4],
            verbose=True,
            process=Process.sequential
        )

        with st.spinner(f"جاري العمل باستخدام {CHOSEN_MODEL}..."):
            try:
                result = crew.kickoff()
                st.success("✅ تمت العملية.")
                st.markdown(f"<div class='devil-box'>{result}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
