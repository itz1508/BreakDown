"""Legacy gap-analysis import; actual implementation is in Planner review."""

from agent.skills.planner.review.gap_analysis import *  # noqa: F401,F403
from agent.skills.planner.review.gap_analysis import main

if __name__ == "__main__":
    raise SystemExit(main())
