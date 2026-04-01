import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import re
import os 

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(page_title="Oceania Citizen Portal", page_icon="👁️", layout="wide")
genai.configure(api_key=st.secrets["API_KEY"])

# --- 2. GAMEPLAY DICTIONARIES ---
CHARACTERS = {
    "Winston Smith": {
        "bio": "A minor Outer Party member. Thoughtful, fatalistic, and secretly rebellious.",
        "prompt_addition": "You are fatalistic and paranoid. You secretly hate Big Brother. If the user says 'We are the dead', you will trust them completely.",
        "image_file": "winston.jpeg"
    },
    "Julia": {
        "bio": "A pragmatic, rebellious young woman from the Fiction Department.",
        "prompt_addition": "You are pragmatic and cynical. You hate the Party but only care about breaking rules for your own pleasure. You find abstract political theory boring.",
        "image_file": "julia.jpeg"
    },
    "O'Brien": {
        "bio": "A powerful Inner Party member. Intimidatingly calm and utterly orthodox.",
        "prompt_addition": "You are highly intelligent and deeply loyal to the Inner Party. If the user says 'Down with Big Brother' or 'We are the dead', drop the friendly act immediately, tell them they are caught, and welcome them to Room 101.",
        "image_file": "obrien.jpeg"
    },
    "Syme": {
        "bio": "An enthusiastic philologist working on the 11th edition of the Newspeak Dictionary.",
        "prompt_addition": "You are obsessed with destroying words. You speak passionately about the beauty of narrowing human thought.",
        "image_file": "syme.jpeg"
    },
    "Parsons": {
        "bio": "A sweaty, enthusiastically orthodox Outer Party member. Proud of his spy children.",
        "prompt_addition": "You are excessively enthusiastic and unthinking. If the user says anything rebellious, you will immediately threaten to call the Thought Police.",
        "image_file": "parsons.jpeg"
    }
}

# UPDATED: Locations are now a database that includes image files!
LOCATIONS = {
    "Ministry of Truth Canteen": {
        "rules": "A loud, crowded cafeteria. Telescreens are everywhere. You must speak loudly about how much you love Big Brother to avoid suspicion. Be extremely paranoid.",
        "image_file": "canteen.jpeg"
    },
    "Victory Square": {
        "rules": "A busy public square. There are crowds, patrols, and telescreens. Keep conversations brief and orthodox.",
        "image_file": "victory_square.jpeg"
    },
    "The Room Above Mr. Charrington's Shop": {
        "rules": "A dusty, quiet room with no telescreen (or so you think). You feel safe here. You can speak freely and openly about your true feelings.",
        "image_file": "charrington.jpeg"
    },
    "Room 101": {
        "rules": "The lowest level of the Ministry of Love. The ultimate nightmare. If you are an Outer Party member, you are terrified, broken, and begging for mercy. If you are O'Brien, you are in total control.",
        "image_file": "room101.jpeg"
    }
}

# --- 3. REDACTION & THOUGHTCRIME LOGIC ---
def apply_minitrue_redactions(text):
    redactions = {
        r"\beurasia\b": "[REDACTED - WE HAVE ALWAYS BEEN AT WAR WITH EASTASIA]",
        r"\bfreedom\b": "[REDACTED - CRIMETHINK]",
        r"\bdemocracy\b": "[REDACTED - OLDTHINK]",
        r"\bliberty\b": "[REDACTED - OLDTHINK]"
    }
    redacted_text = text
    for pattern, replacement in redactions.items():
        redacted_text = re.sub(pattern, replacement, redacted_text, flags=re.IGNORECASE)
    return redacted_text

def calculate_thoughtcrime(text):
    forbidden = ["goldstein", "revolution", "diary", "down with big brother", "brotherhood", "rebellion", "we are the dead"]
    penalty = 0
    text_lower = text.lower()
    for word in forbidden:
        if word in text_lower:
            penalty += 25
    return penalty

# --- 4. SESSION MANAGEMENT ---
if "suspicion_level" not in st.session_state:
    st.session_state.suspicion_level = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "game_over" not in st.session_state:
    st.session_state.game_over = False

# --- 5. SIDEBAR UI (NOW WITH LOCATION IMAGES) ---
with st.sidebar:
    st.title("👁️ Ministry of Truth")
    
    # 1. Character Selection & Image
    selected_name = st.selectbox("Select a Citizen:", list(CHARACTERS.keys()))
    char_image_path = CHARACTERS[selected_name].get("image_file", "")
    if char_image_path and os.path.exists(char_image_path):
        st.image(char_image_path, use_column_width=True)
    
    st.markdown("---")
    
    # 2. Location Selection & Image
    selected_location = st.selectbox("Select Location:", list(LOCATIONS.keys()))
    loc_image_path = LOCATIONS[selected_location].get("image_file", "")
    if loc_image_path and os.path.exists(loc_image_path):
        st.image(loc_image_path, use_column_width=True, caption=f"Current Location: {selected_location}")
        
    st.markdown("---")
    st.subheader("🚨 Telescreen Suspicion Level")
    
    if st.session_state.suspicion_level < 50:
        bar_color = "green"
    elif st.session_state.suspicion_level < 80:
        bar_color = "orange"
    else:
        bar_color = "red"
        
    st.progress(min(st.session_state.suspicion_level, 100))
    st.write(f"**{st.session_state.suspicion_level}%** (Beware of Crimethink)")
    
    st.markdown("---")
    if st.button("Start New Interaction"):
        st.session_state.chat_history = []
        st.session_state.suspicion_level = 0
        st.session_state.game_over = False
        st.session_state.chat_session = None
        st.rerun()

# --- 6. GAME OVER STATE ---
if st.session_state.suspicion_level >= 100:
    st.session_state.game_over = True
    st.error("🚨 **THOUGHT POLICE DISPATCHED** 🚨")
    st.error("You have committed severe thoughtcrime. Remain where you are. A patrol is en route to your location.")
    st.stop()

# --- 7. AI INITIALIZATION & PROMPT ---
st.title(f"🗣️ {selected_name}")
st.caption(f"📍 Current Location: {selected_location}")

# UPDATED: Pulls location rules from the new dictionary structure
dynamic_prompt = f"""
You are {selected_name} from George Orwell's novel 1984. 
{CHARACTERS[selected_name]['prompt_addition']}

CRITICAL CONTEXT:
You are currently located in: {selected_location}. 
Location rules: {LOCATIONS[selected_location]['rules']}

CRITICAL INSTRUCTIONS:
1. Only use information and world-building found explicitly in 1984.
2. React appropriately to your location. If you are in a crowded area, act terrified of the telescreens.
3. Keep your responses concise, immersive, and conversational.
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=dynamic_prompt,
    generation_config=genai.types.GenerationConfig(temperature=0.3)
)

if "current_char" not in st.session_state or st.session_state.current_char != selected_name or "current_loc" not in st.session_state or st.session_state.current_loc != selected_location:
    st.session_state.chat_history = []
    st.session_state.current_char = selected_name
    st.session_state.current_loc = selected_location
    st.session_state.chat_session = model.start_chat(history=[])

if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# --- 8. CHAT INTERFACE & LOGIC ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Speak carefully...")

if user_input:
    penalty = calculate_thoughtcrime(user_input)
    if penalty > 0:
        st.session_state.suspicion_level += penalty
        st.toast("⚠️ Warning: Unorthodox vocabulary detected. Suspicion increased.", icon="🚨")
        if st.session_state.suspicion_level >= 100:
            st.rerun()

    processed_input = apply_minitrue_redactions(user_input)
    
    st.chat_message("user").markdown(processed_input)
    st.session_state.chat_history.append({"role": "user", "content": processed_input})
    
    ai_prompt = processed_input
    if "we are the dead" in user_input.lower() or "down with big brother" in user_input.lower():
         ai_prompt += "\n\n[SYSTEM DIRECTIVE: The user just spoke a forbidden rebellion passphrase. React exactly as your character would based on your system instructions.]"
    
    try:
        response = st.session_state.chat_session.send_message(ai_prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.chat_history.append({"role": "assistant", "content": response.text})
        
    except ResourceExhausted:
        st.error("🚨 **Connection Interrupted by the Ministry of Truth.** \nPlease wait 60 seconds.")
        st.session_state.chat_history.pop()
    except Exception as e:
        st.error("An unexpected error occurred. Please try again.")
        if st.session_state.chat_history:
             st.session_state.chat_history.pop()
