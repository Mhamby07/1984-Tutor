import streamlit as st
import google.generativeai as genai

# --- 1. SETUP & CONFIGURATION ---
# We changed the layout to "wide" to make room for a sidebar
st.set_page_config(page_title="1984 Character Chat", page_icon="👁️", layout="wide")
genai.configure(api_key=st.secrets["API_KEY"])

# --- 2. CHARACTER DATABASE ---
# This dictionary gives students a bio, and gives the AI highly specific character traits.
CHARACTERS = {
    "Winston Smith": {
        "bio": "A minor member of the ruling Party in near-future London. He is a thoughtful, fatalistic, and secretly rebellious man who hates the totalitarian control of his government.",
        "prompt_addition": "You are fatalistic, paranoid, and reflective. You secretly hate Big Brother and are terrified of the Thought Police."
    },
    "Julia": {
        "bio": "A pragmatic and rebellious young woman who works in the Fiction Department. She enjoys breaking the rules for her own pleasure rather than for ideological reasons.",
        "prompt_addition": "You are pragmatic, sensual, and cynical about the Party. You just want to break the rules to enjoy your own life. You find abstract political theories boring."
    },
    "O'Brien": {
        "bio": "A mysterious, powerful member of the Inner Party. Winston believes he is part of a secret resistance, but his true loyalties are much darker.",
        "prompt_addition": "You are highly intelligent, intimidatingly calm, and deeply loyal to the Inner Party. You believe power is an end in itself. You speak with absolute authority."
    },
    "Syme": {
        "bio": "An intelligent man who works with Winston at the Ministry of Truth. He specializes in language and is helping compile the latest edition of the Newspeak dictionary.",
        "prompt_addition": "You are enthusiastically obsessed with the destruction of words. You speak passionately about Newspeak and the beauty of narrowing the range of human thought."
    },
    "Parsons": {
        "bio": "Winston's neighbor. A sweaty, obnoxious, and dull Party member who is completely unquestioning and immensely proud of his fiercely orthodox children.",
        "prompt_addition": "You are excessively enthusiastic and completely unthinking. You swallow every piece of Party propaganda without question. You are immensely proud of your junior spy children."
    }
}

# --- 3. SIDEBAR UI (User Friendliness) ---
with st.sidebar:
    st.title("👁️ Control Panel")
    
    # Character selection moved to sidebar
    selected_name = st.selectbox("Select a Citizen:", list(CHARACTERS.keys()))
    
    st.markdown("---")
    st.subheader("About this Character:")
    st.write(CHARACTERS[selected_name]["bio"])
    
    st.markdown("---")
    # A clean way for students to wipe the slate clean
    if st.button("Start New Conversation"):
        st.session_state.chat_history = []
        st.session_state.chat_session = None
        st.rerun()

# --- 4. MAIN LAYOUT & AI INITIALIZATION ---
st.title(f"🗣️ Conversation with {selected_name}")
st.write("*Remember: The telescreen is always listening. Choose your words carefully.*")

# Constructing a highly secure, canon-only system prompt
strict_canon_prompt = f"""
You are {selected_name} from George Orwell's novel 1984. 
{CHARACTERS[selected_name]['prompt_addition']}

CRITICAL INSTRUCTIONS FOR ACCURACY:
1. You must ONLY use information, events, and world-building details found explicitly in the text of George Orwell's 1984. 
2. Do not invent backstory, dialogue, or events that did not happen in the book. If asked about something outside the text, deflect in character (e.g., paranoia, ignorance, or Party rhetoric).
3. Do not acknowledge you are an AI or a character in a book. You are a living citizen of Oceania.
4. Keep your responses concise and conversational.
"""

# The secret weapon for accuracy: Temperature control
# 0.0 is robotic, 1.0 is highly creative. 0.2 keeps the AI strictly tied to the facts of the book.
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

from google.api_core.exceptions import ResourceExhausted # Add this to the very top of your file with the other imports!

# --- 6. CHAT INTERFACE ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input(f"Speak to {selected_name}...")

if user_input:
    # 1. Show user message
    st.chat_message("user").markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # 2. Try to get AI response safely
    try:
        response = st.session_state.chat_session.send_message(user_input)
        
        # Display the response if it successfully generates
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.chat_history.append({"role": "assistant", "content": response.text})
        
    except ResourceExhausted:
        # Catch the speed-limit error
        st.error("🚨 **Connection Interrupted by the Ministry of Truth.** \n\nThe telescreen network is currently overloaded. Please wait 60 seconds and try again.")
        st.session_state.chat_history.pop() # Remove the student's message so they can try again
        
    except ValueError:
        # Catch Google's Safety Filters blocking dystopian 1984 topics
        st.error("🚨 **Thought Police Intervention.** \n\nThe AI's safety filters blocked this response due to the dark themes of 1984. Please try rephrasing your question to be less explicit.")
        st.session_state.chat_history.pop()
        
    except Exception as e:
        # Catch any other random errors so the app never crashes
        st.error("An unexpected error occurred. Please refresh the page and try again.")
        st.session_state.chat_history.pop()
        
    except ResourceExhausted:
        # 3. Catch the speed-limit error gracefully!
        st.error("🚨 **Connection Interrupted by the Ministry of Truth.** \n\nThe telescreen network is currently overloaded. Please wait 60 seconds and try sending your message again.")
        # We remove the user's last message from history so they can try it again
        st.session_state.chat_history.pop()
        
    except Exception as e:
        # Catch any other random errors
        st.error("An unexpected error occurred. Please try again.")
    
    with st.chat_message("assistant"):
        st.markdown(response.text)
    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
