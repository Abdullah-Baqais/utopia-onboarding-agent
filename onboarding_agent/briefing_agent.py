"""
Utopia Studio — Morning Briefing Agent (Second Agent)
======================================================
Bonus: Second-agent handoff for Utopia OS.

This agent reads the structured JSON state produced by the Onboarding
Operator Agent (agent.py) and takes the next action:
  1. Generates a human-readable morning briefing for the studio operator
  2. Optionally posts it to Slack
  3. Outputs structured JSON another agent could consume

This is the Utopia OS pattern: agent.py emits → briefing_agent.py picks up.

Usage:
    python briefing_agent.py              # Print briefing to stdout
    python briefing_agent.py --slack      # Also post to Slack (needs webhook)
    python briefing_agent.py --json       # Output as JSON only
"""

import argparse
import json
import os
from datetime import date, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Optional imports
# ---------------------------------------------------------------------------
_requests_available = True
try:
    import requests
except ImportError:
    requests = None  # type: ignore
    _requests_available = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
STATE_FILE = Path(__file__).resolve().parent / "fellows_state.json"


# ---------------------------------------------------------------------------
# Load state
# ---------------------------------------------------------------------------
def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"fellows": {}}
    return json.loads(STATE_FILE.read_text())


# ---------------------------------------------------------------------------
# Status evaluation (same logic as agent.py — duplicated intentionally so
# each agent is self-contained and can evolve independently)
# ---------------------------------------------------------------------------
def assess_fellow_status(checklist: dict) -> dict:
    today = date.today()
    overdue = 0
    urgent = 0
    complete = 0
    total = 0
    blockers: list = []

    for owner, entries in checklist.items():
        if owner.startswith("_"):
            continue
        for it in entries:
            total += 1
            status = it.get("status", "pending")
            if status == "complete":
                complete += 1
                continue
            due_date = date.fromisoformat(it["due_date"])
            if due_date < today:
                overdue += 1
                if (today - due_date).days > 2:
                    blockers.append(it)
            elif due_date == today:
                urgent += 1

    if complete == total:
        color = "green"
        label = "on track (all complete)"
    elif len(blockers) > 0 or overdue >= 2:
        color = "red"
        label = f"at risk ({overdue} overdue, {len(blockers)} >48h)"
    elif overdue >= 1 or urgent >= 1:
        color = "amber"
        label = f"needs attention ({overdue} overdue, {urgent} due today)"
    else:
        color = "green"
        label = "on track"

    return {
        "color": color,
        "label": label,
        "total_items": total,
        "complete": complete,
        "overdue": overdue,
        "due_today": urgent,
        "blockers": [b["item"] for b in blockers],
    }


# ---------------------------------------------------------------------------
# Briefing generator
# ---------------------------------------------------------------------------
def generate_briefing(state: dict) -> dict:
    """Read state, evaluate all fellows, produce a structured briefing."""
    fellows = state.get("fellows", {})
    if not fellows:
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": "No fellows in setup.",
            "fellows": [],
            "red_count": 0,
            "amber_count": 0,
            "green_count": 0,
            "slack_message": "☀️ *Morning Briefing* — No fellows currently in setup.",
        }

    briefing_fellows = []
    red_count = 0
    amber_count = 0
    green_count = 0

    for name, data in fellows.items():
        checklist = data.get("checklist", {})
        status = assess_fellow_status(checklist)
        status["name"] = name
        status["start_date"] = data.get("start_date", "unknown")
        briefing_fellows.append(status)

        if status["color"] == "red":
            red_count += 1
        elif status["color"] == "amber":
            amber_count += 1
        else:
            green_count += 1

    # Build human-readable Slack / text message
    lines = [
        "☀️ *Morning Briefing — Utopia Studio Operations*",
        f"📅 {date.today().isoformat()}",
        "",
        f"*{len(fellows)} fellows in setup:* "
        f"{green_count} 🟢 on track, "
        f"{amber_count} 🟡 needs attention, "
        f"{red_count} 🔴 at risk.",
        "",
    ]

    # Reds first (escalation), then ambers, then greens
    sorted_fellows = sorted(
        briefing_fellows,
        key=lambda f: {"red": 0, "amber": 1, "green": 2}[f["color"]],
    )

    for f in sorted_fellows:
        emoji = {"red": "🔴", "amber": "🟡", "green": "🟢"}[f["color"]]
        lines.append(f"{emoji} *{f['name']}* — starts {f['start_date']} — {f['label']}")
        if f["blockers"]:
            for blocker in f["blockers"]:
                lines.append(f"    ⛔ {blocker}")
        if f["due_today"]:
            lines.append(f"    ⏳ {f['due_today']} item(s) due today")

    lines.append("")
    lines.append("_Generated by Utopia OS — Briefing Agent_")

    slack_message = "\n".join(lines)

    return {
        "timestamp": datetime.now().isoformat(),
        "summary": (
            f"{len(fellows)} fellows: "
            f"{green_count} green, {amber_count} amber, {red_count} red"
        ),
        "fellows": briefing_fellows,
        "red_count": red_count,
        "amber_count": amber_count,
        "green_count": green_count,
        "slack_message": slack_message,
    }


# ---------------------------------------------------------------------------
# Slack sender
# ---------------------------------------------------------------------------
def send_to_slack(message: str) -> bool:
    if not SLACK_WEBHOOK_URL:
        print("[warn] SLACK_WEBHOOK_URL not set — cannot send to Slack.")
        return False
    if not _requests_available or requests is None:
        print("[warn] requests package not installed.")
        return False
    try:
        resp = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=10,
        )
        if resp.status_code == 200:
            print("[ok] Briefing posted to Slack.")
            return True
        else:
            print(f"[warn] Slack returned {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as exc:
        print(f"[warn] Slack send failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Utopia Studio Morning Briefing Agent")
    parser.add_argument(
        "--slack",
        action="store_true",
        help="Post the briefing to Slack via webhook",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON only (for downstream agents)",
    )
    args = parser.parse_args()

    state = load_state()
    briefing = generate_briefing(state)

    if args.json:
        # Structured output for another agent to consume
        print(json.dumps(briefing, indent=2, default=str))
        return

    # Human-readable output
    print(briefing["slack_message"])
    print()

    if args.slack:
        send_to_slack(briefing["slack_message"])


if __name__ == "__main__":
    main()
