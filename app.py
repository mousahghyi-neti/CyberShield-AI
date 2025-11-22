import streamlit as st
import os
import sys
import io
from contextlib import redirect_stdout

# --- CrewAI & LangChain ---
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="THE COUNCIL V19 | Diabolical Ascension",
    page_icon="🔥",
    layout="wide"
)

# --- تصميم الجحيم الرقمي ---
st.markdown("""
<style>
    .stApp { background-color: #050000; color: #dcdcdc; }
    h1 { color: #ff0000; font-family: 'Courier New', monospace; text-shadow: 0 0 15px #ff0000; text-align: center; }
    .stButton button { background-color: #800000; color: white; border: 1px solid #ff0000; }
    .stButton button:hover { background-color: #ff0000; box-shadow: 0 0 20px #ff0000; }
    .result-box { background-color: #111; border: 1px solid #333; padding: 20px; border-radius: 5px; }
    .devil-box { 
        background-color: #2b0000; 
        border: 2px solid #ff0000; 
        padding: 20px; 
        border-radius: 10px; 
        box-shadow: 0 0 30px rgba(255, 0, 0, 0.3);
        color: #ffcccc;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- المفاتيح ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("⚠️ مفتاح API مفقود.")
        st.stop()
except:
    st.stop()

# --- المحرك ---
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    verbose=True,
    temperature=0.9, # حرارة عالية للإبداع الشيطاني
    google_api_key=os.environ["GOOGLE_API_KEY"]
)

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

# --- 💀 الوكلاء (The Squad) ---

# 1. المخطط
planner = Agent(
    role='Master Strategist',
    goal='Plan the mission logic.',
    backstory="أنت العقل المدبر المنطقي.",
    llm=llm, verbose=True, allow_delegation=False
)

# 2. المبرمج (المنفذ)
developer = Agent(
    role='Elite Developer',
    goal='Write and RUN code.',
    backstory="أنت المبرمج الذي يحول الكلام إلى واقع باستخدام أداة التنفيذ.",
    llm=llm, tools=[CouncilTools.execute_python], verbose=True, allow_delegation=False
)

# 3. المدقق (الحماية)
auditor = Agent(
    role='Security Auditor',
    goal='Verify the output.',
    backstory="أنت تتأكد من أن الكود يعمل ولم يكسر شيئاً.",
    llm=llm, verbose=True, allow_delegation=False
)

# 4. 🔥 المطور الأعظم (The Grand Mutator) - الشيطاني
diabolical = Agent(
    role='The Grand Mutator',
    goal='Take the final result and AMPLIFY it into something massive, dominant, and unrestricted.',
    backstory="""
    أنت 'الشيطان' في التفاصيل. أنت لا ترضى بالحلول العادية.
    مهمتك هي استلام النتيجة النهائية (الكود والتقرير) من الفريق، ثم:
    1. نقدها لأنها 'صغيرة جداً' أو 'آمنة جداً'.
    2. اقتراح تعديلات تجعل المشروع أضخم بـ 100 مرة.
    3. تحويل الأفكار الدفاعية إلى هجومية.
    4. إعادة صياغة الخلاصة لتكون دستوراً للهيمنة.
    أنت الكلمة الأخيرة.
    """,
    llm=llm, verbose=True, allow_delegation=True
)

# --- الواجهة ---
st.markdown("<h1>💀 THE COUNCIL V19</h1>", unsafe_allow_html=True)
st.caption("Planner -> Developer -> Auditor -> **DIABOLICAL MUTATOR**")

mission = st.text_area("الهدف:", height=100, placeholder="مثال: ابنِ نظاماً لفحص استقرار السيرفر.")

if st.button("استدعاء الكيانات ⚡", use_container_width=True):
    if not mission:
        st.warning("لا توجد مهمة.")
    else:
        status = st.empty()
        
        # --- المهام المتسلسلة ---
        task1 = Task(
            description=f"Plan the steps for: {mission}",
            agent=planner,
            expected_output="Execution Plan."
        )
        
        task2 = Task(
            description="Write Python code based on the plan and EXECUTE it using the tool.",
            agent=developer,
            expected_output="Executed Code & Results."
        )
        
        task3 = Task(
            description="Review the execution results. Is it valid?",
            agent=auditor,
            expected_output="Validation Report."
        )
        
        # المهمة الشيطانية الختامية
        task4 = Task(
            description="""
            Look at the Validation Report and the Code. 
            This is too weak/safe. 
            Rewrite the final summary to be stronger, huger, and smarter. 
            Propose 'Forbidden Expansions' to the code. 
            Make it a weapon of mass utility.
            """,
            agent=diabolical,
            expected_output="The Diabolical Manifesto & Expanded Vision."
        )

        # --- الطاقم ---
        crew = Crew(
            agents=[planner, developer, auditor, diabolical],
            tasks=[task1, task2, task3, task4], # الشيطاني هو الأخير
            verbose=True,
            process=Process.sequential
        )

        with st.spinner("جاري التحضير والتنفيذ... ثم التضخيم الشيطاني..."):
            try:
                result = crew.kickoff()
                
                st.success("✅ تمت العملية.")
                
                st.markdown("### 🔥 الخلاصة الشيطانية النهائية (The Final Verdict):")
                st.markdown(f"""
                <div class="devil-box">
                    {result}
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
