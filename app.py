import html
import os

import streamlit as st
from groq import Groq

import agent
import storage
import tools

# =========================================================

# PAGE

# =========================================================

st.set_page_config(
page_title="Daily Planner Agent",
page_icon="📅",
layout="wide"
)

# =========================================================

# SESSION STATE

# =========================================================

st.session_state.setdefault("messages", [])
st.session_state.setdefault("pending_prompt", None)

# =========================================================

# API KEY

# =========================================================

def get_api_key():
key = os.environ.get("GROQ_API_KEY")

```
if key:
    return key

try:
    return st.secrets["GROQ_API_KEY"]
except Exception:
    return None
```

# =========================================================

# LANGUAGE

# =========================================================

def detect_language(text):

```
text = text.lower()

if (
    "roman urdu" in text
    or "roman urdu mein" in text
    or "roman urdu me" in text
    or "roman urdu main" in text
    or "in roman urdu" in text
):
    return "Roman Urdu"

if (
    "english mein" in text
    or "english me" in text
    or "english main" in text
    or "english may" in text
    or "in english" in text
):
    return "English"

if (
    "urdu mein" in text
    or "urdu me" in text
    or "urdu main" in text
    or "urdu may" in text
    or "in urdu" in text
):
    return "Urdu"

return None
```

def language_instruction(text):

```
language = detect_language(text)

if language == "English":
    return (
        "IMPORTANT: The user explicitly requested English. "
        "Answer completely in English. "
        "Do not use Roman Urdu or Urdu script."
    )

if language == "Roman Urdu":
    return (
        "IMPORTANT: The user explicitly requested Roman Urdu. "
        "Answer completely in Roman Urdu using Latin letters. "
        "Do not use Urdu script."
    )

if language == "Urdu":
    return (
        "IMPORTANT: The user explicitly requested Urdu. "
        "Answer completely in Urdu script. "
        "Do not use Roman Urdu."
    )

return (
    "IMPORTANT: No language was explicitly requested. "
    "Follow the language used by the user. "
    "English input means English response. "
    "Roman Urdu input means Roman Urdu response. "
    "Urdu-script input means Urdu-script response."
)
```

# =========================================================

# CHAT

# =========================================================

def run_prompt(text):

```
if not text:
    return

text = text.strip()

if not text:
    return

st.session_state.messages.append(
    {
        "role": "user",
        "content": text
    }
)

key = get_api_key()

if not key:
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                "Please add GROQ_API_KEY to "
                "Streamlit Secrets."
            )
        }
    )
    return

history = []

for message in st.session_state.messages[:-1]:
    history.append(
        {
            "role": message["role"],
            "content": message["content"]
        }
    )

prompt = (
    text
    + "\n\n"
    + language_instruction(text)
)

try:

    client = Groq(
        api_key=key
    )

    answer = agent.run_agent(
        client,
        history,
        prompt
    )

    if isinstance(answer, dict):
        answer = answer.get(
            "answer",
            answer.get(
                "response",
                "I could not generate a response."
            )
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": str(answer)
        }
    )

except Exception as error:

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                "I could not generate a response right now."
            ),
            "trace": str(error)
        }
    )
```

# =========================================================

# TASK

# =========================================================

def toggle_task(task_id):

```
value = st.session_state.get(
    "task_" + str(task_id),
    False
)

tools.set_task_done(
    task_id,
    value
)
```

# =========================================================

# SCHEDULE CARD

# =========================================================

def make_schedule_card(slot):

```
slot_type = str(
    slot.get("type", "task")
).lower()

icons = {
    "prayer": "🕌",
    "study": "📚",
    "work": "💼",
    "break": "☕",
    "meal": "🍽️",
    "sleep": "🌙",
    "exercise": "🏃",
    "task": "📝"
}

icon = icons.get(
    slot_type,
    "📌"
)

title = html.escape(
    str(
        slot.get(
            "title",
            "Untitled"
        )
    )
)

time = html.escape(
    str(
        slot.get(
            "time",
            ""
        )
    )
)

detail = html.escape(
    str(
        slot.get(
            "detail",
            ""
        )
    )
)

return f"""
<div class="schedule-card">

    <div class="schedule-icon">
        {icon}
    </div>

    <div>

        <div class="schedule-time">
            {time}
        </div>

        <div class="schedule-title">
            {title}
        </div>

        <div class="schedule-detail">
            {detail}
        </div>

    </div>

</div>
"""
```

# =========================================================

# CSS

# =========================================================

st.markdown(
"""

<style>

.stApp {
    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(244,114,182,0.20),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(168,85,247,0.18),
            transparent 28%
        ),
        linear-gradient(
            135deg,
            #fff7fc,
            #f8f0ff
        );
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 8rem;
}


/* HERO */

.hero {
    padding: 42px;
    margin-bottom: 28px;
    border-radius: 30px;
    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.96),
            rgba(250,235,255,0.92)
        );
    border: 1px solid rgba(184,63,212,0.20);
    box-shadow:
        0 20px 60px rgba(124,58,237,0.12);
}

.hero-badge {
    display: inline-block;
    padding: 7px 14px;
    border-radius: 999px;
    background: rgba(184,63,212,0.10);
    color: #b83fd4;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 15px;
}

.hero-title {
    margin: 0;
    font-size: clamp(38px,5vw,60px);
    line-height: 1.05;
    font-weight: 850;
    letter-spacing: -2px;
    background:
        linear-gradient(
            90deg,
            #b83fd4,
            #7c3aed
        );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    margin-top: 14px;
    max-width: 760px;
    font-size: 17px;
    line-height: 1.65;
    color: #765f80;
}


/* SCHEDULE */

.schedule-card {
    display: flex;
    gap: 15px;
    align-items: flex-start;
    padding: 18px;
    margin-bottom: 12px;
    border-radius: 18px;
    background: rgba(255,255,255,0.82);
    border: 1px solid rgba(190,120,220,0.22);
}

.schedule-icon {
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    background: #f4ddff;
    font-size: 21px;
    flex-shrink: 0;
}

.schedule-time {
    font-size: 12px;
    font-weight: 750;
    color: #b83fd4;
}

.schedule-title {
    font-size: 16px;
    font-weight: 750;
    color: #25152f;
}

.schedule-detail {
    margin-top: 4px;
    font-size: 13px;
    color: #765f80;
}


/* CHAT */

div[data-testid="stChatMessage"] {
    border-radius: 20px;
    border: 1px solid rgba(190,120,220,0.22);
    background: rgba(255,255,255,0.78);
    margin-bottom: 12px;
}

div[data-testid="stChatInput"] {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    width: min(850px,calc(100vw - 40px));
    z-index: 999;
}

div[data-testid="stChatInput"] > div {
    border-radius: 22px !important;
    border: 1px solid rgba(184,63,212,0.30) !important;
    background: rgba(255,255,255,0.97) !important;
    box-shadow:
        0 12px 40px rgba(91,33,110,0.18) !important;
}


/* BUTTONS */

.stButton > button {
    border-radius: 14px !important;
    border: 1px solid rgba(184,63,212,0.20) !important;
    background: rgba(255,255,255,0.82) !important;
    font-weight: 650 !important;
}

.stButton > button:hover {
    border-color: #b83fd4 !important;
    transform: translateY(-1px);
}


/* MOBILE */

@media (max-width:768px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero {
        padding: 28px 24px;
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

""",
unsafe_allow_html=True
)

# =========================================================

# HERO

# =========================================================

st.markdown(
"""

<div class="hero">

```
<div class="hero-badge">
    ✨ AI-powered personal planning
</div>

<h1 class="hero-title">
    Daily Planner Agent
</h1>

<div class="hero-subtitle">
    Plan your day, organize tasks, manage your schedule,
    and get personalized daily guidance with your AI planner.
</div>
```

</div>
""",
    unsafe_allow_html=True
)

# =========================================================

# SIDEBAR

# =========================================================

with st.sidebar:

```
st.markdown("## ⚙️ Planner Settings")

st.caption(
    "Customize your daily planning preferences."
)

st.divider()

state = storage.load()

prayer_times = state.get(
    "prayer_times",
    {}
)

st.markdown("### 🕌 Prayer Times")

with st.form("prayer_form"):

    fajr = st.text_input(
        "Fajr",
        value=prayer_times.get(
            "Fajr",
            ""
        )
    )

    dhuhr = st.text_input(
        "Dhuhr",
        value=prayer_times.get(
            "Dhuhr",
            ""
        )
    )

    asr = st.text_input(
        "Asr",
        value=prayer_times.get(
            "Asr",
            ""
        )
    )

    maghrib = st.text_input(
        "Maghrib",
        value=prayer_times.get(
            "Maghrib",
            ""
        )
    )

    isha = st.text_input(
        "Isha",
        value=prayer_times.get(
            "Isha",
            ""
        )
    )

    save = st.form_submit_button(
        "Save Prayer Times",
        use_container_width=True
    )

    if save:

        storage.set_prayer_time(
            "Fajr",
            fajr
        )

        storage.set_prayer_time(
            "Dhuhr",
            dhuhr
        )

        storage.set_prayer_time(
            "Asr",
            asr
        )

        storage.set_prayer_time(
            "Maghrib",
            maghrib
        )

        storage.set_prayer_time(
            "Isha",
            isha
        )

        st.success(
            "Prayer times saved."
        )

        st.rerun()

st.divider()

if st.button(
    "Reset Planner Data",
    use_container_width=True
):

    storage.reset()

    st.session_state.messages = []

    st.success(
        "Planner data reset."
    )

    st.rerun()

st.divider()

st.caption(
    f"Model: {agent.MODEL}"
)

st.caption(
    "Daily Planner Agent"
)
```

# =========================================================

# DATA

# =========================================================

state = storage.load()

schedule = state.get(
"schedule",
[]
)

tasks = state.get(
"tasks",
[]
)

fixed_commitments = state.get(
"fixed_commitments",
[]
)

schedule_note = state.get(
"schedule_note",
""
)

# =========================================================

# TABS

# =========================================================

chat_tab, schedule_tab, tasks_tab = st.tabs(
[
"💬 Chat",
"📅 Schedule",
"✅ Tasks"
]
)

# =========================================================

# CHAT TAB

# =========================================================

with chat_tab:

```
st.markdown(
    "### ✨ What would you like to plan?"
)

st.caption(
    "Ask me to plan your day, organize tasks, "
    "adjust your schedule, or summarize your day."
)

col1, col2, col3 = st.columns(3)

with col1:

    if st.button(
        "📋 Plan My Day",
        use_container_width=True
    ):

        queue_prompt(
            "Plan my day based on my current tasks, "
            "commitments, prayer times, and schedule."
        )

        st.rerun()

with col2:

    if st.button(
        "🔄 Adjust My Plan",
        use_container_width=True
    ):

        queue_prompt(
            "Review my current plan and suggest useful "
            "adjustments to make my day more organized."
        )

        st.rerun()

with col3:

    if st.button(
        "📊 Day Summary",
        use_container_width=True
    ):

        queue_prompt(
            "Give me a summary of my current day, including "
            "completed tasks, remaining tasks, schedule, "
            "and useful suggestions."
        )

        st.rerun()

st.markdown("---")

for message in st.session_state.messages:

    avatar = (
        "🧑"
        if message["role"] == "user"
        else "🤖"
    )

    with st.chat_message(
        message["role"],
        avatar=avatar
    ):

        st.markdown(
            message["content"]
        )

        if message.get("trace"):

            with st.expander(
                "Agent details"
            ):

                st.code(
                    message["trace"]
                )
```

# =========================================================

# SCHEDULE TAB

# =========================================================

with schedule_tab:

```
st.markdown(
    "### 📅 Today's Schedule"
)

if schedule_note:

    st.info(
        schedule_note
    )

if schedule:

    for slot in schedule:

        st.markdown(
            make_schedule_card(slot),
            unsafe_allow_html=True
        )

else:

    st.markdown(
        """
```

<div class="schedule-card">

```
<div class="schedule-icon">
    🌸
</div>

<div>

    <div class="schedule-title">
        No schedule yet
    </div>

    <div class="schedule-detail">
        Ask the Daily Planner Agent to plan your day.
    </div>

</div>
```

</div>
""",
            unsafe_allow_html=True
        )

# =========================================================

# TASKS TAB

# =========================================================

with tasks_tab:

```
st.markdown(
    "### ✅ Today's Tasks"
)

completed = sum(
    1
    for task in tasks
    if task.get(
        "done",
        False
    )
)

total = len(tasks)

remaining = max(
    total - completed,
    0
)

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Total Tasks",
        total
    )

with col2:

    st.metric(
        "Completed",
        completed
    )

with col3:

    st.metric(
        "Remaining",
        remaining
    )

if total:

    st.progress(
        completed / total
    )

st.markdown("---")

if tasks:

    sorted_tasks = sorted(
        tasks,
        key=lambda task: (
            task.get(
                "done",
                False
            ),
            -int(
                task.get(
                    "priority",
                    0
                )
            )
        )
    )

    for index, task in enumerate(
        sorted_tasks
    ):

        task_id = task.get(
            "id",
            f"task_{index}"
        )

        title = task.get(
            "title",
            "Untitled task"
        )

        checked = task.get(
            "done",
            False
        )

        new_value = st.checkbox(
            title,
            value=checked,
            key=f"task_{task_id}"
        )

        if new_value != checked:

            toggle_task(
                task_id
            )

            st.rerun()

else:

    st.markdown(
        """
```

<div class="schedule-card">

```
<div class="schedule-icon">
    🌷
</div>

<div>

    <div class="schedule-title">
        No tasks yet
    </div>

    <div class="schedule-detail">
        Ask the Daily Planner Agent to create your plan.
    </div>

</div>
```

</div>
""",
            unsafe_allow_html=True
        )

# =========================================================

# CHAT INPUT

# =========================================================

user_prompt = st.chat_input(
"Message Daily Planner Agent..."
)

if st.session_state.pending_prompt is not None:

```
prompt = st.session_state.pending_prompt

st.session_state.pending_prompt = None

run_prompt(prompt)

st.rerun()
```

if user_prompt:

```
run_prompt(
    user_prompt
)

st.rerun()
```


