"""Tools the agent can call. Every tool returns a JSON-serializable dict."""
import re
from datetime import datetime

import storage

DAY_START = 7 * 60    # 07:00
DAY_END = 22 * 60     # 22:00
PRAYER_MINUTES = 15
BLOCK_TYPES = ("task", "fixed", "prayer", "meal", "break")
PRIORITIES = ("high", "medium", "low")
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")


# ---------- helpers ----------
def now_local() -> datetime:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Karachi"))
    except Exception:
        return datetime.now()


def _to_min(value) -> int:
    if not isinstance(value, str) or not TIME_RE.match(value.strip()):
        raise ValueError(f"Invalid time '{value}'. Use 24-hour HH:MM, e.g. 14:30")
    h, m = (int(x) for x in value.strip().split(":"))
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError(f"Invalid time '{value}'. Use 24-hour HH:MM, e.g. 14:30")
    return h * 60 + m


def _fmt(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _priority(value) -> str:
    value = str(value or "medium").strip().lower()
    if value not in PRIORITIES:
        raise ValueError("priority must be one of: high, medium, low")
    return value


def _minutes(value, default=30) -> int:
    if value is None or value == "":
        return default
    try:
        value = int(float(value))
    except (TypeError, ValueError):
        raise ValueError("estimated_minutes must be a number")
    if value <= 0 or value > 720:
        raise ValueError("estimated_minutes must be between 1 and 720")
    return value


def _find(items: list, item_id) -> dict:
    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        raise ValueError("id must be a number")
    for item in items:
        if item["id"] == item_id:
            return item
    raise ValueError(f"No item found with id {item_id}")


# ---------- tools ----------
def get_current_datetime() -> dict:
    now = now_local()
    return {"date": now.strftime("%Y-%m-%d"), "weekday": now.strftime("%A"),
            "time_24h": now.strftime("%H:%M")}


def add_task(title: str, estimated_minutes=30, priority="medium") -> dict:
    title = str(title or "").strip()
    if not title:
        raise ValueError("title is required")
    state = storage.load()
    task = {"id": state["next_id"], "title": title,
            "estimated_minutes": _minutes(estimated_minutes),
            "priority": _priority(priority), "done": False}
    state["next_id"] += 1
    state["tasks"].append(task)
    storage.save(state)
    return {"added": task}


def list_tasks() -> dict:
    tasks = storage.load()["tasks"]
    tasks = sorted(tasks, key=lambda t: (t["done"], PRIORITY_ORDER[t["priority"]]))
    return {"tasks": tasks, "pending_count": sum(1 for t in tasks if not t["done"])}


def update_task(task_id, title=None, estimated_minutes=None, priority=None) -> dict:
    state = storage.load()
    task = _find(state["tasks"], task_id)
    if title is not None and str(title).strip():
        task["title"] = str(title).strip()
    if estimated_minutes is not None:
        task["estimated_minutes"] = _minutes(estimated_minutes)
    if priority is not None:
        task["priority"] = _priority(priority)
    storage.save(state)
    return {"updated": task}


def set_task_done(task_id, done: bool = True) -> dict:
    state = storage.load()
    task = _find(state["tasks"], task_id)
    task["done"] = bool(done)
    storage.save(state)
    return {"task": task}


def complete_task(task_id) -> dict:
    return set_task_done(task_id, True)


def delete_task(task_id) -> dict:
    state = storage.load()
    task = _find(state["tasks"], task_id)
    state["tasks"].remove(task)
    storage.save(state)
    return {"deleted": task}


def add_commitment(title: str, start: str, end: str) -> dict:
    title = str(title or "").strip()
    if not title:
        raise ValueError("title is required")
    s, e = _to_min(start), _to_min(end)
    if e <= s:
        raise ValueError("end must be after start")
    state = storage.load()
    item = {"id": state["next_id"], "title": title, "start": _fmt(s), "end": _fmt(e)}
    state["next_id"] += 1
    state["commitments"].append(item)
    storage.save(state)
    return {"added": item}


def list_commitments() -> dict:
    items = sorted(storage.load()["commitments"], key=lambda c: c["start"])
    return {"commitments": items}


def delete_commitment(commitment_id) -> dict:
    state = storage.load()
    item = _find(state["commitments"], commitment_id)
    state["commitments"].remove(item)
    storage.save(state)
    return {"deleted": item}


def get_prayer_times() -> dict:
    return {"prayer_times": storage.load()["prayer_times"],
            "note": f"Har namaz ke liye {PRAYER_MINUTES} minute ka block rakho."}


def set_prayer_time(name: str, time: str) -> dict:
    state = storage.load()
    key = str(name or "").strip().capitalize()
    if key not in state["prayer_times"]:
        raise ValueError(f"name must be one of: {', '.join(state['prayer_times'])}")
    state["prayer_times"][key] = _fmt(_to_min(time))
    storage.save(state)
    return {"prayer_times": state["prayer_times"]}


def get_schedule() -> dict:
    state = storage.load()
    return {"date": state["schedule_date"], "note": state["schedule_note"],
            "schedule": state["schedule"]}


def _overlap(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


def save_schedule(blocks: list, note: str = "") -> dict:
    """Validate and save the full day schedule. Returns errors if invalid so the
    agent can fix its plan and call this tool again."""
    if not isinstance(blocks, list) or not blocks:
        raise ValueError("blocks must be a non-empty list")
    state = storage.load()

    clean = []
    for i, b in enumerate(blocks):
        if not isinstance(b, dict):
            raise ValueError(f"Block {i} must be an object")
        title = str(b.get("title", "")).strip()
        if not title:
            raise ValueError(f"Block {i} has no title")
        s, e = _to_min(b.get("start")), _to_min(b.get("end"))
        if e <= s:
            raise ValueError(f"Block '{title}': end must be after start")
        if s < DAY_START or e > DAY_END:
            raise ValueError(f"Block '{title}' is outside 07:00-22:00")
        btype = str(b.get("type", "task")).strip().lower()
        if btype not in BLOCK_TYPES:
            raise ValueError(f"Block '{title}': type must be one of {', '.join(BLOCK_TYPES)}")
        task_id = b.get("task_id")
        try:
            task_id = int(task_id) if task_id not in (None, "") else None
        except (TypeError, ValueError):
            task_id = None
        clean.append({"start": _fmt(s), "end": _fmt(e), "title": title, "type": btype,
                      "detail": str(b.get("detail", "") or "").strip(), "task_id": task_id})
    clean.sort(key=lambda x: _to_min(x["start"]))

    problems = []
    # 1) no overlaps between blocks
    for a, b in zip(clean, clean[1:]):
        if _to_min(b["start"]) < _to_min(a["end"]):
            problems.append(f"'{a['title']}' ({a['start']}-{a['end']}) overlaps "
                            f"'{b['title']}' ({b['start']}-{b['end']})")

    # 2) fixed commitments and prayers must be present and untouched
    protected = []
    for c in state["commitments"]:
        protected.append((c["title"], _to_min(c["start"]), _to_min(c["end"]), "fixed"))
    for name, t in state["prayer_times"].items():
        s = _to_min(t)
        protected.append((name, s, s + PRAYER_MINUTES, "prayer"))

    fixed_spans = [(_to_min(c["start"]), _to_min(c["end"])) for c in state["commitments"]]
    for name, ps, pe, kind in protected:
        if ps < DAY_START or pe > DAY_END:
            continue  # outside the planning window
        if kind == "prayer" and any(_overlap(ps, pe, fs, fe) for fs, fe in fixed_spans):
            continue  # prayer falls inside a class/meeting: pray right after it instead
        covering = [b for b in clean if b["type"] == kind
                    and _overlap(_to_min(b["start"]), _to_min(b["end"]), ps, pe)]
        if not covering:
            problems.append(f"Missing {kind} block for '{name}' at {_fmt(ps)}-{_fmt(pe)} "
                            f"(add a block of type '{kind}')")
        for b in clean:
            if b["type"] not in ("fixed", "prayer") and _overlap(
                    _to_min(b["start"]), _to_min(b["end"]), ps, pe):
                problems.append(f"'{b['title']}' ({b['start']}-{b['end']}) clashes with "
                                f"{kind} '{name}' ({_fmt(ps)}-{_fmt(pe)})")

    if problems:
        return {"saved": False, "errors": problems,
                "hint": "Fix these problems and call save_schedule again with the full corrected list."}

    state["schedule"] = clean
    state["schedule_note"] = str(note or "").strip()
    state["schedule_date"] = now_local().strftime("%Y-%m-%d")
    storage.save(state)

    scheduled_ids = {b["task_id"] for b in clean if b["task_id"] is not None}
    left_out = [{"id": t["id"], "title": t["title"]} for t in state["tasks"]
                if not t["done"] and t["id"] not in scheduled_ids]
    result = {"saved": True, "blocks_saved": len(clean)}
    if left_out:
        result["pending_tasks_not_scheduled"] = left_out
        result["hint"] = "In tasks ko schedule nahi kiya gaya; user ko batao ya agar jagah hai to add karo."
    return result


# ---------- registry + schemas ----------
TOOL_FUNCS = {
    "get_current_datetime": get_current_datetime,
    "add_task": add_task,
    "list_tasks": list_tasks,
    "update_task": update_task,
    "complete_task": complete_task,
    "delete_task": delete_task,
    "add_commitment": add_commitment,
    "list_commitments": list_commitments,
    "delete_commitment": delete_commitment,
    "get_prayer_times": get_prayer_times,
    "set_prayer_time": set_prayer_time,
    "get_schedule": get_schedule,
    "save_schedule": save_schedule,
}


def _fn(name, description, properties=None, required=None):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties or {},
                       "required": required or []}}}


TOOL_SCHEMAS = [
    _fn("get_current_datetime", "Get today's date, weekday and current local time."),
    _fn("add_task", "Add a new task to the user's to-do list.",
        {"title": {"type": "string"},
         "estimated_minutes": {"type": "integer", "description": "Estimated duration in minutes"},
         "priority": {"type": "string", "enum": list(PRIORITIES)}}, ["title"]),
    _fn("list_tasks", "List all tasks with id, priority, duration and done status."),
    _fn("update_task", "Edit an existing task's title, duration or priority.",
        {"task_id": {"type": "integer"}, "title": {"type": "string"},
         "estimated_minutes": {"type": "integer"},
         "priority": {"type": "string", "enum": list(PRIORITIES)}}, ["task_id"]),
    _fn("complete_task", "Mark a task as done.", {"task_id": {"type": "integer"}}, ["task_id"]),
    _fn("delete_task", "Delete a task.", {"task_id": {"type": "integer"}}, ["task_id"]),
    _fn("add_commitment", "Add a fixed commitment (class, meeting...) with 24-hour HH:MM times.",
        {"title": {"type": "string"}, "start": {"type": "string", "description": "HH:MM 24h"},
         "end": {"type": "string", "description": "HH:MM 24h"}}, ["title", "start", "end"]),
    _fn("list_commitments", "List all fixed commitments."),
    _fn("delete_commitment", "Delete a fixed commitment.",
        {"commitment_id": {"type": "integer"}}, ["commitment_id"]),
    _fn("get_prayer_times", "Get the user's saved prayer (namaz) times."),
    _fn("set_prayer_time", "Change one prayer time.",
        {"name": {"type": "string", "enum": ["Fajr", "Zuhr", "Asr", "Maghrib", "Isha"]},
         "time": {"type": "string", "description": "HH:MM 24h"}}, ["name", "time"]),
    _fn("get_schedule", "Get the currently saved schedule for the day."),
    _fn("save_schedule",
        "Validate and save the FULL day schedule (07:00-22:00). Must include every fixed "
        "commitment (type 'fixed') and every prayer (type 'prayer'), with no overlaps. "
        "Returns errors if invalid; fix and call again.",
        {"blocks": {"type": "array", "items": {"type": "object", "properties": {
            "start": {"type": "string", "description": "HH:MM 24h"},
            "end": {"type": "string", "description": "HH:MM 24h"},
            "title": {"type": "string"},
            "type": {"type": "string", "enum": list(BLOCK_TYPES)},
            "task_id": {"type": "integer", "description": "id of the task, for type 'task'"},
            "detail": {"type": "string"}},
            "required": ["start", "end", "title", "type"]}},
         "note": {"type": "string", "description": "Short coach note for the user"}},
        ["blocks"]),
]


def execute_tool(name: str, args) -> dict:
    func = TOOL_FUNCS.get(name)
    if func is None:
        return {"error": f"Unknown tool '{name}'"}
    if not isinstance(args, dict):
        return {"error": "Tool arguments must be a JSON object"}
    try:
        return func(**args)
    except TypeError as exc:
        return {"error": f"Bad arguments for {name}: {exc}"}
    except ValueError as exc:
        return {"error": str(exc)}
    except Exception as exc:  # keep the agent alive on unexpected errors
        return {"error": f"{type(exc).__name__}: {exc}"}
