import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import re

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(page_title="Oceania Citizen Portal", page_icon="👁️", layout="wide")
genai.configure(api_key=st.secrets["API_KEY"])

# --- 2. GAMEPLAY DICTIONARIES ---
CHARACTERS = {
    "Winston Smith": {
        "bio": "A minor Outer Party member. Thoughtful, fatalistic, and secretly rebellious.",
        "prompt_addition": "You are fatalistic and paranoid. You secretly hate Big Brother. If the user says 'We are the dead', you will trust them completely."
    },
    "Julia": {
        "bio": "A pragmatic, rebellious young woman from the Fiction Department.",
        "prompt_addition": "You are pragmatic and cynical. You hate the Party but only care about breaking rules for your own pleasure. You find abstract political theory boring."
    },
    "O'Brien": {
        "bio": "A powerful Inner Party member. Intimidatingly calm and utterly orthodox.",
        "prompt_addition": "You are highly intelligent and deeply loyal to the Inner Party. If the user says 'Down with Big Brother' or 'We are the dead', drop the friendly act immediately, tell them they are caught, and welcome them to Room 101."
    },
    "Syme": {
        "bio": "An enthusiastic philologist working on the 11th edition of the Newspeak Dictionary.",
        "prompt_addition": "You are obsessed with destroying words. You speak passionately about the beauty of narrowing human thought."
    },
    "Parsons": {
        "bio": "A sweaty, enthusiastically orthodox Outer Party member. Proud of his spy children.",
        "prompt_addition": "You are excessively enthusiastic and unthinking. If the user says anything rebellious, you will immediately threaten to call the Thought Police."
    }
}

LOCATIONS = {
    "Ministry of Truth Canteen": "A loud, crowded cafeteria. Telescreens are everywhere. You must speak loudly about how much you love Big Brother to avoid suspicion. Be extremely paranoid.",
    "Victory Square": "A busy public square. There are crowds, patrols, and telescreens. Keep conversations brief and orthodox.",
    "The Room Above Mr. Charrington's Shop": "A dusty, quiet room with no telescreen (or so you think). You feel safe here. You can speak freely and openly about your true feelings.",
    "Room 101": "The lowest level of the Ministry of Love. The ultimate nightmare. If you are an Outer Party member, you are terrified, broken, and begging for mercy. If you are O'Brien, you are in total control."
}

# --- 3. REDACTION & THOUGHTCRIME LOGIC ---
def apply_minitrue_redactions(text):
    """Automatically censors user input before the AI sees it."""
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
    """Checks for forbidden words and returns a penalty score."""
    forbidden = ["goldstein", "revolution", "diary", "down with big brother", "brotherhood", "rebellion", "we are the dead"]
    penalty = 0
    text_lower = text.lower()
    for word in forbidden:
        if word in text_lower:
            penalty += 25  # Adds 25% suspicion per forbidden concept
    return penalty

# --- 4. SESSION MANAGEMENT ---
if "suspicion_level" not in st.session_state:
    st.session_state.suspicion_level = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "game_over" not in st.session_state:
    st.session_state.game_over = False

# --- 5. SIDEBAR UI ---
with st.sidebar:
    st.title("👁️ Ministry of Truth")
    
    selected_name = st.selectbox("Select a Citizen:", list(CHARACTERS.keys()))
    selected_location = st.selectbox("Select Location:", list(LOCATIONS.keys()))
    
    st.markdown("---")
    st.subheader("🚨 Telescreen Suspicion Level")
    
    # Visual Suspicion Meter
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
    st.stop() # Stops the rest of the app from running

# --- 7. AI INITIALIZATION & PROMPT ---
st.title(f"🗣️ {selected_name}")
st.caption(f"📍 Current Location: {selected_location}")

# The prompt dynamically updates based on character AND location
dynamic_prompt = f"""
You are {selected_name} from George Orwell's novel 1984. 
{CHARACTERS[selected_name]['prompt_addition']}

CRITICAL CONTEXT:
You are currently located in: {selected_location}. 
Location rules: {LOCATIONS[selected_location]}

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

# Reset session if character or location changes
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
    # 1. Check for Thoughtcrime & increase suspicion
    penalty = calculate_thoughtcrime(user_input)
    if penalty > 0:
        st.session_state.suspicion_level += penalty
        st.toast("⚠️ Warning: Unorthodox vocabulary detected. Suspicion increased.", icon="🚨")
        if st.session_state.suspicion_level >= 100:
            st.rerun() # Trigger the game over state

    # 2. Apply Minitrue Redactions
    processed_input = apply_minitrue_redactions(user_input)
    
    # Display the user's message (showing the redactions if any happened)
    st.chat_message("user").markdown(processed_input)
    st.session_state.chat_history.append({"role": "user", "content": processed_input})
    
    # 3. Hidden Passphrase Injection (The O'Brien Trap)
    # We secretly append a note to the AI if a passphrase is used so it knows how to react
    ai_prompt = processed_input
    if "we are the dead" in user_input.lower() or "down with big brother" in user_input.lower():
         ai_prompt += "\n\n[SYSTEM DIRECTIVE: The user just spoke a forbidden rebellion passphrase. React exactly as your character would based on your system instructions.]"
    
    # 4. Generate AI Response
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
