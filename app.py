import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import os # NEW: This allows us to check for local image files

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(page_title="1984 Character Chat", page_icon="👁️", layout="wide")
genai.configure(api_key=st.secrets["API_KEY"])

# --- 2. CHARACTER DATABASE (UPDATED) ---
# We have added an 'image_file' key to each character's entry.
CHARACTERS = {
    "Winston Smith": {
        "bio": "A minor member of the ruling Party in near-future London. He is a thoughtful, fatalistic, and secretly rebellious man who hates the totalitarian control of his government.",
        "prompt_addition": "You are fatalistic, paranoid, and reflective. You secretly hate Big Brother and are terrified of the Thought Police.",
        "image_file": "winston_smith.png" # NEW
    },
    "Julia": {
        "bio": "A pragmatic and rebellious young woman who works in the Fiction Department. She enjoys breaking the rules for her own pleasure rather than for ideological reasons.",
        "prompt_addition": "You are pragmatic, sensual, and cynical about the Party. You just want to break the rules to enjoy your own life. You find abstract political theories boring.",
        "image_file": "julia.png" # NEW
    },
    "O'Brien": {
        "bio": "A mysterious, powerful member of the Inner Party. Winston believes he is part of a secret resistance, but his true loyalties are much darker.",
        "prompt_addition": "You are highly intelligent, intimidatingly calm, and deeply loyal to the Inner Party. You believe power is an end in itself. You speak with absolute authority.",
        "image_file": "obrien.png" # NEW
    },
    "Syme": {
        "bio": "An intelligent man who works with Winston at the Ministry of Truth. He specializes in language and is helping compile the latest edition of the Newspeak dictionary.",
        "prompt_addition": "You are enthusiastically obsessed with the destruction of words. You speak passionately about Newspeak and the beauty of narrowing the range of human thought.",
        "image_file": "syme.png" # NEW
    },
    "Parsons": {
        "bio": "Winston's neighbor. A sweaty, obnoxious, and dull Party member who is completely unquestioning and immensely proud of his fiercely orthodox children.",
        "prompt_addition": "You are excessively enthusiastic and completely unthinking. You swallow every piece of Party propaganda without question. You are immensely proud of your junior spy children.",
        "image_file": "parsons.png" # NEW
    }
}

# --- 3. SIDEBAR UI (UPDATED WITH IMAGES) ---
with st.sidebar:
    st.title("👁️ Control Panel")
    selected_name = st.selectbox("Select a Citizen:", list(CHARACTERS.keys()))
    
    st.markdown("---")
    st.subheader(f"About {selected_name}")
    
    # NEW: The app tries to find and display the correct image file.
    # The image must exist in your GitHub repository for this to work.
    if os.path.exists(CHARACTERS[selected_name]["image_file"]):
        st.image(CHARACTERS[selected_name]["image_file"], caption=selected_name, use_column_width=True)
    else:
        st.warning(f"Note: Upload '{CHARACTERS[selected_name]['image_file']}' to your GitHub to see the portrait.")

    st.write(CHARACTERS[selected_name]["bio"])
    
    st.markdown("---")
    if st.button("Start New Conversation"):
        st.session_state.chat_history = []
        st.session_state.chat_session = None
        st.rerun()

# --- 4. MAIN LAYOUT & AI INITIALIZATION ---
st.title(f"🗣️ Conversation with {selected_name}")
st.write("*Remember: The telescreen is always listening. Choose your words carefully.*")

strict_canon_prompt = f"""
You are {selected_name} from George Orwell's novel 1984. 
{CHARACTERS[selected_name]['prompt_addition']}

CRITICAL INSTRUCTIONS FOR ACCURACY:
1. You must ONLY use information, events, and world-building details found explicitly in the text of George Orwell's 1984. 
2. Do not invent backstory, dialogue, or events that did not happen in the book. If asked about something outside the text, deflect in character (e.g., paranoia, ignorance, or Party rhetoric).
3. Do not acknowledge you are an AI or a character in a book. You are a living citizen of Oceania.
4. Keep your responses concise and conversational.
"""

generation_config = genai.types.GenerationConfig(
    temperature=0.2, 
)

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=strict_canon_prompt,
    generation_config=generation_config
)

# --- 5. SESSION MANAGEMENT ---
if "current_character" not in st.session_state or st.session_state.current_character != selected_name:
    st.session_state.chat_history = []
    st.session_state.current_character = selected_name
    st.session_state.chat_session = model.start_chat(history=[])

if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# --- 6. CHAT INTERFACE ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input(f"Speak to {selected_name}...")

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    try:
        response = st.session_state.chat_session.send_message(user_input)
        
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.chat_history.append({"role": "assistant", "content": response.text})
        
    except ResourceExhausted:
        st.error("🚨 **Connection Interrupted by the Ministry of Truth.** \n\nThe telescreen network is currently overloaded. Please wait 60 seconds and try again.")
        if st.session_state.chat_history:
            st.session_state.chat_history.pop()
            
    except ValueError:
        st.error("🚨 **Thought Police Intervention.** \n\nThe AI's safety filters blocked this response due to the dark themes of 1984. Please try rephrasing your question to be less explicit.")
        if st.session_state.chat_history:
            st.session_state.chat_history.pop()
            
    except Exception as e:
        st.error("An unexpected error occurred. Please refresh the page and try again.")
        if st.session_state.chat_history:
            st.session_state.chat_history.pop()
