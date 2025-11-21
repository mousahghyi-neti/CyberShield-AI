import streamlit as st
import google.generativeai as genai
import time

# --- إعداد القاعة (Page Config) ---
st.set_page_config(page_title="The Council | المجلس", page_icon="🏛️", layout="wide")

# --- تصميم الفخامة (Dark Mafia/Luxury Style) ---
st.markdown("""
<style>
    .main {background-color: #050505; color: #e0e0e0;}
    h1 {color: #d4af37; font-family: 'Times New Roman'; text-align: center; letter-spacing: 2px;}
    .advisor-card {
        background-color: #1a1a1a; 
        border: 1px solid #333; 
        border-left: 4px solid #d4af37;
        padding: 20px; 
        margin-bottom: 15px; 
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .advisor-name {color: #d4af37; font-size: 18px; font-weight: bold; margin-bottom: 10px; font-family: serif;}
    .advisor-role {color: #888; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;}
    .stTextArea textarea {background-color: #111; color: white; border: 1px solid #333;}
    .stButton button {
        width: 100%; 
        background-color: #d4af37; 
        color: black; 
        font-weight: bold; 
        border: none; 
        padding: 10px;
        text-transform: uppercase;
    }
    .stButton button:hover {background-color: #b59326;}
    .error-box {color: #ff4b4b; font-size: 12px;}
</style>
""", unsafe_allow_html=True)

# --- العنوان ---
st.title("🏛️ THE COUNCIL")
st.markdown("<p style='text-align: center; color: gray; font-style: italic;'>حيث تجتمع العقول العظمى لاتخاذ قراراتك المصيرية</p>", unsafe_allow_html=True)
st.divider()

# --- الاتصال بالمحرك ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ مفتاح الدخول للقاعة مفقود (API Key).")
    st.stop()

genai.configure(api_key=api_key)

# --- الدالة الذكية لاختيار الموديل (The Smart Selector) ---
# هذه الدالة هي "العقل المدبر" لتجنب الأخطاء السابقة
def get_response(prompt_text):
    # القائمة الذهبية: نبدأ بالأقوى (الذي عمل معك سابقاً) ثم الاحتياطي
    models_priority = ['gemini-2.5-flash', 'gemini-pro']
    
    last_error = None
    for model_name in models_priority:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt_text)
            return response.text # نجحنا! نخرج من الدالة فوراً
        except Exception as e:
            last_error = e
            continue # فشل هذا الموديل، نجرب التالي بصمت
            
    # إذا فشلت كل الموديلات، نرفع الراية الحمراء
    raise last_error

# --- المدخلات ---
col1, col2 = st.columns([2, 1])
with col1:
    problem = st.text_area("اطرح المعضلة أو القرار الذي تريد اتخاذه:", height=150, placeholder="مثال: هل يجب أن أترك وظيفتي وأبدأ مشروعي الخاص بميزانية محدودة؟")

with col2:
    st.markdown("### 👥 الأعضاء الحاضرون:")
    st.markdown("✅ **Steve Jobs** (الابتكار)")
    st.markdown("✅ **Machiavelli** (الدهاء)")
    st.markdown("✅ **Jordan Belfort** (المال)")
    st.markdown("🛡️ **Hammad Hijazi** (الأمن والحكمة)")

# --- زر الاستدعاء ---
if st.button("استدعاء المجلس (Call The Council)"):
    if not problem:
        st.warning("القاعة صامتة.. اطرح موضوعاً للنقاش.")
    else:
        results_container = st.container()
        
        advisors = [
            {"name": "Steve Jobs", "role": "VISIONARY & DESIGN", "style": "مباشر، قاسٍ، يركز على المنتج والتميز، يكره الحلول الوسط.", "icon": "🍎"},
            {"name": "Niccolò Machiavelli", "role": "POWER & STRATEGY", "style": "ماكر، واقعي جداً، يركز على السيطرة والمصلحة، الغاية تبرر الوسيلة.", "icon": "🦊"},
            {"name": "Jordan Belfort", "role": "SALES & MONEY", "style": "حماسي، جشع، يركز على الربح السريع وكيفية بيع الفكرة لأي شخص.", "icon": "💸"},
            {"name": "Hammad Hijazi", "role": "CHAIRMAN & SECURITY", "style": "حكيم، خبير أمني، يوزن المخاطر، ويعطي القرار النهائي المتزن الذي يحميك.", "icon": "🛡️"}
        ]

        with st.spinner('جاري التشاور بين الأعضاء...'):
            for advisor in advisors:
                prompt = f"""
                تقمص شخصية: {advisor['name']}.
                السياق: أنت في مجلس إدارة سري.
                سؤال المستخدم: "{problem}"
                
                مهمتك:
                1. أعط رأياً يعكس فلسفتك ({advisor['style']}) بدقة تامة.
                2. كن حازماً ومختصراً (لا تتجاوز 4 أسطر).
                3. تحدث بالعربية بأسلوبك الخاص.
                """
                
                try:
                    # استخدام الدالة الذكية بدلاً من الاتصال المباشر
                    reply = get_response(prompt)
                    
                    time.sleep(0.3) 
                    with results_container:
                        st.markdown(f"""
                        <div class="advisor-card">
                            <div class="advisor-role">{advisor['icon']} {advisor['role']}</div>
                            <div class="advisor-name">{advisor['name']}</div>
                            <div style="color: #ccc; line-height: 1.6;">{reply}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"عذراً، {advisor['name']} غير متاح حالياً. (السبب: {e})")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #333;'>The Council System v2.0 (Self-Healing Core)</p>", unsafe_allow_html=True)
