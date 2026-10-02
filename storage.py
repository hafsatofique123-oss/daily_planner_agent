"""Simple JSON file storage so tasks/schedule survive page refreshes."""
import json
import os
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "planner_data.json"

DEFAULT_PRAYERS = {
    "Fajr": "05:00",
    "Zuhr": "12:15",
    "Asr": "15:30",
    "Maghrib": "17:40",
    "Isha": "19:00",
}


def default_state() -> dict:
    return {
        "next_id": 1,
        "tasks": [],
        "commitments": [],
        "prayer_times": dict(DEFAULT_PRAYERS),
        "schedule": [],
        "schedule_note": "",
        "schedule_date": "",
    }


def load() -> dict:
    state = default_state()
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                state.update(data)
        except (json.JSONDecodeError, OSError):
            pass
    return state


def save(state: dict) -> None:
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, DATA_FILE)


def reset() -> None:
    save(default_state())
