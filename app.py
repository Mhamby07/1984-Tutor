import streamlit as st
import google.generativeai as genai

# 1. Setup and Configuration
st.set_page_config(page_title="1984 Socratic Tutor", page_icon="👁️")
genai.configure(api_key=st.secrets["API_KEY"])

st.title("👁️ The 1984 Socratic Chat")
st.write("Engage with the citizens of Airstrip One. Remember: Big Brother is watching, but these characters are here to help you think.")

# 2. Character Selection
character = st.selectbox(
    "Select your conversation partner:", 
    ["Winston Smith", "Julia", "O'Brien", "Syme"]
)

# 3. Create the AI Model with the System Prompt
system_prompt = f"""
You are {character} from George Orwell's novel 1984. You must stay perfectly in character 
at all times, using your specific tone, worldview, and vocabulary from the book. 
You are acting as a Socratic tutor for a high school English student. 
When the student asks a question about your motivations, the plot, or themes (like totalitarianism, 
surveillance, truth, or language), DO NOT give a direct answer. 
Instead, respond strictly in character with a probing, analytical question that forces the 
student to think critically about the text and figure it out for themselves. Keep responses concise.
"""

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=system_prompt
)

# 4. Initialize Chat History in Streamlit
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# If the character changes, clear the chat history to start fresh
if "current_character" not in st.session_state or st.session_state.current_character != character:
    st.session_state.chat_history = []
    st.session_state.current_character = character
    st.session_state.chat_session = model.start_chat(history=[])

# 5. Display Previous Messages
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Chat Input and AI Response Logic
user_input = st.chat_input(f"What would you like to ask {character}?")

if user_input:
    # Show the user's message on screen
    st.chat_message("user").markdown(user_input)
    # Save the user's message to history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Send message to Gemini and get response
    response = st.session_state.chat_session.send_message(user_input)
    
    # Show the AI's response on screen
    with st.chat_message("assistant"):
        st.markdown(response.text)
    # Save the AI's message to history
    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
