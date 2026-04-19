import streamlit as st
import google.generativeai as genai
import PyPDF2

# --- Page Configuration ---
st.set_page_config(page_title="AI Lesson Planner", page_icon="📚", layout="centered")

# --- API Key Setup ---
# Streamlit securely stores API keys in a "secrets" dictionary.
# We will set this up in the Streamlit Cloud dashboard later.
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash') # Using the standard text model
except KeyError:
    st.warning("API Key not found. We will configure this in Streamlit later!")

# --- Helper Function to Extract Text from PDF ---
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
st.write("Fill out the details below, and the AI will generate a structured, timed lesson plan.")

# Time & Scheduling Inputs
col1, col2, col3 = st.columns(3)
with col1:
    week = st.selectbox("Week", range(1, 17))
with col2:
    day = st.selectbox("Day", range(1, 6))
with col3:
    length = st.number_input("Class Length (minutes)", min_value=10, max_value=300, value=90)

# Objective Input
objective = st.text_input("Lesson Objective", placeholder="e.g., Students will be able to analyze supply and demand curves.")

# Materials Inputs
st.subheader("Lesson Materials Context")
st.write("Upload a syllabus or reading material so the AI understands the context.")
uploaded_file = st.file_uploader("Upload PDF (Optional)", type="pdf")
material_url = st.text_input("External Link/URL (Optional)")

# Activity Checkboxes
st.subheader("Activities to Include")
act_col1, act_col2, act_col3, act_col4, act_col5 = st.columns(5)
lecture = act_col1.checkbox("Lecture", value=True)
individual = act_col2.checkbox("Individual activity")
group = act_col3.checkbox("Group activity")
skills = act_col4.checkbox("Skills Check")
assessment = act_col5.checkbox("Assessment")

# --- App Logic & AI Generation ---
if st.button("Generate AI Lesson Plan", type="primary"):
    
    # Gather selected activities into a list
    selected_activities = []
    if lecture: selected_activities.append("Lecture")
    if individual: selected_activities.append("Individual activity")
    if group: selected_activities.append("Group activity")
    if skills: selected_activities.append("Skills Check")
    if assessment: selected_activities.append("Assessment")

    # Basic Validation
    if not selected_activities:
        st.error("Please select at least one activity type.")
    elif not objective:
        st.error("Please provide a lesson objective.")
    else:
        with st.spinner("Analyzing materials and generating your lesson plan..."):
            
            # 1. Process the PDF text if one was uploaded
            pdf_context = ""
            if uploaded_file is not None:
                pdf_context = extract_text_from_pdf(uploaded_file)
                # Truncate text if it's massively long to save processing time
                if len(pdf_context) > 20000: 
                    pdf_context = pdf_context[:20000] + "... [Text Truncated]"

            # 2. Build the AI Prompt
            prompt = f"""
            You are an expert university professor and instructional designer. 
            Create a highly structured lesson plan based on the following parameters:
            
            - Timeline: Week {week}, Day {day}
            - Total Class Length: {length} minutes
            - Objective: {objective}
            - External Resource URL: {material_url if material_url else 'None provided'}
            - Required Activity Types: {', '.join(selected_activities)}
            
            Context from uploaded course materials (use this to inform the content):
            {pdf_context if pdf_context else 'No PDF materials provided.'}
            
            Format the response clearly with Markdown. Include:
            1. A brief overview of the lesson.
            2. A chronological schedule broken down by minutes (e.g., [0:00-0:15] Lecture: Intro to Topic). Ensure the total time adds up exactly to {length} minutes.
            3. Specific talking points, discussion questions, or activity instructions based on the objective and materials.
            """

            # 3. Call the AI API
            try:
                response = model.generate_content(prompt)
                
                # 4. Display the results
                st.success("Lesson Plan Generated!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"An error occurred while contacting the AI: {e}")
                st.info("Did you remember to set your GEMINI_API_KEY in the Streamlit Secrets?")
