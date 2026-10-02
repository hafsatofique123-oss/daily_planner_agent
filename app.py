"""Daily Planner Agent - Streamlit UI.  Run:  streamlit run app.py"""
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

load_dotenv()
st.set_page_config(page_title="Daily Planner Agent", page_icon="🗓️", layout="centered")

ICONS = {"task": "📌", "fixed": "🏫", "prayer": "🕌", "meal": "🍽️", "break": "☕"}
PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}

# ---------- themes (light pink / light purple) ----------
THEMES = {
    "🌸 Light Pink": {
        "bg1": "#fff4f9", "bg2": "#ffe3ef", "card": "#ffffff", "text": "#4a2038",
        "muted": "#9a6b84", "accent": "#e8559a", "accent2": "#f78fb8", "soft": "#ffd6e7",
        "border": "#f7c6dc",
    },
    "💜 Light Purple": {
        "bg1": "#f6f1ff", "bg2": "#e8dcff", "card": "#ffffff", "text": "#2e1f4d",
        "muted": "#7a6a9c", "accent": "#8b5cf6", "accent2": "#b794f6", "soft": "#e4d7ff",
        "border": "#d5c3fb",
    },
}

CSS = Template("""
<style>
.stApp { background: linear-gradient(160deg, $bg1 0%, $bg2 100%); color: $text; }
.stApp p, .stApp li, .stApp label, .stApp span, .stApp h1, .stApp h2, .stApp h3,
.stApp h4, .stApp div[data-testid="stMarkdownContainer"] { color: $text; }
header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { background: $card; border-right: 1px solid $border; }
section[data-testid="stSidebar"] * { color: $text; }

.hero { background: linear-gradient(120deg, $accent, $accent2); border-radius: 20px;
  padding: 20px 22px; margin-bottom: 8px; box-shadow: 0 8px 24px $border; }
.hero h1 { margin: 0; font-size: 1.6rem; color: #fff !important; }
.hero p { margin: 4px 0 0; color: #fff !important; opacity: .92; font-size: .95rem; }

.stButton > button, .stFormSubmitButton > button { background: $card; color: $accent;
  border: 1.5px solid $accent2; border-radius: 14px; font-weight: 600; transition: all .15s; }
.stButton > button:hover, .stFormSubmitButton > button:hover { background: $accent;
  color: #fff; border-color: $accent; transform: translateY(-1px); box-shadow: 0 4px 12px $border; }
.stButton > button *, .stFormSubmitButton > button * { color: inherit !important; }

button[data-baseweb="tab"] { border-radius: 12px 12px 0 0; font-weight: 600; }
button[data-baseweb="tab"][aria-selected="true"] { color: $accent !important; }
div[data-baseweb="tab-highlight"] { background-color: $accent !important; }

div[data-testid="stChatMessage"] { background: $card; border: 1px solid $border;
  border-radius: 16px; padding: 12px; box-shadow: 0 2px 10px $soft; }
div[data-testid="stChatInput"] { border-radius: 16px; border: 1.5px solid $accent2; }
div[data-testid="stChatInput"] textarea { background: $card; color: $text; }
input, textarea { background: $card !important; color: $text !important; }
div[data-testid="stExpander"] { background: $card; border: 1px solid $border; border-radius: 12px; }
div[data-testid="stAlert"] { border-radius: 14px; }
div[role="radiogroup"] label { background: $card; border: 1.5px solid $border;
  border-radius: 999px; padding: 4px 14px; }

.slot { display: flex; gap: 12px; background: $card; border: 1px solid $border;
  border-left: 6px solid $accent; border-radius: 14px; padding: 10px 14px; margin-bottom: 8px;
  box-shadow: 0 2px 8px $soft; }
.slot .time { min-width: 108px; font-weight: 700; font-size: .85rem; color: $accent; }
.slot .title { font-weight: 600; }
.slot .detail { font-size: .8rem; color: $muted; }
.slot.fixed { border-left-color: #5b9df0; background: #eef5ff; }
.slot.prayer { border-left-color: #3fb58a; background: #ebf9f3; }
.slot.meal { border-left-color: #f4a259; background: #fff3e6; }
.slot.break { border-left-color: #b7b7d0; background: #f4f4fb; }
.slot.fixed .title, .slot.prayer .title, .slot.meal .title, .slot.break .title { color: #333344; }
.chip { display: inline-block; background: $soft; border-radius: 999px; padding: 2px 10px;
  font-size: .8rem; margin-right: 6px; color: $text; }
</style>
""")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "theme_choice" not in st.session_state:
    st.session_state.theme_choice = "🌸 Light Pink"


# ---------- helpers ----------
def get_api_key() -> str:
    return (st.session_state.get("api_key_input", "") or os.getenv("GROQ_API_KEY", "")).strip()


def queue_prompt(text: str) -> None:
    st.session_state.pending_prompt = text


def toggle_task(task_id: int) -> None:
    tools.set_task_done(task_id, st.session_state.get(f"task_{task_id}", False))


def run_prompt(text: str) -> None:
    key = get_api_key()
    st.session_state.messages.append({"role": "user", "content": text})
    if not key:
        reply, trace = "Pehle sidebar mein apni Groq API key daalo (ya .env file mein set karo). 🔑", []
    else:
        history = [{"role": m["role"], "content": m["content"]}
                   for m in st.session_state.messages[:-1]]
        try:
            with st.spinner("Agent soch raha hai aur tools chala raha hai..."):
                reply, trace = agent.run_agent(Groq(api_key=key), history, text)
        except AuthenticationError:
            reply, trace = "API key sahi nahi lagti. Sidebar mein check karo. 🔑", []
        except RateLimitError:
            reply, trace = "Groq ki rate limit lag gayi hai. Thori der baad dobara try karo. ⏳", []
        except Exception as exc:
            reply, trace = f"Kuch masla aa gaya: {type(exc).__name__}: {exc}", []
    st.session_state.messages.append({"role": "assistant", "content": reply, "trace": trace})


def slot_html(b: dict) -> str:
    btype = b["type"] if b["type"] in ICONS else "task"
    detail = f"<div class='detail'>{html.escape(b['detail'])}</div>" if b.get("detail") else ""
    return (f"<div class='slot {btype}'><div class='time'>{html.escape(b['start'])} – "
            f"{html.escape(b['end'])}</div><div><div class='title'>{ICONS[btype]} "
            f"{html.escape(b['title'])}</div>{detail}</div></div>")


# ---------- header + theme switch ----------
head_l, head_r = st.columns([3, 2])
with head_r:
    st.radio("Theme", list(THEMES), key="theme_choice", horizontal=True,
             label_visibility="collapsed")
st.markdown(CSS.substitute(THEMES[st.session_state.theme_choice]), unsafe_allow_html=True)
st.markdown("<div class='hero'><h1>🗓️ Daily Planner Agent</h1>"
            "<p>Tasks batao, plan banwao, aur din mein jab marzi badlao ✨</p></div>",
            unsafe_allow_html=True)

# ---------- sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")
    st.text_input("Groq API key", type="password", key="api_key_input",
                  help="Ya project folder ki .env file mein GROQ_API_KEY set karo.")
    if get_api_key():
        st.success("API key mil gayi ✅")
    else:
        st.warning("API key chahiye")
    st.caption(f"Model: `{agent.MODEL}`")

    st.subheader("🕌 Namaz times (24h)")
    prayers = storage.load()["prayer_times"]
    with st.form("prayer_form"):
        new_times = {n: st.text_input(n, value=t) for n, t in prayers.items()}
        if st.form_submit_button("Save namaz times"):
            for name, value in new_times.items():
                result = tools.execute_tool("set_prayer_time", {"name": name, "time": value})
                if "error" in result:
                    st.error(f"{name}: {result['error']}")
            st.rerun()

    st.divider()
    if st.button("🗑️ Saara data reset karo"):
        storage.reset()
        st.session_state.messages = []
        st.rerun()

# ---------- main ----------
state = storage.load()
tab_chat, tab_plan, tab_tasks = st.tabs(["💬 Chat", "📅 Schedule", "✅ Tasks"])

with tab_chat:
    c1, c2, c3 = st.columns(3)
    c1.button("📅 Plan my day", use_container_width=True, on_click=queue_prompt,
              args=("Mere tasks aur commitments dekh kar aaj ka poora plan banao aur save karo.",))
    c2.button("🔄 Plan adjust", use_container_width=True, on_click=queue_prompt,
              args=("Abhi ke waqt ke hisaab se bacha hua din dobara plan karo.",))
    c3.button("🌙 Din ka summary", use_container_width=True, on_click=queue_prompt,
              args=("Aaj ka summary do: kya complete hua aur kya baqi hai.",))

    if not st.session_state.messages:
        st.info("Misal: *\"Assignment 2 ghante, gym 1 ghanta, ammi ko call 15 min. "
                "Class 9 se 1 baje hai.\"* phir *\"Plan my day\"* dabao.")
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("trace"):
                with st.expander(f"🔧 Agent ne {len(m['trace'])} tool call(s) kiye"):
                    for t in m["trace"]:
                        st.markdown(f"**{t['name']}** `{json.dumps(t['args'], ensure_ascii=False)[:300]}`")
                        st.caption(json.dumps(t["result"], ensure_ascii=False)[:400])

with tab_plan:
    if not state["schedule"]:
        st.info("Abhi koi schedule nahi hai. Chat mein \"Plan my day\" dabao.")
    else:
        if state["schedule_note"]:
            st.success(state["schedule_note"])
        st.caption(f"Date: {state['schedule_date']}")
        st.markdown("".join(slot_html(b) for b in state["schedule"]), unsafe_allow_html=True)

with tab_tasks:
    done = sum(1 for t in state["tasks"] if t["done"])
    total = len(state["tasks"])
    st.subheader("Tasks")
    if total:
        st.progress(done / total, text=f"{done}/{total} complete")
    else:
        st.caption("Koi task nahi. Chat mein agent ko batao.")
    for t in sorted(state["tasks"], key=lambda x: (x["done"], tools.PRIORITY_ORDER[x["priority"]])):
        st.checkbox(f"{PRIORITY_ICON[t['priority']]} {t['title']} ({t['estimated_minutes']} min)",
                    value=t["done"], key=f"task_{t['id']}", on_change=toggle_task, args=(t["id"],))
    st.subheader("Fixed commitments")
    if not state["commitments"]:
        st.caption("Koi commitment nahi.")
    for c in sorted(state["commitments"], key=lambda x: x["start"]):
        st.markdown(f"<span class='chip'>{html.escape(c['start'])} – {html.escape(c['end'])}</span> "
                    f"{html.escape(c['title'])}", unsafe_allow_html=True)

user_text = st.chat_input("Apna message likho...")
pending = st.session_state.pop("pending_prompt", None)
if user_text or pending:
    run_prompt(user_text or pending)
    st.rerun()
