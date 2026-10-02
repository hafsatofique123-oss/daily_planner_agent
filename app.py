import html
import json
import os
from string import Template

import streamlit as st
from dotenv import load_dotenv
from groq import AuthenticationError, Groq, RateLimitError

import agent
import storage
import tools


# =========================================================
# APP CONFIGURATION
# =========================================================

load_dotenv()

st.set_page_config(
    page_title="Daily Planner Agent",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# ICONS
# =========================================================

ICONS = {
    "task": "📌",
    "fixed": "🏫",
    "prayer": "🕌",
    "meal": "🍽️",
    "break": "☕",
}

PRIORITY_ICON = {
    "high": "🔴",
    "medium": "🟡",
    "low": "🟢",
}


# =========================================================
# THEMES
# =========================================================

THEMES = {
    "🌸 Light Pink": {
        "bg1": "#fff7fb",
        "bg2": "#ffe7f1",
        "card": "#ffffff",
        "text": "#3f2634",
        "muted": "#987386",
        "accent": "#e8559a",
        "accent2": "#f58ab7",
        "soft": "#ffe0ec",
        "border": "#f5c5d9",
        "shadow": "rgba(232, 85, 154, 0.14)",
    },
    "💜 Light Purple": {
        "bg1": "#f8f5ff",
        "bg2": "#e9ddff",
        "card": "#ffffff",
        "text": "#30234a",
        "muted": "#7c6b9d",
        "accent": "#8b5cf6",
        "accent2": "#b18af7",
        "soft": "#e8dcff",
        "border": "#d6c5f7",
        "shadow": "rgba(139, 92, 246, 0.14)",
    },
}


# =========================================================
# MODERN CSS
# =========================================================

CSS = Template(
    """
<style>

/* =====================================================
   GLOBAL
   ===================================================== */

.stApp {
    background:
        radial-gradient(
            circle at 10% 10%,
            $soft 0%,
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 15%,
            $soft 0%,
            transparent 25%
        ),
        linear-gradient(
            145deg,
            $bg1 0%,
            $bg2 100%
        );

    color: $text;
}

.main .block-container {
    max-width: 1450px;
    padding-top: 1.5rem;
    padding-bottom: 5rem;
}

.stApp p,
.stApp li,
.stApp label,
.stApp span,
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4 {
    color: $text;
}

header[data-testid="stHeader"] {
    background: transparent;
}


/* =====================================================
   SIDEBAR
   ===================================================== */

section[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.90);
    border-right: 1px solid $border;
    backdrop-filter: blur(18px);
}

section[data-testid="stSidebar"] * {
    color: $text;
}

section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
}


/* =====================================================
   HERO
   ===================================================== */

.hero-wrapper {
    position: relative;
    overflow: hidden;

    background:
        linear-gradient(
            120deg,
            $accent 0%,
            $accent2 100%
        );

    border-radius: 26px;
    padding: 30px 34px;
    margin-bottom: 22px;

    box-shadow:
        0 15px 40px $shadow;
}

.hero-wrapper::before {
    content: "";

    position: absolute;

    width: 190px;
    height: 190px;

    border-radius: 50%;

    background: rgba(255, 255, 255, 0.13);

    right: -55px;
    top: -75px;
}

.hero-wrapper::after {
    content: "";

    position: absolute;

    width: 125px;
    height: 125px;

    border-radius: 50%;

    background: rgba(255, 255, 255, 0.10);

    right: 100px;
    bottom: -75px;
}

.hero-content {
    position: relative;
    z-index: 2;
}

.hero-title {
    font-size: 2.3rem;
    font-weight: 800;

    color: #ffffff !important;

    margin: 0;

    letter-spacing: -0.8px;
}

.hero-subtitle {
    color: rgba(255, 255, 255, 0.95) !important;

    font-size: 1rem;

    margin-top: 8px;

    max-width: 700px;
}

.hero-badge {
    display: inline-block;

    margin-top: 17px;

    padding: 7px 14px;

    border-radius: 999px;

    background: rgba(255, 255, 255, 0.18);

    color: white !important;

    font-size: 0.78rem;

    font-weight: 700;

    border: 1px solid rgba(255, 255, 255, 0.24);
}


/* =====================================================
   BUTTONS
   ===================================================== */

.stButton > button,
.stFormSubmitButton > button {

    min-height: 44px;

    border-radius: 14px;

    border: 1.5px solid $border;

    background: rgba(255, 255, 255, 0.92);

    color: $accent;

    font-weight: 700;

    transition:
        all 0.18s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {

    background: $accent;

    color: white !important;

    border-color: $accent;

    transform: translateY(-2px);

    box-shadow:
        0 8px 20px $shadow;
}

.stButton > button *,
.stFormSubmitButton > button * {
    color: inherit !important;
}


/* =====================================================
   QUICK ACTIONS
   ===================================================== */

.quick-action .stButton > button {

    min-height: 58px;

    border-radius: 17px;

    font-size: 0.9rem;

    background: rgba(255, 255, 255, 0.90);
}


/* =====================================================
   TABS
   ===================================================== */

button[data-baseweb="tab"] {

    border-radius: 13px 13px 0 0;

    font-weight: 700;

    padding: 11px 18px;
}

button[data-baseweb="tab"][aria-selected="true"] {

    color: $accent !important;
}

div[data-baseweb="tab-highlight"] {

    background-color: $accent !important;

    height: 3px;
}


/* =====================================================
   CHAT MESSAGES
   ===================================================== */

div[data-testid="stChatMessage"] {

    background: rgba(255, 255, 255, 0.90);

    border: 1px solid $border;

    border-radius: 20px;

    padding: 15px 18px;

    margin-bottom: 12px;

    box-shadow:
        0 5px 18px $shadow;
}

div[data-testid="stChatMessage"] p {

    line-height: 1.65;
}


/* =====================================================
   CHAT INPUT
   ===================================================== */

div[data-testid="stChatInput"] {

    position: fixed;

    bottom: 22px;

    left: 50%;

    transform: translateX(-50%);

    width: min(900px, 72%);

    z-index: 999;

    background: rgba(255, 255, 255, 0.97);

    border: 2px solid $accent2;

    border-radius: 23px;

    padding: 5px 8px;

    box-shadow:
        0 12px 38px rgba(0, 0, 0, 0.10),
        0 0 0 5px $shadow;

    backdrop-filter: blur(16px);
}

div[data-testid="stChatInput"] textarea {

    background: transparent !important;

    color: $text !important;

    font-size: 0.98rem;
}

div[data-testid="stChatInput"] textarea::placeholder {

    color: $muted !important;
}


/* =====================================================
   INPUTS
   ===================================================== */

input,
textarea {

    background: rgba(255, 255, 255, 0.94) !important;

    color: $text !important;

    border-radius: 13px !important;
}

div[data-baseweb="select"] > div {

    border-radius: 13px;
}


/* =====================================================
   EXPANDER
   ===================================================== */

div[data-testid="stExpander"] {

    background: rgba(255, 255, 255, 0.90);

    border: 1px solid $border;

    border-radius: 15px;
}


/* =====================================================
   ALERTS
   ===================================================== */

div[data-testid="stAlert"] {

    border-radius: 15px;
}


/* =====================================================
   RADIO
   ===================================================== */

div[role="radiogroup"] label {

    background: rgba(255, 255, 255, 0.78);

    border: 1.5px solid $border;

    border-radius: 999px;

    padding: 5px 14px;
}


/* =====================================================
   SECTION CARD
   ===================================================== */

.section-card {

    background: rgba(255, 255, 255, 0.84);

    border: 1px solid $border;

    border-radius: 20px;

    padding: 20px;

    margin-bottom: 18px;

    box-shadow:
        0 6px 22px $shadow;
}

.section-title {

    font-size: 1.08rem;

    font-weight: 800;

    margin-bottom: 4px;
}

.section-subtitle {

    font-size: 0.83rem;

    color: $muted !important;

    margin-bottom: 3px;
}


/* =====================================================
   SCHEDULE
   ===================================================== */

.slot {

    display: flex;

    gap: 16px;

    align-items: center;

    background: rgba(255, 255, 255, 0.93);

    border: 1px solid $border;

    border-left: 6px solid $accent;

    border-radius: 17px;

    padding: 14px 17px;

    margin-bottom: 10px;

    box-shadow:
        0 4px 14px $shadow;

    transition:
        transform 0.15s ease;
}

.slot:hover {

    transform: translateX(3px);
}

.slot .time {

    min-width: 120px;

    font-weight: 800;

    font-size: 0.82rem;

    color: $accent;
}

.slot .title {

    font-weight: 700;

    font-size: 0.94rem;
}

.slot .detail {

    font-size: 0.79rem;

    color: $muted !important;

    margin-top: 3px;
}

.slot.fixed {

    border-left-color: #5b9df0;

    background: #eef5ff;
}

.slot.prayer {

    border-left-color: #3fb58a;

    background: #ebf9f3;
}

.slot.meal {

    border-left-color: #f4a259;

    background: #fff3e6;
}

.slot.break {

    border-left-color: #aaaac7;

    background: #f5f5fb;
}

.slot.fixed .title,
.slot.prayer .title,
.slot.meal .title,
.slot.break .title {

    color: #333344;
}


/* =====================================================
   CHIPS
   ===================================================== */

.chip {

    display: inline-block;

    background: $soft;

    border: 1px solid $border;

    border-radius: 999px;

    padding: 5px 11px;

    font-size: 0.78rem;

    margin-right: 6px;

    color: $text;
}


/* =====================================================
   TASKS
   ===================================================== */

div[data-testid="stCheckbox"] {

    background: rgba(255, 255, 255, 0.76);

    border: 1px solid $border;

    border-radius: 14px;

    padding: 7px 12px;

    margin-bottom: 7px;
}


/* =====================================================
   PROGRESS
   ===================================================== */

div[data-testid="stProgress"] > div {

    border-radius: 999px;
}

div[data-testid="stProgress"] div[role="progressbar"] {

    background-color: $accent;
}


/* =====================================================
   MOBILE
   ===================================================== */

@media (max-width: 900px) {

    .main .block-container {

        padding-left: 1rem;

        padding-right: 1rem;
    }

    .hero-title {

        font-size: 1.7rem;
    }

    .hero-wrapper {

        padding: 23px;

        border-radius: 21px;
    }

    div[data-testid="stChatInput"] {

        width: 90%;

        bottom: 12px;
    }

    .slot {

        flex-direction: column;

        align-items: flex-start;

        gap: 4px;
    }

    .slot .time {

        min-width: auto;
    }
}

</style>
"""
)


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "theme_choice" not in st.session_state:
    st.session_state.theme_choice = "🌸 Light Pink"


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_api_key() -> str:

    return (
        st.session_state.get("api_key_input", "")
        or os.getenv("GROQ_API_KEY", "")
    ).strip()


def queue_prompt(text: str) -> None:

    st.session_state.pending_prompt = text


def toggle_task(task_id: int) -> None:

    tools.set_task_done(
        task_id,
        st.session_state.get(
            f"task_{task_id}",
            False,
        ),
    )


def run_prompt(text: str) -> None:

    key = get_api_key()

    st.session_state.messages.append(
        {
            "role": "user",
            "content": text,
        }
    )

    if not key:

        reply = (
            "Please add your Groq API key in the sidebar "
            "or set `GROQ_API_KEY` in your environment. 🔑"
        )

        trace = []

    else:

        history = [
            {
                "role": m["role"],
                "content": m["content"],
            }
            for m in st.session_state.messages[:-1]
        ]

        try:

            with st.spinner(
                "Your planner agent is thinking..."
            ):

                reply, trace = agent.run_agent(
                    Groq(api_key=key),
                    history,
                    text,
                )

        except AuthenticationError:

            reply = (
                "The Groq API key appears to be invalid. "
                "Please check your API key in the sidebar. 🔑"
            )

            trace = []

        except RateLimitError:

            reply = (
                "Groq rate limit reached. "
                "Please wait a little and try again. ⏳"
            )

            trace = []

        except Exception as exc:

            reply = (
                f"Something went wrong: "
                f"{type(exc).__name__}: {exc}"
            )

            trace = []

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply,
            "trace": trace,
        }
    )


def slot_html(b: dict) -> str:

    btype = (
        b.get("type")
        if b.get("type") in ICONS
        else "task"
    )

    detail = ""

    if b.get("detail"):

        detail = (
            f"<div class='detail'>"
            f"{html.escape(str(b['detail']))}"
            f"</div>"
        )

    return (
        f"<div class='slot {btype}'>"

        f"<div class='time'>"
        f"{html.escape(str(b.get('start', '')))}"
        f" – "
        f"{html.escape(str(b.get('end', '')))}"
        f"</div>"

        f"<div>"

        f"<div class='title'>"
        f"{ICONS[btype]} "
        f"{html.escape(str(b.get('title', '')))}"
        f"</div>"

        f"{detail}"

        f"</div>"

        f"</div>"
    )


# =========================================================
# THEME SELECTOR
# =========================================================

top_left, top_right = st.columns([4, 2])

with top_right:

    st.radio(
        "Theme",
        list(THEMES.keys()),
        key="theme_choice",
        horizontal=True,
        label_visibility="collapsed",
    )


theme = THEMES[st.session_state.theme_choice]

st.markdown(
    CSS.substitute(theme),
    unsafe_allow_html=True,
)


# =========================================================
# HERO HEADER
# =========================================================

st.markdown(
    """
    <div class="hero-wrapper">

        <div class="hero-content">

            <div class="hero-title">
                🗓️ Daily Planner Agent
            </div>

            <div class="hero-subtitle">
                Organize your tasks, manage your commitments,
                and let your AI planner structure your day.
            </div>

            <div class="hero-badge">
                ✨ AI-Powered Daily Planning
            </div>

        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## ⚙️ Settings")

    st.caption(
        "Configure your planner agent and daily preferences."
    )

    st.text_input(
        "Groq API Key",
        type="password",
        key="api_key_input",
        placeholder="Enter your Groq API key",
        help=(
            "You can also set GROQ_API_KEY "
            "as an environment variable."
        ),
    )

    if get_api_key():

        st.success("API key detected ✅")

    else:

        st.warning("Groq API key required")

    st.caption(
        f"Model: `{agent.MODEL}`"
    )

    st.divider()

    st.markdown("### 🕌 Prayer Times")

    st.caption(
        "Set your daily prayer times using 24-hour format."
    )

    prayers = storage.load()["prayer_times"]

    with st.form("prayer_form"):

        new_times = {
            name: st.text_input(
                name,
                value=time,
            )
            for name, time in prayers.items()
        }

        if st.form_submit_button(
            "Save Prayer Times",
            use_container_width=True,
        ):

            for name, value in new_times.items():

                result = tools.execute_tool(
                    "set_prayer_time",
                    {
                        "name": name,
                        "time": value,
                    },
                )

                if "error" in result:

                    st.error(
                        f"{name}: {result['error']}"
                    )

            st.rerun()

    st.divider()

    if st.button(
        "🗑️ Reset All Data",
        use_container_width=True,
    ):

        storage.reset()

        st.session_state.messages = []

        st.rerun()


# =========================================================
# LOAD APP DATA
# =========================================================

state = storage.load()


# =========================================================
# MAIN TABS
# =========================================================

tab_chat, tab_plan, tab_tasks = st.tabs(
    [
        "💬 AI Chat",
        "📅 Daily Schedule",
        "✅ Tasks",
    ]
)


# =========================================================
# AI CHAT TAB
# =========================================================

with tab_chat:

    st.markdown(
        """
        <div class="section-card">

            <div class="section-title">
                🤖 Your AI Planning Assistant
            </div>

            <div class="section-subtitle">
                Tell the agent what you need to do,
                then ask it to organize or adjust your day.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ⚡ Quick Actions")

    qa1, qa2, qa3 = st.columns(3)

    with qa1:

        st.markdown(
            '<div class="quick-action">',
            unsafe_allow_html=True,
        )

        st.button(
            "📅 Plan My Day",
            use_container_width=True,
            on_click=queue_prompt,
            args=(
                "Look at my tasks and commitments, "
                "create a complete plan for today, "
                "and save it.",
            ),
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    with qa2:

        st.markdown(
            '<div class="quick-action">',
            unsafe_allow_html=True,
        )

        st.button(
            "🔄 Adjust My Plan",
            use_container_width=True,
            on_click=queue_prompt,
            args=(
                "Based on the current time, "
                "re-plan the remaining part of my day.",
            ),
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    with qa3:

        st.markdown(
            '<div class="quick-action">',
            unsafe_allow_html=True,
        )

        st.button(
            "🌙 Day Summary",
            use_container_width=True,
            on_click=queue_prompt,
            args=(
                "Give me today's summary: "
                "what is completed and what is still remaining.",
            ),
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    if not st.session_state.messages:

        st.info(
            "💡 Example: "
            "\"I have a 2-hour assignment, "
            "a 1-hour gym session, and a 15-minute call. "
            "My class is from 9 AM to 1 PM.\" "
            "Then click **Plan My Day**."
        )

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(
                message["content"]
            )

            if message.get("trace"):

                with st.expander(
                    f"🔧 Agent used "
                    f"{len(message['trace'])} tool call(s)"
                ):

                    for tool_call in message["trace"]:

                        st.markdown(
                            f"**{tool_call['name']}** "
                            f"`{json.dumps(tool_call['args'], ensure_ascii=False)[:300]}`"
                        )

                        st.caption(
                            json.dumps(
                                tool_call["result"],
                                ensure_ascii=False,
                            )[:400]
                        )


# =========================================================
# DAILY SCHEDULE TAB
# =========================================================

with tab_plan:

    if not state["schedule"]:

        st.info(
            "📅 No schedule has been created yet. "
            "Go to **AI Chat** and click **Plan My Day**."
        )

    else:

        if state["schedule_note"]:

            st.success(
                state["schedule_note"]
            )

        st.markdown(
            f"""
            <div class="section-card">

                <div class="section-title">
                    📅 Today's Schedule
                </div>

                <div class="section-subtitle">
                    Date: {html.escape(str(state["schedule_date"]))}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "".join(
                slot_html(block)
                for block in state["schedule"]
            ),
            unsafe_allow_html=True,
        )


# =========================================================
# TASKS TAB
# =========================================================

with tab_tasks:

    done = sum(
        1
        for task in state["tasks"]
        if task["done"]
    )

    total = len(state["tasks"])

    st.markdown(
        """
        <div class="section-card">

            <div class="section-title">
                ✅ Task Manager
            </div>

            <div class="section-subtitle">
                Track your tasks and monitor your daily progress.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    if total:

        st.progress(
            done / total,
            text=f"{done} of {total} tasks completed",
        )

    else:

        st.caption(
            "No tasks yet. Tell your AI planner "
            "what you need to accomplish."
        )

    st.markdown("### 📌 My Tasks")

    for task in sorted(
        state["tasks"],
        key=lambda x: (
            x["done"],
            tools.PRIORITY_ORDER[x["priority"]],
        ),
    ):

        st.checkbox(
            (
                f"{PRIORITY_ICON[task['priority']]} "
                f"{task['title']} "
                f"({task['estimated_minutes']} min)"
            ),
            value=task["done"],
            key=f"task_{task['id']}",
            on_change=toggle_task,
            args=(task["id"],),
        )

    st.markdown("### 🏫 Fixed Commitments")

    if not state["commitments"]:

        st.caption(
            "No fixed commitments added yet."
        )

    else:

        for commitment in sorted(
            state["commitments"],
            key=lambda x: x["start"],
        ):

            st.markdown(
                f"""
                <div style="margin-bottom:10px;">

                    <span class="chip">
                        {html.escape(str(commitment["start"]))}
                        –
                        {html.escape(str(commitment["end"]))}
                    </span>

                    <strong>
                        {html.escape(str(commitment["title"]))}
                    </strong>

                </div>
                """,
                unsafe_allow_html=True,
            )


# =========================================================
# CHAT INPUT
# =========================================================

user_text = st.chat_input(
    "✨ Ask your planner anything..."
)

pending = st.session_state.pop(
    "pending_prompt",
    None,
)

if user_text or pending:

    run_prompt(
        user_text or pending
    )

    st.rerun()


