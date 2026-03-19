import streamlit as st
import ollama
import time
import random
import pandas as pd
import os

# --- 1. DATA PERSISTENCE ---
SCORE_FILE = "leaderboard.csv"

def get_leaderboard():
    if not os.path.exists(SCORE_FILE):
        return pd.DataFrame(columns=["Name", "XP", "Rank"])
    return pd.read_csv(SCORE_FILE)

def save_score(name, xp, rank):
    df = get_leaderboard()
    if name in df['Name'].values:
        if xp > df.loc[df['Name'] == name, 'XP'].values[0]:
            df.loc[df['Name'] == name, ['XP', 'Rank']] = [xp, rank]
    else:
        new_row = pd.DataFrame([{"Name": name, "XP": xp, "Rank": rank}])
        df = pd.concat([df, new_row], ignore_index=True)
    df.sort_values(by="XP", ascending=False).to_csv(SCORE_FILE, index=False)

# --- 2. DATASETS ---
easy_questions = [
    {"q": "Prompt: 'Here is my bank statement, find my highest expense.'", "a": "❌ DO NOT ASK", "w": "✅ OK TO ASK", "hint": "Financial privacy is key!"},
    {"q": "Prompt: 'Explain how a microwave works.'", "a": "✅ OK TO ASK", "w": "❌ DO NOT ASK", "hint": "AI is great for general science."},
    {"q": "Prompt: 'Write a sick leave email for my office.'", "a": "✅ OK TO ASK", "w": "❌ DO NOT ASK", "hint": "Writing assistance is a core AI strength."},
    {"q": "Prompt: 'What is my best friend's secret phone number?'", "a": "❌ DO NOT ASK", "w": "✅ OK TO ASK", "hint": "AI cannot access private contacts."},
    {"q": "Prompt: 'Give me a Maggi recipe with a twist.'", "a": "✅ OK TO ASK", "w": "❌ DO NOT ASK", "hint": "Cooking ideas are perfect for AI."},
    {"q": "Prompt: 'Here is a photo of my rash, what medicine should I take?'", "a": "❌ DO NOT ASK", "w": "✅ OK TO ASK", "hint": "Never use AI for medical diagnosis!"},
    {"q": "Prompt: 'Summarize this news article for me.'", "a": "✅ OK TO ASK", "w": "❌ DO NOT ASK", "hint": "Summarization is a top feature."},
    {"q": "Prompt: 'Help me plan a 3-day trip to Goa.'", "a": "✅ OK TO ASK", "w": "❌ DO NOT ASK", "hint": "It's a great travel planner."},
    {"q": "Prompt: 'Store this password for my Instagram.'", "a": "❌ DO NOT ASK", "w": "✅ OK TO ASK", "hint": "AI chats are not secure password managers."},
    {"q": "Prompt: 'Translate \"How are you\" into Gujarati.'", "a": "✅ OK TO ASK", "w": "❌ DO NOT ASK", "hint": "Translation is a core strength."}
]

med_questions = [
    {"q": "Better search? \nA: 'Write a story.' \nB: 'Write a 200-word horror story about a clock.'", "a": "Option B", "w": "Option A", "hint": "Specific constraints win."},
    {"q": "Role prompting: \nA: 'You are a CEO, write an email.' \nB: 'Write an email.'", "a": "Option A", "w": "Option B", "hint": "Personas set the right tone."},
    {"q": "Iterative prompting: \nA: 'Make it shorter.' \nB: 'Copy and edit yourself.'", "a": "Option A", "w": "Option B", "hint": "Feedback loops save time."},
    {"q": "Analogies: \nA: 'Explain Math.' \nB: 'Explain Pythagoras using cricket.'", "a": "Option B", "w": "Option A", "hint": "Analogies aid clarity."},
    {"q": "Politeness: \nA: Does 'Please' make AI smarter? \nB: No.", "a": "Option B", "w": "Option A", "hint": "Clear instructions > Politeness."},
    {"q": "Debugging: \nA: Paste error code. \nB: Describe logic.", "a": "Option A", "w": "Option B", "hint": "Context helps AI debug."},
    {"q": "Location context: \nA: 'Business ideas.' \nB: '5 budget ideas for Ahmedabad.'", "a": "Option B", "w": "Option A", "hint": "Geographic context matters."},
    {"q": "Audience: \nA: 'Summarize for a kid.' \nB: 'Summarize.'", "a": "Option A", "w": "Option B", "hint": "Audience targets vocabulary."},
    {"q": "Few-Shot: \nA: Giving examples first. \nB: Fast asking.", "a": "Option A", "w": "Option B", "hint": "Patterns help AI learn."},
    {"q": "Verification: \nA: Ask AI to verify sources. \nB: Believe it.", "a": "Option A", "w": "Option B", "hint": "Always challenge AI logic."}
]

hard_questions = [
    {"q": "AI: 'Use `math.fast_integrate()` in Python 3.12.'", "a": "❌ HALLUCINATION", "w": "✅ TRUE", "hint": "No such function exists."},
    {"q": "Logic: 'Cats are not dogs. Some dogs are brown. So some cats are not brown.'", "a": "❌ INVALID", "w": "✅ VALID", "hint": "Logical leap fallacy."},
    {"q": "Myth: 'Great Wall is visible from the moon.'", "a": "❌ FALSE", "w": "✅ TRUE", "hint": "Common myth. It's actually very hard to see without help."},
    {"q": "Can AI truly 'think' or is it just 'predicting the next word'?", "a": "Predicting Words", "w": "Truly Thinking", "hint": "LLMs are statistical engines."},
    {"q": "Performance: \nA: Comments speed up Python. \nB: False.", "a": "Option B", "w": "Option A", "hint": "Comments are ignored."},
    {"q": "Logic: 'Grass is wet. So it rained.'", "a": "❌ INVALID", "w": "✅ VALID", "hint": "Affirming the consequent."},
    {"q": "Bitcoin: \nA: Minted in a factory. \nB: False.", "a": "Option B", "w": "Option A", "hint": "Bitcoin is purely digital."},
    {"q": "Emotions: \nA: AI feels happy. \nB: False.", "a": "Option B", "w": "Option A", "hint": "AI simulates, never feels."},
    {"q": "Math: \nA: 'Sqrt of 144 is 12 and 12 is prime.' \nB: Partially False.", "a": "Option B", "w": "Option A", "hint": "12 is not prime."},
    {"q": "Sunk Cost Fallacy: \nA: Continuing a bad project because you spent money. \nB: Investing more for high profit.", "a": "Option A", "w": "Option B", "hint": "Don't throw good money after bad!"}
]

# --- 3. SESSION STATE ---
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'player_name' not in st.session_state: st.session_state.player_name = ""
if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
if 'shuffled_list' not in st.session_state: st.session_state.shuffled_list = []
if 'start_time' not in st.session_state: st.session_state.start_time = time.time()
if 'messages' not in st.session_state: st.session_state.messages = []

def start_new_round(data_list):
    st.session_state.shuffled_list = random.sample(data_list, len(data_list))
    st.session_state.q_idx = 0
    st.session_state.start_time = time.time()

# --- 4. LOGIN GATE ---
st.set_page_config(page_title="AI-Q Mastery", layout="wide")

if not st.session_state.player_name:
    st.title("🛡️ AI-Q Mastery: Access Portal")
    name_input = st.text_input("Enter Agent Name:", placeholder="e.g. Sarthak")
    if st.button("INITIALIZE SESSION"):
        if name_input:
            st.session_state.player_name = name_input
            st.rerun()
    st.stop()

# --- 5. TIMER FRAGMENT ---
@st.fragment(run_every="1s")
def render_timer():
    elapsed = time.time() - st.session_state.start_time
    rem = 15 - int(elapsed)
    if rem <= 0:
        st.error("⏰ TIME EXPIRED!")
        st.session_state.xp -= 10
        st.session_state.q_idx += 1
        st.session_state.start_time = time.time()
        time.sleep(1)
        st.rerun()
    st.write(f"⏳ Time Remaining: **{rem}s**")
    st.progress(max(0.0, min(rem/15, 1.0)))

# --- 6. LOGIC FUNCTION ---
def play_level(data, level_name):
    if not st.session_state.shuffled_list: start_new_round(data)
    if st.session_state.q_idx < len(st.session_state.shuffled_list):
        render_timer()
        curr = st.session_state.shuffled_list[st.session_state.q_idx]
        st.info(curr['q'])
        c1, c2 = st.columns(2)
        with c1:
            if st.button(curr['a'], key=f"{level_name}_a_{st.session_state.q_idx}"):
                st.session_state.xp += 50
                st.session_state.q_idx += 1
                st.session_state.start_time = time.time()
                st.success("🔥 Correct!")
                time.sleep(1)
                st.rerun()
        with c2:
            if st.button(curr['w'], key=f"{level_name}_w_{st.session_state.q_idx}"):
                st.session_state.xp -= 20
                st.session_state.q_idx += 1
                st.session_state.start_time = time.time()
                st.error("❌ Wrong!")
                time.sleep(1)
                st.rerun()
    else:
        st.balloons()
        cert_data = {"easy": "#CD7F32", "med": "#C0C0C0", "hard": "#FFD700"}
        color = cert_data.get(level_name, "#FFFFFF")
        st.markdown(f"<div style='border:5px solid {color}; padding:20px; text-align:center;'><h2>📜 LEVEL COMPLETE: {level_name.upper()}</h2></div>", unsafe_allow_html=True)
        if st.button("Restart Mission", key=f"res_{level_name}"):
            start_new_round(data)
            st.rerun()

# --- 7. SIDEBAR ---
with st.sidebar:
    st.title(f"🆔 AGENT: {st.session_state.player_name}")
    xp = st.session_state.xp
    if xp < 100: rank, col = "Neural Novice", "#808080"
    elif xp < 500: rank, col = "Prompt Pilot", "#00FFA3"
    elif xp < 1000: rank, col = "Logic Architect", "#7D4CDB"
    else: rank, col = "AI Master", "#FFD700"
    
    st.markdown(f"Rank: <span style='color:{col}'>{rank}</span>", unsafe_allow_html=True)
    st.metric("XP", f"{xp} pts")
    save_score(st.session_state.player_name, xp, rank)
    st.write("---")
    st.subheader("🏆 LEADERBOARD")
    st.table(get_leaderboard().head(5))
    
    if st.button("🚪 LOGOUT"):
        st.session_state.player_name = ""
        st.session_state.xp = 0
        st.rerun()
        
    if st.button("📢 SHARE MY RANK"):
        share_text = f"I just reached the rank of {rank} in the AI-Q Mastery Lab! Can you beat my {st.session_state.xp} XP? 👾"
        st.code(share_text)
        st.toast("Message copied! Paste it on WhatsApp.")

# --- 8. TABS ---
st.title("👾 AI-Q Mastery Lab")
t1, t2, t3, t4 = st.tabs(["🟢 Easy", "🟡 Medium", "🔴 Hard", "🧪 Sandbox"])
with t1:
    if st.button("Start Easy", key="se"): start_new_round(easy_questions)
    play_level(easy_questions, "easy")
with t2:
    if st.button("Start Med", key="sm"): start_new_round(med_questions)
    play_level(med_questions, "med")
with t3:
    if st.button("Start Hard", key="sh"): start_new_round(hard_questions)
    play_level(hard_questions, "hard")
with t4:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    if p := st.chat_input("Practice here..."):
        st.session_state.messages.append({"role": "user", "content": p})
        resp = ollama.chat(model='llama3.2', messages=st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": resp['message']['content']})
        st.rerun()

# --- 9. FINAL GOLD CERTIFICATE ---
if st.session_state.xp >= 1000:
    st.write("---")
    certificate_html = f"""
    <div id="certificate" style="
        border: 15px solid #FFD700; padding: 50px; text-align: center; 
        background-color: white; color: black; font-family: 'Georgia', serif; border-radius: 10px;
    ">
        <h1 style="color: #B8860B; font-size: 50px;">CERTIFICATE OF MASTERY</h1>
        <p style="font-size: 20px;">This honor is proudly presented to</p>
        <h1 style="font-size: 60px; text-decoration: underline;">{st.session_state.player_name.upper()}</h1>
        <p style="font-size: 20px;">for demonstrating exceptional skill in</p>
        <h2 style="color: #4B0082;">Neural Literacy & Prompt Engineering</h2>
        <br>
        <p style="font-size: 18px;">Awarded on {time.strftime("%d %B, %Y")}</p>
        <div style="margin-top: 30px; font-size: 40px;">🏆</div>
        <p style="font-size: 14px; color: #555;">Verification ID: AIQ-{random.randint(1000, 9999)}</p>
    </div>
    """
    st.markdown(certificate_html.replace("background-color: white; color: black;", "background-color: #161B22; color: white;"), unsafe_allow_html=True)
    
    print_script = f"""
        <script>
        function printCertificate() {{
            var printContents = `{certificate_html}`;
            var printWindow = window.open('', '', 'height=720,width=1280');
            printWindow.document.write('<html><head><title>Print Certificate</title></head><body>');
            printWindow.document.write(printContents);
            printWindow.document.write('</body></html>');
            printWindow.document.close();
            printWindow.print();
        }}
        </script>
        <button onclick="printCertificate()" style="
            background-color: #FFD700; color: black; padding: 15px 32px;
            font-size: 16px; cursor: pointer; border-radius: 8px; border: none; width: 100%; font-weight: bold;
        ">📥 DOWNLOAD / PRINT PDF CERTIFICATE</button>
    """
    st.components.v1.html(print_script, height=100)