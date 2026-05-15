"""
Utopia Studio — Onboarding Operator Agent
==========================================
Operations Track: Automates the fellow onboarding process.

Takes a fellow name and start date, then:
1. Generates a structured onboarding checklist with owners and due dates
2. Drafts Slack messages to each function (ops, tech, welcome-pack)
3. Summarizes what is missing or overdue for any fellow currently in setup

Integrations:
  - Claude API (anthropic) — enriches checklist with operational notes
  - Slack Incoming Webhook — sends draft messages directly to channels

Designed to slot into Utopia OS as a node — output is structured JSON
another agent can consume.

Usage:
    python agent.py "Fellow Name" "2025-06-15"
    python agent.py --status  # Show all fellows in setup and their status
"""

import argparse
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Optional imports — agent runs without these, but enrichment/sending is skipped
# ---------------------------------------------------------------------------
_anthropic_available = True
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore
    _anthropic_available = False

_requests_available = True
try:
    import requests
except ImportError:
    requests = None  # type: ignore
    _requests_available = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
DATA_FILE = Path(__file__).resolve().parent / "fellows_state.json"
NL = "\n"  # f-string-safe newline

# Onboarding items per the Utopia Studio operations spec
# Format: (item, owner_function, days_before_start_date)
ONBOARDING_ITEMS = [
    ("KYC completed", "ops", 3),
    ("First stipend released", "ops", 1),
    ("QDB housing confirmed", "ops", 3),
    ("Slack channel: fellow-facing", "tech", 2),
    ("Slack channel: studio-only", "tech", 2),
    ("Linear project loaded from template", "tech", 2),
    ("Claude.ai project live", "tech", 2),
    ("Drive folder structured per template", "tech", 2),
    ("Physical welcome kit sent", "welcome-pack", 3),
    ("Day-1 schedule confirmed", "welcome-pack", 1),
]

OWNER_FUNCTIONS = {
    "ops": "Operations",
    "tech": "Tech",
    "welcome-pack": "Welcome Pack",
}

# Studio rule: every item complete by 17:00 Doha time the day before start.
# Anything red the morning of start is escalated.


# =========================================================================
#  State management (local JSON — production would use a DB)
# =========================================================================
def load_state() -> dict:
    """Load persisted fellow state from disk."""
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except json.JSONDecodeError:
            print("WARNING: Corrupted state file; starting fresh.")
    return {"fellows": {}}


def save_state(state: dict) -> None:
    """Persist fellow state to disk."""
    DATA_FILE.write_text(json.dumps(state, indent=2, default=str))


# =========================================================================
#  Claude enrichment (optional — needs ANTHROPIC_API_KEY)
# =========================================================================
def _claude_enrich_checklist(
    fellow_name: str,
    start_date: date,
    checklist: dict,
) -> Optional[str]:
    """Use Claude to add operator-facing notes to the checklist."""
    if not _anthropic_available or Anthropic is None:
        return None
    if not ANTHROPIC_API_KEY:
        return None

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    items_flat = []
    for owner, entries in checklist.items():
        if owner.startswith("_"):
            continue
        for e in entries:
            items_flat.append(
                f"- [{e['status']}] {e['item']} "
                f"(owner: {e['owner_function']}, due: {e['due_date']})"
            )

    prompt = f"""You are an operations agent at Utopia Studio, a venture studio in Doha.

A new fellow named "{fellow_name}" starts on {start_date.isoformat()}.
Their onboarding checklist is below.

In 2-3 sentences, add any operational note or risk flag the studio operator
should be aware of (e.g. if the start date is very soon and items are due
immediately, if it falls on a weekend, etc.). Be concise.

Checklist:
{NL.join(items_flat)}

Return ONLY the note text, no JSON, no markdown formatting."""

    try:
        resp = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=256,
            system="You are a concise operations assistant. Respond with plain text only.",
            messages=[{"role": "user", "content": prompt}],
        )
        note = resp.content[0].text.strip()
        return note
    except Exception as exc:
        print(f"  [warn] Claude enrichment skipped: {exc}")
        return None


# =========================================================================
#  Slack webhook sender (optional — needs SLACK_WEBHOOK_URL)
# =========================================================================
def send_slack_message(owner_func: str, message: str) -> bool:
    """Send a Slack message via incoming webhook (if configured)."""
    if not SLACK_WEBHOOK_URL:
        print(
            f"  [warn] SLACK_WEBHOOK_URL not set — skipping Slack send for {owner_func}"
        )
        return False
    if not _requests_available or requests is None:
        print(
            f"  [warn] requests package not installed; "
            f"cannot send Slack message for {owner_func}"
        )
        return False
    try:
        resp = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"  [ok] Slack message sent to {owner_func}")
            return True
        else:
            print(
                f"  [warn] Slack webhook returned {resp.status_code}: {resp.text[:200]}"
            )
            return False
    except Exception as exc:
        print(f"  [warn] Slack send failed for {owner_func}: {exc}")
        return False


# =========================================================================
#  Core logic
# =========================================================================
def generate_checklist(
    fellow_name: str,
    start_date: date,
    *,
    use_claude: bool = True,
) -> dict:
    """
    Build the structured onboarding checklist for one fellow.

    Returns a dict keyed by owner function, each value a list of item dicts
    with: item, owner, owner_function, due_date, status.
    """
    checklist: dict = {}
    for item_desc, owner, days_before in ONBOARDING_ITEMS:
        due_date = start_date - timedelta(days=days_before)
        owner_name = OWNER_FUNCTIONS.get(owner, owner)
        entry = {
            "item": item_desc,
            "owner": owner,
            "owner_function": owner_name,
            "due_date": due_date.isoformat(),
            "status": "pending",
        }
        checklist.setdefault(owner, []).append(entry)

    # If Claude is available, enrich with any extra context
    if use_claude:
        enrichment = _claude_enrich_checklist(fellow_name, start_date, checklist)
        if enrichment:
            checklist["_claude_notes"] = enrichment

    return checklist


def generate_slack_messages(
    fellow_name: str,
    start_date: date,
    checklist: dict,
) -> dict:
    """
    Draft one Slack message per owner function, ready to copy-paste into
    the appropriate channel (or send via webhook).
    """
    messages = {}
    for owner_func in ("ops", "tech", "welcome-pack"):
        owner_name = OWNER_FUNCTIONS[owner_func]
        items = checklist.get(owner_func, [])
        if not items:
            continue
        item_lines = "\n".join(
            f"  • {it['item']} — due {it['due_date']}" for it in items
        )
        messages[owner_func] = (
            f"👋 *New Fellow Onboarding — {fellow_name}*\n\n"
            f"Hi {owner_name} team! {fellow_name} starts on "
            f"*{start_date.isoformat()}*. Please action the items below "
            f"by their due dates. Target: everything complete by 17:00 "
            f"Doha time the day before start.\n\n"
            f"{item_lines}\n\n"
            f"Reply in thread when each item is done. 🙏"
        )
    return messages


def assess_fellow_status(checklist: dict) -> dict:
    """
    Evaluate a single fellow's checklist and return a status summary.

    Conventions per the studio brief:
      - green  = all items complete or on track
      - amber  = one item slipping (past due but <48h, or due today)
      - red    = two+ items slipping OR any blocker open >48h
    """
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


def process_new_fellow(
    fellow_name: str,
    start_date_str: str,
    *,
    use_claude: bool = True,
    send_slack: bool = False,
) -> dict:
    """Full pipeline: ingest a new fellow, produce the operations output."""
    start_date = date.fromisoformat(start_date_str)

    # 1. Generate checklist
    checklist = generate_checklist(fellow_name, start_date, use_claude=use_claude)

    # 2. Generate Slack messages
    slack_msgs = generate_slack_messages(fellow_name, start_date, checklist)

    # 3. Persist state
    state = load_state()
    state["fellows"][fellow_name] = {
        "start_date": start_date.isoformat(),
        "checklist": checklist,
        "created_at": datetime.now().isoformat(),
    }
    save_state(state)

    # 4. Optionally send Slack messages via webhook
    if send_slack:
        for owner_func, msg in slack_msgs.items():
            send_slack_message(owner_func, msg)

    # 5. Build status summary
    status = assess_fellow_status(checklist)

    return {
        "fellow": fellow_name,
        "start_date": start_date.isoformat(),
        "checklist": checklist,
        "slack_messages": slack_msgs,
        "status_summary": status,
    }


def get_all_fellows_status() -> dict:
    """Return a status summary for every fellow currently in setup."""
    state = load_state()
    fellows = state.get("fellows", {})
    summary = {}
    for name, data in fellows.items():
        checklist = data.get("checklist", {})
        summary[name] = {
            "start_date": data.get("start_date", "unknown"),
            "status": assess_fellow_status(checklist),
        }
    return summary


# =========================================================================
#  CLI
# =========================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Utopia Studio Onboarding Operator Agent"
    )
    parser.add_argument(
        "name",
        nargs="?",
        help="Fellow name (e.g. 'Aisha Al-Thani')",
    )
    parser.add_argument(
        "start_date",
        nargs="?",
        help="Start date in ISO format (e.g. 2025-06-15)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show status of all fellows currently in setup",
    )
    parser.add_argument(
        "--no-claude",
        action="store_true",
        help="Skip Claude API enrichment",
    )
    parser.add_argument(
        "--send-slack",
        action="store_true",
        help="Send draft messages to Slack via webhook (needs SLACK_WEBHOOK_URL)",
    )
    args = parser.parse_args()

    # --status mode
    if args.status:
        all_status = get_all_fellows_status()
        if not all_status:
            print("No fellows in setup.")
            return
        print(json.dumps(all_status, indent=2, default=str))
        return

    # New fellow mode
    if not args.name or not args.start_date:
        parser.error(
            "Provide fellow name and start date, or use --status.\n"
            "Example: python agent.py 'Aisha Al-Thani' 2025-06-15"
        )
        return

    # Determine Claude usage
    use_claude = True
    if args.no_claude:
        use_claude = False
    elif not _anthropic_available:
        print("[info] anthropic package not installed — Claude enrichment skipped.")
        use_claude = False
    elif not ANTHROPIC_API_KEY:
        print("[info] ANTHROPIC_API_KEY not set — Claude enrichment skipped.")
        use_claude = False

    output = process_new_fellow(
        args.name,
        args.start_date,
        use_claude=use_claude,
        send_slack=args.send_slack,
    )

    print(json.dumps(output, indent=2, default=str))
    print()  # blank separator

    # Human-readable summary
    status = output["status_summary"]
    print(f"Status: {status['color'].upper()} — {status['label']}")
    if status["blockers"]:
        print(f"Blockers: {', '.join(status['blockers'])}")

    # Print Slack messages for easy copy-paste
    print("\n─── Draft Slack Messages ───")
    for owner, msg in output["slack_messages"].items():
        print(f"\n--- {OWNER_FUNCTIONS.get(owner, owner)} ---")
        print(msg)


if __name__ == "__main__":
    main()
