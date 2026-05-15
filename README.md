# Onboarding Operator Agent

**One-liner:** An AI agent that automates Utopia Studio's fellow onboarding — takes a fellow name and start date, outputs a structured checklist with owners/due-dates, draft Slack messages per function, and a real-time missing/overdue summary across all fellows in setup.

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set environment variables (optional — agent runs fine without them)

| Variable | Purpose | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` | Enables Claude-powered operational notes on each checklist | No |
| `SLACK_WEBHOOK_URL` | Sends draft Slack messages directly to channels | No |

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."

# Mac / Linux
export ANTHROPIC_API_KEY="sk-ant-..."
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

### 3. Run

```bash
# Add a new fellow
python agent.py "Fatima Al-Hashimi" "2026-06-22"

# Add a fellow + send Slack messages via webhook
python agent.py "Fatima Al-Hashimi" "2026-06-22" --send-slack

# Skip Claude enrichment (even if key is set)
python agent.py "Fatima Al-Hashimi" "2026-06-22" --no-claude

# Show status dashboard for all fellows in setup
python agent.py --status
```

---

## Prompts Used

The agent uses one Claude API prompt (in `_claude_enrich_checklist`):

```
You are an operations agent at Utopia Studio, a venture studio in Doha.

A new fellow named "{fellow_name}" starts on {start_date}.
Their onboarding checklist is below.

In 2-3 sentences, add any operational note or risk flag the studio operator
should be aware of (e.g. if the start date is very soon and items are due
immediately, if it falls on a weekend, etc.). Be concise.

Checklist:
[flat list of checklist items with status/owner/due_date]

Return ONLY the note text, no JSON, no markdown formatting.
```

---

## Tools / APIs Called

| Tool | How it's used | Activation |
|---|---|---|
| **Claude API** (Anthropic) | Enriches each onboarding checklist with operator-facing risk notes | Set `ANTHROPIC_API_KEY` |
| **Slack Incoming Webhook** | Sends draft onboarding messages directly to ops/tech/welcome-pack channels | Set `SLACK_WEBHOOK_URL` |
| **Local JSON state** | Persists fellow data between runs (`fellows_state.json`) | Always on |

---

## Architecture

```
                   ┌──────────────────────┐
                   │   Studio Operator    │
                   │  (runs from CLI or   │
                   │   triggered by cron) │
                   └──────────┬───────────┘
                              │
              ┌───────────────▼───────────────┐
              │     Onboarding Agent (agent.py) │
              │                                │
              │  ┌──────────────────────────┐  │
              │  │  1. generate_checklist() │  │
              │  │     → dates computed     │  │
              │  │     → Claude enrichment  │  │
              │  └──────────┬───────────────┘  │
              │             │                  │
              │  ┌──────────▼───────────────┐  │
              │  │ 2. generate_slack_msgs() │  │
              │  │     → draft per function │  │
              │  └──────────┬───────────────┘  │
              │             │                  │
              │  ┌──────────▼───────────────┐  │
              │  │ 3. assess_status()       │  │
              │  │     → green/amber/red    │  │
              │  └──────────┬───────────────┘  │
              │             │                  │
              │  ┌──────────▼───────────────┐  │
              │  │ 4. persist to JSON       │  │
              │  │     → fellows_state.json │  │
              │  └──────────────────────────┘  │
              └────────────────────────────────┘
                              │
              ┌───────────────▼────────────────┐
              │        Structured JSON          │
              │  → checklist, slack_messages,   │
              │    status_summary               │
              └────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
   ┌──────────┐       ┌──────────────┐    ┌──────────────┐
   │  Linear   │       │    Slack     │    │  Next Agent  │
   │  (issue)  │       │  (message)   │    │  (Utopia OS) │
   └──────────┘       └──────────────┘    └──────────────┘
```

---

## Output Format

Every run produces JSON with this schema:

```json
{
  "fellow": "string",
  "start_date": "YYYY-MM-DD",
  "checklist": {
    "ops": [
      {
        "item": "KYC completed",
        "owner": "ops",
        "owner_function": "Operations",
        "due_date": "YYYY-MM-DD",
        "status": "pending"
      }
    ],
    "tech": [ ... ],
    "welcome-pack": [ ... ],
    "_claude_notes": "string (optional)"
  },
  "slack_messages": {
    "ops": "markdown string",
    "tech": "markdown string",
    "welcome-pack": "markdown string"
  },
  "status_summary": {
    "color": "green | amber | red",
    "label": "human-readable status",
    "total_items": 10,
    "complete": 0,
    "overdue": 0,
    "due_today": 0,
    "blockers": []
  }
}
```

---

## Status Convention (from studio brief)

| Color | Rule |
|---|---|
| 🟢 Green | All items complete, or all due dates are in the future |
| 🟡 Amber | One item past due (<48h) OR one item due today |
| 🔴 Red | Two+ items past due OR any item overdue >48h — escalated |

---

## Sample Run

```bash
$ python agent.py "Fatima Al-Hashimi" "2026-06-22"

Status: GREEN — on track

─── Draft Slack Messages ───

--- Operations ---
👋 *New Fellow Onboarding — Fatima Al-Hashimi*

Hi Operations team! Fatima Al-Hashimi starts on *2026-06-22*.
Please action the items below by their due dates. Target: everything
complete by 17:00 Doha time the day before start.

  • KYC completed — due 2026-06-12
  • First stipend released — due 2026-06-14
  • QDB housing confirmed — due 2026-06-12

Reply in thread when each item is done. 🙏
```

---

## Bonus: Second-Agent Handoff + Scheduled Run

### 1. Morning Briefing Agent (`briefing_agent.py`)

This is the **second agent in the Utopia OS chain**. It reads the JSON state
produced by `agent.py` and takes the next action — generating a daily briefing.

```bash
# Print human-readable briefing
python briefing_agent.py

# Output JSON for another agent to consume (the Utopia OS pattern)
python briefing_agent.py --json

# Post the briefing directly to Slack
python briefing_agent.py --slack
```

**Sample output:**
```
☀️ *Morning Briefing — Utopia Studio Operations*
📅 2026-05-15

*2 fellows in setup:* 2 🟢 on track, 0 🟡 needs attention, 0 🔴 at risk.

🟢 *Fatima Al-Hashimi* — starts 2026-06-15 — on track
🟢 *Khalid Al-Mohannadi* — starts 2026-07-01 — on track

_Generated by Utopia OS — Briefing Agent_
```

### 2. Scheduled Runner (`scheduler.py`)

Fires the full pipeline automatically. Runs `agent.py --status` → `briefing_agent.py`.

```bash
# Run the full pipeline now
python scheduler.py --now

# Run the full pipeline now + post briefing to Slack
python scheduler.py --now --slack

# Run forever, firing daily at 9:00 AM Doha time (UTC+3)
python scheduler.py --daemon

# Daemon + auto-post to Slack
python scheduler.py --daemon --slack
```

### Agent Chain (Utopia OS Pattern)

```
agent.py (checklist + status)
    │
    │  fellows_state.json
    ▼
briefing_agent.py (morning briefing)
    │
    │  structured JSON / Slack message
    ▼
[ next agent in Utopia OS ... ]
```
