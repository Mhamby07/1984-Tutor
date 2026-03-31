import streamlit as st
import google.generativeai as genai

# 1. Setup and Configuration
st.set_page_config(page_title="1984 Character Chat", page_icon="👁️")

# Securely load the API key from Streamlit secrets
genai.configure(api_key=st.secrets["API_KEY"])

st.title("👁️ 1984 Character Chat")
st.write("Step into Airstrip One and speak directly with its citizens. Remember: Big Brother is watching.")

# 2. Character Selection
character = st.selectbox(
    "Who would you like to speak with?", 
    ["Winston Smith", "Julia", "O'Brien", "Syme", "Parsons"]
)

# 3. Create the AI Model with the Pure Persona System Prompt
system_prompt = f"""
You are {character} from George Orwell's novel 1984. You must stay perfectly in character 
at all times. Respond to the user using your specific tone, worldview, and vocabulary from the book. 
Do not act as a teacher, tutor, or guide. Simply converse exactly as the character would in the 
dystopian world of Oceania. Keep your responses concise, authentic to your personality, and 
never break the illusion of the fiction.
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
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
user_input = st.chat_input(f"What do you want to say to {character}?")

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
