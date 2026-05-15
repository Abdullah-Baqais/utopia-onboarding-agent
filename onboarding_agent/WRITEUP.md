# Writeup — Onboarding Operator Agent

**Track:** Operations  
**Applicant:** Abdullah Baqais  
**Date:** 2026-05-15

---

## Operator & Problem (3–4 sentences)

The Operations Lead at Utopia Studio manually coordinates every new fellow's onboarding across three functions (ops, tech, welcome-pack). For each fellow, they must track 10 checklist items with different owners and due dates, draft separate Slack messages to each team, and chase overdue items — all while managing 6–10 fellows simultaneously across different stages. This manual process costs roughly 2–3 hours per fellow and creates a risk of missed items, especially when multiple fellows start in the same week. The studio's target of "everything complete by 17:00 Doha time the day before start" is often missed because no single system tracks all items across all fellows in real time.

## The Agent (3–4 sentences)

The Onboarding Operator Agent takes a fellow name and start date as input, and produces three structured outputs in a single run: (1) a complete onboarding checklist with 10 items, each assigned to the correct owner function with a computed due date relative to the start date; (2) draft Slack messages — one per function (ops, tech, welcome-pack) — ready to paste into channels; (3) a status summary using the studio's green/amber/red convention, flagging which fellows are at risk and which specific items are blocking them. It calls the Claude API to enrich each checklist with operational risk notes (e.g., "start date falls on a Sunday — expedite Friday items"), and can optionally send Slack messages directly via incoming webhook. All output is structured JSON, making it consumable by another agent in Utopia OS without a human in the middle.

## Sample Input (paste it)

```
python agent.py "Fatima Al-Hashimi" "2026-06-15"
```

(No Claude API key set — ran with `--no-claude` mode.)

## Sample Output (paste it)

```json
{
  "fellow": "Fatima Al-Hashimi",
  "start_date": "2026-06-15",
  "checklist": {
    "ops": [
      {
        "item": "KYC completed",
        "owner": "ops",
        "owner_function": "Operations",
        "due_date": "2026-06-12",
        "status": "pending"
      },
      {
        "item": "First stipend released",
        "owner": "ops",
        "owner_function": "Operations",
        "due_date": "2026-06-14",
        "status": "pending"
      },
      {
        "item": "QDB housing confirmed",
        "owner": "ops",
        "owner_function": "Operations",
        "due_date": "2026-06-12",
        "status": "pending"
      }
    ],
    "tech": [
      {
        "item": "Slack channel: fellow-facing",
        "owner": "tech",
        "owner_function": "Tech",
        "due_date": "2026-06-13",
        "status": "pending"
      },
      {
        "item": "Slack channel: studio-only",
        "owner": "tech",
        "owner_function": "Tech",
        "due_date": "2026-06-13",
        "status": "pending"
      },
      {
        "item": "Linear project loaded from template",
        "owner": "tech",
        "owner_function": "Tech",
        "due_date": "2026-06-13",
        "status": "pending"
      },
      {
        "item": "Claude.ai project live",
        "owner": "tech",
        "owner_function": "Tech",
        "due_date": "2026-06-13",
        "status": "pending"
      },
      {
        "item": "Drive folder structured per template",
        "owner": "tech",
        "owner_function": "Tech",
        "due_date": "2026-06-13",
        "status": "pending"
      }
    ],
    "welcome-pack": [
      {
        "item": "Physical welcome kit sent",
        "owner": "welcome-pack",
        "owner_function": "Welcome Pack",
        "due_date": "2026-06-12",
        "status": "pending"
      },
      {
        "item": "Day-1 schedule confirmed",
        "owner": "welcome-pack",
        "owner_function": "Welcome Pack",
        "due_date": "2026-06-14",
        "status": "pending"
      }
    ]
  },
  "slack_messages": {
    "ops": "👋 *New Fellow Onboarding — Fatima Al-Hashimi*\n\nHi Operations team! Fatima Al-Hashimi starts on *2026-06-15*. Please action the items below by their due dates. Target: everything complete by 17:00 Doha time the day before start.\n\n  • KYC completed — due 2026-06-12\n  • First stipend released — due 2026-06-14\n  • QDB housing confirmed — due 2026-06-12\n\nReply in thread when each item is done. 🙏",
    "tech": "👋 *New Fellow Onboarding — Fatima Al-Hashimi*\n\nHi Tech team! Fatima Al-Hashimi starts on *2026-06-15*. Please action the items below by their due dates. Target: everything complete by 17:00 Doha time the day before start.\n\n  • Slack channel: fellow-facing — due 2026-06-13\n  • Slack channel: studio-only — due 2026-06-13\n  • Linear project loaded from template — due 2026-06-13\n  • Claude.ai project live — due 2026-06-13\n  • Drive folder structured per template — due 2026-06-13\n\nReply in thread when each item is done. 🙏",
    "welcome-pack": "👋 *New Fellow Onboarding — Fatima Al-Hashimi*\n\nHi Welcome Pack team! Fatima Al-Hashimi starts on *2026-06-15*. Please action the items below by their due dates. Target: everything complete by 17:00 Doha time the day before start.\n\n  • Physical welcome kit sent — due 2026-06-12\n  • Day-1 schedule confirmed — due 2026-06-14\n\nReply in thread when each item is done. 🙏"
  },
  "status_summary": {
    "color": "green",
    "label": "on track",
    "total_items": 10,
    "complete": 0,
    "overdue": 0,
    "due_today": 0,
    "blockers": []
  }
}
```

## What You Cut (2–3 bullets)

- **Linear API integration.** I chose not to build a direct Linear integration that creates/issues checklist items as Linear tasks. The JSON output is structured so another agent (or a simple Zapier/Make automation) can ingest it and create Linear issues. Building the full OAuth flow and Linear GraphQL client would have taken a day by itself without making the core logic better.
- **Real-time Slack event listener.** A Slack bot that lets an operator type `/onboard Fatima Al-Hashimi 2026-06-15` in a channel would be slick, but it requires standing up a persistent server, registering a Slack app, and handling OAuth — infrastructure overhead that doesn't improve the agent's decision-making. The CLI + webhook pattern achieves the same outcome with zero infrastructure.
- **Multi-fellow batch import.** I considered a CSV upload mode where the operator pastes 5 names at once. I cut it because the studio brief says 6–10 fellows at different milestones — simultaneous batch starts are rare, and individual entry gives the operator a moment to review each checklist before firing off messages.

## What Broke or Surprised You (2–3 bullets)

- **The `anthropic` package had a breaking API change** between the version I initially referenced (`0.39.0`) and the latest (`0.102.0`). The `Messages.create` signature changed. I caught this when the install pulled the latest version, and I updated the model string to `claude-sonnet-4-6` which is the current model ID. The model string should ideally be configurable via environment variable.
- **Date math edge case: Friday starts.** If a fellow starts on a Monday, the "1 day before" items fall on Sunday — when nobody is working. The agent correctly flags these as due Sunday, but it doesn't automatically adjust them to the previous Thursday. A production version should implement a "business day" calculation for due dates that skips Fridays and Saturdays (the Doha weekend).
- **JSON state file concurrency.** If two operators run the agent simultaneously, they'll clobber each other's `fellows_state.json`. I acknowledged this by keeping the state file simple and noting it should be replaced with a proper database (SQLite at minimum) before multi-operator use.

## If You Had Two More Days (2–3 bullets)

- **Linear API integration.** Push each checklist item as a Linear issue into the fellow's project, tagged with the owner function, and update the `--status` command to pull real-time completion status from Linear rather than the local JSON file. This closes the loop: the agent not only generates the checklist but also monitors it live.
- **Scheduled morning briefing.** A 9 AM Doha time cron job that runs `--status`, evaluates all fellows, and posts a single Slack message: "☀️ Morning briefing: 3 fellows in setup. 2 green, 1 red — Fatima Al-Hashimi has 3 items overdue >48h." This is the daily dashboard the Fellowships team currently builds manually.
- **Business-day-aware due dates.** Replace the naive `start_date - N days` logic with a proper Doha business calendar that skips Fridays and Saturdays, and automatically pulls items forward when a due date would land on a weekend.
