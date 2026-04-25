import streamlit as st
import google.generativeai as genai
import PyPDF2

# --- Page Configuration ---
st.set_page_config(page_title="AI Lesson Planner", page_icon="📚", layout="centered")

# --- Session State Management ---
if "lesson_plan" not in st.session_state:
    st.session_state.lesson_plan = None

# --- API Key Setup ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except KeyError:
    st.warning("API Key not found in Streamlit Secrets!")

# --- Helper Functions ---
def extract_text_from_pdf(uploaded_file):
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text

# --- Build the User Interface ---
st.title("📚 AI University Lesson Plan Generator")

# Course Context Inputs (New)
col_course1, col_course2 = st.columns(2)
with col_course1:
    course_name = st.text_input("Course Name (Optional)", placeholder="e.g., Intro to Microeconomics")
with col_course2:
    course_code = st.text_input("Course Code (Optional)", placeholder="e.g., ECON 101")

# Time & Scheduling Inputs
col1, col2, col3 = st.columns(3)
with col1:
    week = st.selectbox("Week", range(1, 17))
with col2:
    day = st.selectbox("Day", range(1, 6))
with col3:
    length = st.number_input("Class Length (mins)", min_value=10, max_value=300, value=90)

objective = st.text_input("Lesson Objective", placeholder="e.g., Students will be able to analyze supply and demand curves.")

uploaded_file = st.file_uploader("Upload PDF Materials (Optional)", type="pdf")
material_url = st.text_input("External Link/URL (Optional)")

st.subheader("Activities to Include")
act_col1, act_col2, act_col3, act_col4, act_col5 = st.columns(5)
lecture = act_col1.checkbox("Lecture", value=True)
individual = act_col2.checkbox("Individual activity")
group = act_col3.checkbox("Group activity")
skills = act_col4.checkbox("Skills Check")
assessment = act_col5.checkbox("Assessment")

# --- App Logic & AI Generation ---
if st.button("Generate Lesson Plan", type="primary"):
    selected_activities = [act for act, selected in zip(
        ["Lecture", "Individual activity", "Group activity", "Skills Check", "Assessment"], 
        [lecture, individual, group, skills, assessment]) if selected]

    if not selected_activities:
        st.error("Please select at least one activity type.")
    elif not objective:
        st.error("Please provide a lesson objective.")
    else:
        with st.spinner("Analyzing materials and writing plan (this takes ~10 seconds)..."):
            
            pdf_context = ""
            if uploaded_file is not None:
                pdf_context = extract_text_from_pdf(uploaded_file)
                if len(pdf_context) > 20000: 
                    pdf_context = pdf_context[:20000] + "... [Text Truncated]"

            # Format course info string if provided
            course_context = ""
            if course_name or course_code:
                course_context = f"- Course: {course_name} {course_code}\n"

            # 1. Generate the Lesson Plan text
            plan_prompt = f"""
            You are an expert university professor. Create a lesson plan:
            {course_context}- Timeline: Week {week}, Day {day}
            - Total Length: {length} minutes
            - Objective: {objective}
            - Required Activities: {', '.join(selected_activities)}
            Context: {pdf_context}
            Format clearly with Markdown. Include a chronological schedule.
            """
            
            plan_response = model.generate_content(plan_prompt)
            st.session_state.lesson_plan = plan_response.text

# --- Display Results & Downloads ---
if st.session_state.lesson_plan:
    st.markdown("---")
    st.success("Generation Complete!")
    
    st.download_button(
        label="📄 Download Plan (.md)",
        data=st.session_state.lesson_plan,
        file_name=f"Lesson_Plan_Week_{week}.md",
        mime="text/markdown"
    )
    st.caption("Hint: For a clean PDF, right-click this page and select **Print -> Save as PDF**.")
            
    st.markdown("---")
    st.markdown(st.session_state.lesson_plan)
    
    st.markdown("---")
    # Reset Button (New)
    if st.button("🔄 Reset / Start Over"):
        st.session_state.lesson_plan = None
        st.rerun()
