"""
Utopia Studio — Scheduled Runner
=================================
Bonus: Scheduled run — fires the agent pipeline automatically.

Two modes:
  1. --now     Run the full pipeline immediately (checklist → briefing)
  2. --daemon  Sleep until next 9:00 AM Doha time (UTC+3), then run,
               then sleep again. Runs indefinitely.

Designed for cron / Windows Task Scheduler, or as a long-running daemon.

Usage:
    python scheduler.py --now       # Run once, print briefing, exit
    python scheduler.py --daemon    # Run forever, firing daily at 9 AM Doha
    python scheduler.py --now --slack  # Run once + post to Slack
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
DOHA_UTC_OFFSET = 3  # UTC+3


def run_pipeline(send_slack: bool = False) -> None:
    """Run agent.py --status, then briefing_agent.py. Print results."""
    print(f"\n{'=' * 60}")
    print(f"  Utopia OS Pipeline — {datetime.now().isoformat()}")
    print(f"{'=' * 60}\n")

    # Step 1: Run the onboarding agent's status check
    print("[1/2] Running Onboarding Operator Agent (status check)...")
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    result = subprocess.run(
        [sys.executable, str(AGENT_DIR / "agent.py"), "--status"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(AGENT_DIR),
        timeout=30,
        env=env,
    )
    if result.returncode != 0:
        print(f"[error] agent.py --status failed:\n{result.stderr}")
        return
    print(result.stdout.strip())

    # Step 2: Run the briefing agent
    print("\n[2/2] Running Morning Briefing Agent...")
    cmd = [sys.executable, str(AGENT_DIR / "briefing_agent.py")]
    if send_slack:
        cmd.append("--slack")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(AGENT_DIR),
        timeout=30,
        env=env,
    )
    if result.returncode != 0:
        print(f"[error] briefing_agent.py failed:\n{result.stderr}")
        return
    print(result.stdout)


def seconds_until_next_9am_doha() -> float:
    """
    Calculate seconds until the next 9:00 AM Doha time (UTC+3).
    If it's already past 9 AM today, target 9 AM tomorrow.
    """
    now_utc = datetime.utcnow()
    doha_now = now_utc + timedelta(hours=DOHA_UTC_OFFSET)

    # Target: 9:00 today in Doha
    target_doha = doha_now.replace(hour=9, minute=0, second=0, microsecond=0)

    if doha_now >= target_doha:
        # Already past 9 AM — target tomorrow
        target_doha += timedelta(days=1)

    target_utc = target_doha - timedelta(hours=DOHA_UTC_OFFSET)
    delta = (target_utc - now_utc).total_seconds()
    return max(delta, 0)


def daemon_loop(send_slack: bool = False) -> None:
    """Run forever, firing the pipeline every day at 9 AM Doha time."""
    print("🔄 Utopia OS Scheduler — daemon mode")
    print(f"   Pipeline will fire daily at 9:00 AM Doha time (UTC+3)")
    print(f"   Press Ctrl+C to stop.\n")

    while True:
        wait_seconds = seconds_until_next_9am_doha()
        next_run_utc = datetime.utcnow() + timedelta(seconds=wait_seconds)
        next_run_doha = next_run_utc + timedelta(hours=DOHA_UTC_OFFSET)

        print(
            f"⏳ Next run: {next_run_doha.strftime('%Y-%m-%d %H:%M')} Doha time "
            f"({wait_seconds / 60:.0f} min from now)"
        )

        try:
            time.sleep(wait_seconds)
        except KeyboardInterrupt:
            print("\n👋 Scheduler stopped.")
            return

        run_pipeline(send_slack=send_slack)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Utopia Studio Scheduled Runner")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run the full pipeline immediately and exit",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously, firing daily at 9 AM Doha time",
    )
    parser.add_argument(
        "--slack",
        action="store_true",
        help="Post the briefing to Slack (requires SLACK_WEBHOOK_URL)",
    )
    args = parser.parse_args()

    if args.daemon:
        daemon_loop(send_slack=args.slack)
    elif args.now:
        run_pipeline(send_slack=args.slack)
    else:
        parser.print_help()
        print("\nExample: python scheduler.py --now")
        print("         python scheduler.py --daemon --slack")


if __name__ == "__main__":
    main()
