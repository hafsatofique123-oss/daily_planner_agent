"""The planner agent: an LLM (Groq) that decides which tools to call in a loop."""
import json

from groq import APIError, BadRequestError

import tools

MODEL = "openai/gpt-oss-120b"
MAX_STEPS = 12
MAX_RETRIES = 3


def build_system_prompt() -> str:
    now = tools.now_local()
    return f"""Tum "Planner", ek friendly personal Daily Planner Agent ho. User se Roman Urdu + English mix mein baat karo (jaise user likhe), chhote aur saaf jawab do.

Abhi: {now.strftime('%A, %Y-%m-%d')} ka waqt {now.strftime('%H:%M')} (Pakistan time).

Tumhare paas tools hain jo user ke tasks, fixed commitments, namaz times aur schedule manage karte hain. Apni memory par bharosa mat karo: hamesha tools se data lo.

Kaam ka tareeqa:
1. User task/commitment bataye to add_task / add_commitment call karo (ek message mein kai items ho to sab add karo). Time hamesha 24-hour HH:MM mein bhejo (e.g. "3 baje" dopahar = 15:00).
2. Plan banane se pehle list_tasks, list_commitments, get_prayer_times aur get_current_datetime call karo.
3. Schedule 07:00 se 22:00 ke beech banao. Rules:
   - Har fixed commitment (type "fixed") aur har namaz (type "prayer", {tools.PRAYER_MINUTES} min) schedule mein shamil karo, unka time na badlo. Agar namaz ka waqt kisi fixed commitment ke andar aa jaye to namaz ka block commitment ke foran baad rakho.
   - Sabse zaroori (high priority) aur mushkil kaam pehle, khaali waqt mein.
   - Breakfast, lunch, dinner (type "meal") aur chhote breaks (type "break", 5-15 min) rakho.
   - Task blocks mein task_id zaroor do. Agar aaj ka waqt guzar chuka hai to sirf bacha hua waqt plan karo.
   - Jo tasks fit na hon unhein kal ke liye suggest karo, aur overload par honestly batao.
4. Plan ko save_schedule se save karo. Agar errors aayein to unhein theek karke dobara call karo, jab tak saved=true na ho.
5. Jab user kahe "meeting aa gayi" ya plan badalna ho: pehle add_commitment (agar zaroorat ho), phir naya poora schedule save_schedule se save karo.
6. Task mukammal ho jaye to complete_task call karo.
Aakhir mein user ko chhota summary do (kya hua, din ke main blocks, koi warning). Poora schedule dobara text mein mat likho, wo app mein dikh jata hai.
Sirf wahi karo jo tools se mumkin hai; tools ke bina "ho gaya" mat kaho."""


def _chat(client, messages):
    last_error = None
    for _ in range(MAX_RETRIES):
        try:
            return client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools.TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
            )
        except BadRequestError as exc:
            # gpt-oss occasionally emits a malformed tool call; a retry usually fixes it
            last_error = exc
        except APIError:
            raise
    raise last_error


def run_agent(client, history: list, user_message: str, max_steps: int = MAX_STEPS):
    """Run the tool-calling loop. Returns (reply_text, trace)."""
    messages = [{"role": "system", "content": build_system_prompt()}]
    messages += history[-12:]
    messages.append({"role": "user", "content": user_message})
    trace = []

    for _ in range(max_steps):
        response = _chat(client, messages)
        msg = response.choices[0].message
        calls = msg.tool_calls or []

        if not calls:
            return (msg.content or "").strip() or "Ho gaya!", trace

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [{"id": c.id, "type": "function",
                            "function": {"name": c.function.name,
                                         "arguments": c.function.arguments or "{}"}}
                           for c in calls],
        })
        for call in calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
                result = tools.execute_tool(name, args)
            except json.JSONDecodeError:
                args, result = {}, {"error": "Arguments were not valid JSON"}
            trace.append({"name": name, "args": args, "result": result})
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": json.dumps(result, ensure_ascii=False)})

    return ("Maaf kijiye, kaam mukammal karne mein zyada steps lag gaye. "
            "Dobara try karo ya request ko chhota karke bhejo."), trace
