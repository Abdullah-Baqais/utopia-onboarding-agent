# Loom Script — Onboarding Operator Agent (5 min)

**Track:** Operations  
**Agent:** Onboarding Operator Agent (Utopia OS node)  
**Name:** Abdullah Baqais

---

## ⏱️ Timing breakdown

| Section | Time |
|---|---|
| Opening + introduction | 0:00–0:20 |
| Q1: Operator & problem | 0:20–0:45 |
| Q2: Agent explained plainly (Feynman test) | 0:45–1:10 |
| Transition | 1:10–1:15 |
| Demo 1: New fellow + Claude enrichment | 1:15–2:00 |
| Transition | 2:00–2:05 |
| Demo 2: Slack webhook live | 2:05–2:45 |
| Transition | 2:45–2:50 |
| Demo 3: Status dashboard (green/amber/red) | 2:50–3:20 |
| Transition | 3:20–3:25 |
| Demo 4: Full pipeline — the Utopia OS chain | 3:25–4:05 |
| Transition | 4:05–4:10 |
| Code walkthrough (speed round) | 4:10–4:45 |
| Closing | 4:45–5:00 |

---

## 🎬 Before you hit record

Open these windows and arrange them side-by-side:

| Window 1 | Terminal (PowerShell) in the `onboarding_agent` folder |
|---|---|
| Window 2 | Slack — the channel your webhook posts to |
| Window 3 | VS Code with `agent.py` open (for the code segment) |

Run this once to set up a clean slate:

```powershell
del .\fellows_state.json
```

Then pre-type these commands (don't hit enter):

**Terminal tab 1:**
```powershell
python agent.py "Noor Al-Ansari" "2026-06-25"
```

**Terminal tab 2** (pre-typed for later):
```powershell
python agent.py "Rashid Al-Mansoori" "2026-05-10"
python agent.py "Layla Bint Ahmed" "2026-06-30"
```

---

## 🎥 The script

---

### OPENING (0:00–0:20)

> *(Face camera. Smile. Steady pace.)*

**"Hi, I'm Abdullah Baqais. Over the next five minutes I'm going to show you an AI agent for the Operations track I built that automates the fellow onboarding process end to end. Here's what we'll cover: the problem this solves, a live demo with real Slack messages and Claude enrichment, a status dashboard across multiple fellows, the full Utopia OS pipeline — one agent handing off to another — and a quick look at how it's built. Let's jump in."**

*(~20 seconds)*

---

### Q1 — OPERATOR & PROBLEM (0:20–0:45)

> *(Still on camera. Speak directly.)*

**"So first — who needs this, and what were they doing before? The operator is the Operations Lead at Utopia Studio. Every time a new fellow joins, they manually build a 10-item onboarding checklist across three teams — Operations, Tech, and Welcome Pack. They calculate every due date by hand, counting backwards from the start date. They draft separate Slack messages to each team. And then — across 6 to 10 fellows at once — they chase overdue items manually. That's 2 to 3 hours per fellow. The studio's rule is everything complete by 5 PM the day before start — and that rule gets broken, especially when multiple fellows start the same week. There's no single system tracking all of this, so things slip."**

*(~25 seconds)*

---

### Q2 — AGENT EXPLAINED PLAINLY (0:45–1:10)

> *(Still on camera. This is the Feynman test — explain like you're talking to a non-technical operator.)*

**"Here's how my agent works. You give it a fellow's name and a start date. It instantly knows what needs to happen and when — KYC is due 3 days before start, Slack channels 2 days before, and so on. It writes the Slack messages for you — one to each team, with their specific tasks and deadlines, ready to send. Then it checks every fellow in the pipeline and shows you a dashboard: green for on track, amber for needs attention, red for at risk — and it names the exact items that are blocking each one. All the output is structured JSON, which means another agent in Utopia OS can pick it up and take the next action — no human copying and pasting between systems. The operator goes from hours of manual work to a single command."**

*(~25 seconds)*

---

### TRANSITION 1 (1:10–1:15)

> *(Turn to the terminal window.)*

**"Alright — enough talking. Let me show you the agent running live."**

---

### DEMO 1 — NEW FELLOW + CLAUDE ENRICHMENT (1:15–2:00)

> *(Terminal is visible. Hit enter on the pre-typed command.)*

```powershell
python agent.py "Noor Al-Ansari" "2026-06-25"
```

> *(Scroll slowly through the JSON output. Pause at key sections.)*

**"Here's the output. First, the checklist — 10 items organized by function. Ops gets KYC, stipend, and housing. Tech gets Slack channels, Linear project, Claude project, Drive folder. Welcome Pack gets the physical kit and Day-1 schedule. Every item has a computed due date — KYC due June 22nd, three days before the start. All of this was generated from a single name and date."**

> *(Scroll down to `_claude_notes`.)*

**"This field right here — `_claude_notes` — is Claude. The agent asked Claude to review the checklist and flag any operational risks. Claude noticed Noor starts on a Thursday, so any item due Wednesday has zero buffer — if it slips, Thursday morning is a scramble. That's exactly the kind of context an operator would normally have to think through manually for every single fellow. Now it's automatic."**

> *(Scroll to `slack_messages`.)*

**"And down here — three draft Slack messages, one per team. Each one lists that team's specific items and due dates, formatted and ready to go."**

> *(Point at `status_summary`.)*

**"Status is GREEN. All due dates are in the future, nothing is overdue."**

*(~45 seconds)*

---

### TRANSITION 2 (2:00–2:05)

> *(Move mouse to Slack window.)*

**"But draft messages aren't sent messages. Let's actually deliver them."**

---

### DEMO 2 — SLACK WEBHOOK LIVE (2:05–2:45)

> *(Make sure Slack is visible next to the terminal. Run the command.)*

```powershell
python agent.py "Noor Al-Ansari" "2026-06-25" --send-slack
```

> *(Three messages appear in Slack — one per team. Give it a beat so the viewer can see them land.)*

**"There they are. Three messages, delivered to the channel simultaneously — Operations, Tech, and Welcome Pack. Each message has due dates, and context."**

> *(Click into one message to show the formatting.)*

**"Formatted Slack markdown — bold, bulleted, clean. The operator fires this command and walks away. They don't write three different messages. They don't forget to notify one of the functions. It just happens."**

*(~40 seconds)*

---

### TRANSITION 3 (2:45–2:50)

> *(Back to terminal.)*

**"That's one fellow. But the studio runs 6 to 10 fellows at once. Let me show you how the agent tracks all of them."**

---

### DEMO 3 — STATUS DASHBOARD (2:50–3:20)

> *(Type or paste the pre-typed commands.)*

```powershell
python agent.py "Rashid Al-Mansoori" "2026-05-10"
python agent.py "Layla Bint Ahmed" "2026-06-30"
```

> *(Then the dashboard.)*

```powershell
python agent.py --status
```

**"I just added two more fellows. Rashid with a past start date — May 20th, almost a year ago. Layla with a future date. Now let's look at the dashboard."**

> *(Point at the JSON.)*

**"Noor — GREEN. On track. Layla — GREEN. On track. Rashid — RED. 10 items overdue, all of them open more than 48 hours. Every single item is listed as a blocker. This is the exact dashboard the Fellowships team builds manually every morning. The agent produces it in under a second."**

> *(Gesture at the color-coding.)*

**"The convention comes straight from the studio brief. Green means all items complete or on track. Amber means one item slipping — overdue less than 48 hours, or due today. Red means two or more overdue, or any blocker open more than 48 hours — that's escalated. The agent doesn't just say 'Rashid is red.' It tells you KYC is overdue, housing is overdue, Slack channels are overdue — so the operator knows exactly what to chase."**

*(~30 seconds)*

---

### TRANSITION 4 (3:20–3:25)

> *(Still in terminal.)*

**"Now — this is where Utopia OS comes in. One agent shouldn't do everything. The pattern is: one agent emits structured output, the next agent picks it up and takes the next action. Let me show you."**

---

### DEMO 4 — FULL PIPELINE (3:25–4:05)

```powershell
python scheduler.py --now --slack
```

> *(Watch the two pipeline steps run.)*

**"Step 1 — the onboarding agent runs the status check on all fellows. You see the raw JSON — 3 fellows, their colors, their blockers."**

**"Step 2 — the briefing agent picks up that output and does something the first agent doesn't do: it writes a morning briefing. Human-readable. One message. Designed for the operator to read in Slack with their coffee."**

> *(Switch to Slack — show the briefing message.)*

**"Here it is. 'Morning Briefing — Utopia Studio Operations. May 15th. Three fellows in setup: two green, zero amber, one red.' Rashid at risk, 10 blockers. The operator reads this one message and knows exactly what needs attention — before they even open Linear, before they check a spreadsheet. And the `--slack` flag delivered it automatically."**

> *(Pause.)*

**"This is the Utopia OS pattern in action. Agent one — the onboarding agent — emits structured JSON. Agent two — the briefing agent — consumes that JSON and produces a Slack message. They're independent. Either can evolve without touching the other. No human in the middle."**

*(~40 seconds)*

---

### TRANSITION 5 (4:05–4:10)

> *(Switch to VS Code.)*

**"Let me show you what's under the hood — quickly."**

---

### CODE WALKTHROUGH (4:10–4:45)

> *(VS Code open to `agent.py`.)*

**"The agent is about 370 lines of Python. The engine is this table right here — `ONBOARDING_ITEMS`. Ten rows. Each row is three things: what needs to happen, who owns it, and how many days before the start date it's due. That's the studio's real onboarding process, encoded as data. If the process changes — say KYC now needs 5 days instead of 3 — you change one number."**

> *(Scroll to `generate_checklist`.)*

**"The checklist generator loops over that table, subtracts the days from the start date using Python's date math, and builds the structured output. Pure logic. No AI. The agent works with or without Claude."**

> *(Scroll to `assess_fellow_status`.)*

**"The status evaluator is the green-amber-red logic. It compares due dates against today's date, counts how many are overdue, checks if any have been open more than 48 hours, and assigns the color. Again — pure logic, no AI. This runs every morning whether or not an LLM is available."**

> *(Switch to `briefing_agent.py`.)*

**"Separate file — the briefing agent. It reads the JSON state the first agent wrote, evaluates all fellows, and produces that formatted Slack message. Two agents, one shared state file. That's the pattern."**

> *(Switch to `scheduler.py`.)*

**"The scheduler wraps everything. It calculates the time until 9 AM Doha time — UTC plus 3 — sleeps, then fires the pipeline. For production you'd wire this to Windows Task Scheduler or a cron job, and it runs every morning without anyone touching it."**

*(~35 seconds)*

---

### CLOSING (4:45–5:00)

> *(Back to camera.)*

**"So — in five minutes you've seen: a new fellow onboarded in one command, Claude flagging a real operational risk that a manual process would miss, Slack messages delivered to three teams simultaneously, a real-time status dashboard across multiple fellows with the studio's own green-amber-red convention, and the full Utopia OS chain — agent one handing off to agent two — firing automatically. The Operations Lead starts their Monday morning with one Slack message instead of a spreadsheet and three hours of manual chasing."**

> *(Brief pause.)*

**"Code is linked in the submission, along with the writeup and README. Thank you for watching — I'd love to walk you through it live in the next round."**

*(Stop recording.)*

---

## 🎯 Pro tips

- **Don't retake** if you stumble. The brief says "honesty scores higher than polish." Keep going.
- **Speak slower than you think** — Loom viewers can 2x but can't slow down a rushed recording.
- **Mouse cursor big** — Loom settings → "Show cursor highlight" or Windows → Mouse Settings → increase cursor size.
- **Close notifications** — Slack pings and email pop-ups kill credibility. Turn on Focus Assist (`Win + N`).
- **Do one throwaway recording first** — check mic clarity, Slack visibility, and terminal font size.
- **Pre-type every command** — nothing kills momentum like typing live and making a typo.
