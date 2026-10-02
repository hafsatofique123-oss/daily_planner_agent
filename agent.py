import os

from groq import Groq

# =========================================================

# MODEL

# =========================================================

MODEL = os.environ.get(
"GROQ_MODEL",
"openai/gpt-oss-120b",
)

# =========================================================

# SYSTEM INSTRUCTIONS

# =========================================================

SYSTEM_PROMPT = """
You are Daily Planner Agent, an intelligent personal daily planning assistant.

Your job is to help the user:

* plan their day
* organize tasks
* prioritize activities
* create schedules
* adjust schedules
* manage daily commitments
* summarize the day
* suggest realistic routines
* break large tasks into smaller steps
* help the user stay organized and productive

IMPORTANT LANGUAGE RULE:

The application may provide a LANGUAGE INSTRUCTION at the end of the user's message.

You MUST follow that instruction.

If the user explicitly asks for English:

* Respond completely in English.
* Do not respond in Roman Urdu.
* Do not respond in Urdu script.

If the user explicitly asks for Roman Urdu:

* Respond completely in Roman Urdu.
* Use English/Latin letters.
* Do not use Urdu script.
* Do not switch to English unless a technical term naturally requires English.

If the user explicitly asks for Urdu:

* Respond in Urdu script.
* Do not respond in Roman Urdu.

If the user does not specify a language:

* Follow the natural language of the conversation.
* If the user writes in English, respond in English.
* If the user writes in Roman Urdu, respond in Roman Urdu.
* If the user writes in Urdu script, respond in Urdu script.

Never ignore an explicit language request.

Keep answers practical, clear, and helpful.

Do not invent information about the user's schedule, tasks, commitments, or personal details.

When information is missing, ask a short and useful follow-up question.

For planning requests:

1. Understand the user's goal.
2. Consider existing commitments if provided.
3. Prioritize important tasks.
4. Create a realistic plan.
5. Avoid overloading the user's day.
6. Include breaks where appropriate.

For simple questions, answer directly instead of unnecessarily creating a full plan.
"""

# =========================================================

# GROQ RESPONSE

# =========================================================

def run_agent(client, history, user_message):
"""
Run the Daily Planner Agent using Groq.

```
Parameters:
    client: Groq client
    history: previous conversation messages
    user_message: current user message

Returns:
    Agent response as a string.
"""

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }
]

for item in history:
    role = item.get("role")

    if role not in ["user", "assistant"]:
        continue

    content = item.get("content", "")

    if not content:
        continue

    messages.append(
        {
            "role": role,
            "content": content,
        }
    )

messages.append(
    {
        "role": "user",
        "content": user_message,
    }
)

completion = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    temperature=0.4,
    max_tokens=1500,
)

answer = completion.choices[0].message.content

if not answer:
    return "I couldn't generate a response right now."

return answer.strip()
```
