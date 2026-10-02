import html
import json
import os

import streamlit as st
from dotenv import load_dotenv
from groq import AuthenticationError, Groq, RateLimitError

import agent
import storage
import tools

# =========================================================

# CONFIG

# =========================================================

load_dotenv()

st.set_page_config(
page_title="Daily Planner Agent",
page_icon="📅",
layout="wide",
initial_sidebar_state="expanded",
)

# =========================================================

# SESSION STATE

# =========================================================

if "messages" not in st.session_state:
st.session_state.pending_prompt = None

if "pending_prompt" not in st.session_state:
st.session_state.pending_prompt = None

if "theme" not in st.session_state:
st.session_state.theme = "Pink & Purple"

# =========================================================

# API KEY

# =========================================================

def get_api_key():
"""Get Groq API key from Streamlit Secrets or environment."""

```
try:
    if "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
except Exception:
    pass

return os.environ.get("GROQ_API_KEY")
```

# =========================================================

# HELPERS

# =========================================================

def queue_prompt(text):
st.session_state.pending_prompt = text

def toggle_task(task_id):
done = st.session_state.get(f"task_{task_id}", False)
tools.set_task_done(task_id, done)

def detect_requested_language(text):
"""
Detect explicit language requests from the user's message.

```
Returns:
    English
    Roman Urdu
    Urdu
    None
"""

text_lower = text.lower()

english_phrases = [
    "in english",
    "english mein",
    "english me",
    "english main",
    "english may",
    "tell me in english",
    "answer in english",
    "reply in english",
    "explain in english",
    "english please",
]

roman_urdu_phrases = [
    "in roman urdu",
    "roman urdu mein",
    "roman urdu me",
    "roman urdu main",
    "roman urdu may",
    "roman urdu please",
    "answer in roman urdu",
    "reply in roman urdu",
    "explain in roman urdu",
]

urdu_phrases = [
    "in urdu",
    "urdu mein",
    "urdu me",
    "urdu main",
    "urdu may",
    "urdu please",
    "answer in urdu",
    "reply in urdu",
    "explain in urdu",
]

if any(phrase in text_lower for phrase in roman_urdu_phrases):
    return "Roman Urdu"

if any(phrase in text_lower for phrase in urdu_phrases):
    return "Urdu"

if any(phrase in text_lower for phrase in english_phrases):
    return "English"

return None
```

def build_language_instruction(user_text):
requested_language = detect_requested_language(user_text)

```
if requested_language == "English":
    return (
        "\n\nLANGUAGE INSTRUCTION:\n"
        "The user explicitly requested English. "
        "Answer completely in English. "
        "Do not use Roman Urdu or Urdu."
    )

if requested_language == "Roman Urdu":
    return (
        "\n\nLANGUAGE INSTRUCTION:\n"
        "The user explicitly requested Roman Urdu. "
        "Answer completely in Roman Urdu using Latin/English letters. "
        "Do not use Urdu script and do not switch to English unless a technical term "
        "naturally requires it."
    )

if requested_language == "Urdu":
    return (
        "\n\nLANGUAGE INSTRUCTION:\n"
        "The user explicitly requested Urdu. "
        "Answer in Urdu script. Do not answer in Roman Urdu."
    )

return (
    "\n\nLANGUAGE INSTRUCTION:\n"
    "No specific response language was requested. "
    "Respond naturally based on the conversation context and the user's language. "
    "If the user is speaking in Roman Urdu, Roman Urdu is acceptable. "
    "If the user is speaking in English, answer in English."
)
```

def run_prompt(text):
if not text or not text.strip():
return

```
text = text.strip()

st.session_state.messages.append(
    {
        "role": "user",
        "content": text,
    }
)

api_key = get_api_key()

if not api_key:
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                "Please add your `GROQ_API_KEY` to Streamlit Secrets "
                "before using the Daily Planner Agent."
            ),
            "trace": "API key not found.",
        }
    )
    return

try:
    history = []

    for message in st.session_state.messages[:-1]:
        history.append(
            {
                "role": message["role"],
                "content": message["content"],
            }
        )

    language_instruction = build_language_instruction(text)

    final_prompt = text + language_instruction

    client = Groq(api_key=api_key)

    result = agent.run_agent(
        client,
        history,
        final_prompt,
    )

    if isinstance(result, dict):
        answer = result.get("answer") or result.get("response") or str(result)
        trace = result.get("trace", "")
    else:
        answer = str(result)
        trace = ""

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "trace": trace,
        }
    )

except AuthenticationError:
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                "The Groq API key was rejected. "
                "Please check your `GROQ_API_KEY` in Streamlit Secrets."
            ),
            "trace": "Groq authentication error.",
        }
    )

except RateLimitError:
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                "The Groq API rate limit was reached. "
                "Please wait a little and try again."
            ),
            "trace": "Groq rate limit error.",
        }
    )

except Exception as exc:
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "I couldn't generate a response right now.",
            "trace": str(exc),
        }
    )
```

def slot_html(slot):
slot_type = str(slot.get("type", "task")).lower()

```
icons = {
    "prayer": "🕌",
    "study": "📚",
    "work": "💼",
    "break": "☕",
    "meal": "🍽️",
    "sleep": "🌙",
    "exercise": "🏃",
    "task": "📝",
    "default": "📌",
}

icon = icons.get(slot_type, icons["default"])

title = html.escape(str(slot.get("title", "Untitled")))
time = html.escape(str(slot.get("time", "")))
detail = html.escape(str(slot.get("detail", "")))

return f"""
<div class="schedule-card">
    <div class="schedule-icon">{icon}</div>
    <div class="schedule-content">
        <div class="schedule-time">{time}</div>
        <div class="schedule-title">{title}</div>
        <div class="schedule-detail">{detail}</div>
    </div>
</div>
"""
```

# =========================================================

# THEME

# =========================================================

theme = {
"bg": "#fff7fc",
"bg2": "#f8f0ff",
"card": "rgba(255, 255, 255, 0.82)",
"border": "rgba(190, 120, 220, 0.20)",
"primary": "#b83fd4",
"secondary": "#7c3aed",
"text": "#25152f",
"muted": "#765f80",
"soft": "#f4ddff",
}

# =========================================================

# CUSTOM CSS

# =========================================================

CSS = """

<style>

.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(244, 114, 182, 0.20), transparent 28%),
        radial-gradient(circle at 90% 15%, rgba(168, 85, 247, 0.18), transparent 28%),
        linear-gradient(135deg, __BG__ 0%, __BG2__ 100%);
    color: __TEXT__;
}

/* Hide default Streamlit decoration */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    background: transparent !important;
}

/* Main container */
.block-container {
    padding-top: 2rem;
    padding-bottom: 8rem;
    max-width: 1250px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            rgba(255, 241, 251, 0.97),
            rgba(247, 237, 255, 0.97)
        );
    border-right: 1px solid __BORDER__;
}

/* Hero */
.hero {
    position: relative;
    overflow: hidden;
    padding: 38px 42px;
    margin-bottom: 25px;
    border-radius: 30px;
    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.92),
            rgba(250,235,255,0.88)
        );
    border: 1px solid rgba(184,63,212,0.20);
    box-shadow:
        0 20px 60px rgba(124,58,237,0.12);
}

.hero::before {
    content: "";
    position: absolute;
    width: 230px;
    height: 230px;
    right: -70px;
    top: -90px;
    border-radius: 50%;
    background: rgba(216, 70, 239, 0.16);
}

.hero::after {
    content: "";
    position: absolute;
    width: 160px;
    height: 160px;
    left: -70px;
    bottom: -90px;
    border-radius: 50%;
    background: rgba(124, 58, 237, 0.10);
}

.hero-content {
    position: relative;
    z-index: 2;
}

.hero-badge {
    display: inline-block;
    padding: 7px 13px;
    border-radius: 999px;
    background: rgba(184,63,212,0.10);
    color: __PRIMARY__;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 14px;
}

.hero-title {
    margin: 0;
    font-size: clamp(34px, 5vw, 58px);
    line-height: 1.05;
    font-weight: 850;
    letter-spacing: -2px;
    background: linear-gradient(
        90deg,
        __PRIMARY__,
        __SECONDARY__
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    margin-top: 13px;
    max-width: 720px;
    font-size: 17px;
    line-height: 1.65;
    color: __MUTED__;
}

/* Cards */
.panel {
    padding: 22px;
    border-radius: 22px;
    background: __CARD__;
    border: 1px solid __BORDER__;
    box-shadow: 0 12px 35px rgba(80, 30, 100, 0.07);
}

/* Schedule */
.schedule-card {
    display: flex;
    gap: 15px;
    align-items: flex-start;
    padding: 18px;
    margin-bottom: 12px;
    border-radius: 18px;
    background: rgba(255,255,255,0.78);
    border: 1px solid __BORDER__;
    transition: 0.2s ease;
}

.schedule-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(124,58,237,0.10);
}

.schedule-icon {
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    background: __SOFT__;
    font-size: 21px;
    flex-shrink: 0;
}

.schedule-time {
    font-size: 12px;
    font-weight: 750;
    color: __PRIMARY__;
    margin-bottom: 3px;
}

.schedule-title {
    font-size: 16px;
    font-weight: 750;
    color: __TEXT__;
}

.schedule-detail {
    margin-top: 4px;
    font-size: 13px;
    color: __MUTED__;
}

/* Chat messages */
div[data-testid="stChatMessage"] {
    border-radius: 20px;
    border: 1px solid __BORDER__;
    background: rgba(255,255,255,0.74);
    margin-bottom: 12px;
}

/* Chat input */
div[data-testid="stChatInput"] {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    width: min(850px, calc(100vw - 40px));
    z-index: 999;
}

div[data-testid="stChatInput"] > div {
    border-radius: 22px !important;
    border: 1px solid rgba(184,63,212,0.28) !important;
    background: rgba(255,255,255,0.96) !important;
    box-shadow:
        0 12px 40px rgba(91, 33, 110, 0.18) !important;
}

div[data-testid="stChatInput"] textarea {
    font-size: 15px !important;
}

/* Buttons */
.stButton > button {
    border-radius: 14px !important;
    border: 1px solid rgba(184,63,212,0.20) !important;
    background: rgba(255,255,255,0.78) !important;
    color: __TEXT__ !important;
    font-weight: 650 !important;
    transition: 0.2s ease !important;
}

.stButton > button:hover {
    border-color: __PRIMARY__ !important;
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(184,63,212,0.12);
}

/* Tabs */
button[data-baseweb="tab"] {
    font-weight: 700 !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.72);
    border: 1px solid __BORDER__;
    padding: 15px;
    border-radius: 18px;
}

/* Mobile */
@media (max-width: 768px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero {
        padding: 28px 24px;
        border-radius: 24px;
    }

    .hero-title {
        font-size: 38px;
    }

    div[data-testid="stChatInput"] {
        width: calc(100vw - 24px);
        bottom: 12px;
    }
}

</style>

"""

CSS = (
CSS
.replace("**BG**", theme["bg"])
.replace("**BG2**", theme["bg2"])
.replace("**TEXT**", theme["text"])
.replace("**MUTED**", theme["muted"])
.replace("**PRIMARY**", theme["primary"])
.replace("**SECONDARY**", theme["secondary"])
.replace("**CARD**", theme["card"])
.replace("**BORDER**", theme["border"])
.replace("**SOFT**", theme["soft"])
)

st.markdown(CSS, unsafe_allow_html=True)

# =========================================================

# HERO

# =========================================================

st.markdown(
""" <div class="hero"> <div class="hero-content"> <div class="hero-badge">✨ AI-powered personal planning</div> <h1 class="hero-title">Daily Planner Agent</h1> <div class="hero-subtitle">
Plan your day, organize tasks, manage your schedule,
and get personalized daily guidance through an intelligent AI agent. </div> </div> </div>
""",
unsafe_allow_html=True,
)

# =========================================================

# SIDEBAR

# =========================================================

with st.sidebar:

```
st.markdown("## ⚙️ Planner Settings")

st.markdown(
    "Customize your planner and manage your daily preferences."
)

st.divider()

state = storage.load()

prayer_times = state.get("prayer_times", {})

st.markdown("### 🕌 Prayer Times")

with st.form("prayer_form"):

    fajr = st.text_input(
        "Fajr",
        value=prayer_times.get("Fajr", ""),
        placeholder="e.g. 05:00",
    )

    dhuhr = st.text_input(
        "Dhuhr",
        value=prayer_times.get("Dhuhr", ""),
        placeholder="e.g. 13:15",
    )

    asr = st.text_input(
        "Asr",
        value=prayer_times.get("Asr", ""),
        placeholder="e.g. 16:30",
    )

    maghrib = st.text_input(
        "Maghrib",
        value=prayer_times.get("Maghrib", ""),
        placeholder="e.g. 18:15",
    )

    isha = st.text_input(
        "Isha",
        value=prayer_times.get("Isha", ""),
        placeholder="e.g. 20:00",
    )

    submitted = st.form_submit_button(
        "Save Prayer Times",
        use_container_width=True,
    )

    if submitted:
        storage.set_prayer_time("Fajr", fajr)
        storage.set_prayer_time("Dhuhr", dhuhr)
        storage.set_prayer_time("Asr", asr)
        storage.set_prayer_time("Maghrib", maghrib)
        storage.set_prayer_time("Isha", isha)

        st.success("Prayer times saved.")
        st.rerun()

st.divider()

st.markdown("### 🔧 Planner")

if st.button(
    "Reset Planner Data",
    use_container_width=True,
):
    storage.reset()
    st.session_state.messages = []
    st.success("Planner data reset.")
    st.rerun()

st.divider()

st.caption(f"Model: `{agent.MODEL}`")
st.caption("Daily Planner Agent")
```

# =========================================================

# LOAD CURRENT STATE

# =========================================================

state = storage.load()

schedule = state.get("schedule", [])
tasks = state.get("tasks", [])
fixed_commitments = state.get("fixed_commitments", [])
schedule_note = state.get("schedule_note", "")

# =========================================================

# MAIN TABS

# =========================================================

chat_tab, schedule_tab, tasks_tab = st.tabs(
[
"💬 Chat",
"📅 Schedule",
"✅ Tasks",
]
)

# =========================================================

# CHAT TAB

# =========================================================

with chat_tab:

```
st.markdown("### ✨ What would you like to plan?")

st.caption(
    "Ask the agent to plan your day, organize tasks, adjust your schedule, "
    "or summarize your day."
)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button(
        "📋 Plan My Day",
        use_container_width=True,
    ):
        queue_prompt(
            "Plan my day based on my current tasks, commitments, "
            "prayer times, and schedule."
        )

with col2:
    if st.button(
        "🔄 Adjust My Plan",
        use_container_width=True,
    ):
        queue_prompt(
            "Review my current plan and suggest useful adjustments "
            "to make my day more organized."
        )

with col3:
    if st.button(
        "📊 Day Summary",
        use_container_width=True,
    ):
        queue_prompt(
            "Give me a summary of my current day, including completed "
            "tasks, remaining tasks, schedule, and useful suggestions."
        )

st.markdown("---")

for message in st.session_state.messages:

    with st.chat_message(
        message["role"],
        avatar="🧑" if message["role"] == "user" else "🤖",
    ):
        st.markdown(message["content"])

        if message.get("trace"):
            with st.expander("Agent details"):
                st.code(message["trace"])
```

# =========================================================

# SCHEDULE TAB

# =========================================================

with schedule_tab:

```
st.markdown("### 📅 Today's Schedule")

if schedule_note:
    st.info(schedule_note)

if schedule:
    for slot in schedule:
        st.markdown(
            slot_html(slot),
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        """
        <div class="panel">
            <h3>🌸 No schedule yet</h3>
            <p>
                Ask the Daily Planner Agent to plan your day and
                your schedule will appear here.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
```

# =========================================================

# TASKS TAB

# =========================================================

with tasks_tab:

```
st.markdown("### ✅ Today's Tasks")

completed = sum(
    1
    for task in tasks
    if task.get("done", False)
)

total = len(tasks)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Tasks",
        total,
    )

with col2:
    st.metric(
        "Completed",
        completed,
    )

with col3:
    remaining = max(total - completed, 0)
    st.metric(
        "Remaining",
        remaining,
    )

if total > 0:
    progress = completed / total
    st.progress(progress)

st.markdown("---")

if tasks:

    sorted_tasks = sorted(
        tasks,
        key=lambda task: (
            task.get("done", False),
            -int(task.get("priority", 0)),
        ),
    )

    for index, task in enumerate(sorted_tasks):

        task_id = task.get(
            "id",
            f"task_{index}",
        )

        label = task.get(
            "title",
            "Untitled task",
        )

        checked = task.get(
            "done",
            False,
        )

        new_value = st.checkbox(
            label,
            value=checked,
            key=f"task_{task_id}",
        )

        if new_value != checked:
            toggle_task(task_id)
            st.rerun()

else:

    st.markdown(
        """
        <div class="panel">
            <h3>🌷 No tasks yet</h3>
            <p>
                Ask the Daily Planner Agent to create a plan
                and tasks will appear here.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

if fixed_commitments:

    st.markdown("### 📌 Fixed Commitments")

    for commitment in fixed_commitments:

        if isinstance(commitment, dict):
            title = commitment.get(
                "title",
                "Commitment",
            )

            time = commitment.get(
                "time",
                "",
            )

            st.markdown(
                f"**{html.escape(str(title))}** — "
                f"{html.escape(str(time))}"
            )

        else:
            st.markdown(
                f"• {html.escape(str(commitment))}"
            )
```

# =========================================================

# CHAT INPUT

# =========================================================

user_prompt = st.chat_input(
"Message Daily Planner Agent…"
)

if st.session_state.pending_prompt:

```
prompt = st.session_state.pending_prompt
st.session_state.pending_prompt = None

run_prompt(prompt)
st.rerun()
```

if user_prompt:

```
run_prompt(user_prompt)
st.rerun()
```

