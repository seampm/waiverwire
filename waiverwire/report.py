"""Weekly waiver-wire report: who to pick up, and why.

Reads the latest week of nflverse data, scores every skill-position
player on usage trends, and prints the pickups worth a claim. Run it
Tuesday morning after the week's snaps and targets are in.
"""
from __future__ import annotations

import argparse

import pandas as pd

from waiverwire.data.weekly import build_weekly
from waiverwire.metrics.breakouts import score_breakouts


def build_report(season: int, week: int | None = None) -> str:
    df = build_weekly(season)
    week = week or int(df["week"].max())
    scored = score_breakouts(df, week)

    # Season totals to guess who's actually on waivers: high scorers
    # are almost certainly rostered already.
    season_pts = (
        df[df["week"] <= week]
        .groupby("player_id")["fantasy_points_ppr"]
        .sum()
        .rename("season_ppr")
    )
    scored = scored.merge(season_pts, on="player_id", how="left")

    lines = [
        f"WAIVER WIRE — pickups ahead of week {week + 1} (2026 season)",
        "Ranked by usage trend, not last week's box score.",
        "",
    ]

    priority = scored[scored["before_points"]].head(8)
    lines.append("PRIORITY PICKUPS — usage spiking, points lagging behind:")
    for _, r in priority.iterrows():
        lines.append(
            f"  {r['player_name']} ({r['position']}, {r['recent_team']}) "
            f"— score {r['breakout_score']:.0f}: {r['reason']}"
        )
    lines.append("")

    trending = scored[~scored["before_points"]].head(8)
    lines.append("TRENDING — usage up and already producing (likely rostered, check):")
    for _, r in trending.iterrows():
        lines.append(
            f"  {r['player_name']} ({r['position']}, {r['recent_team']}) "
            f"— score {r['breakout_score']:.0f}: {r['reason']}"
        )
    lines.append("")
    lines.append(
        "Usage moves before touchdowns do. These are the players whose "
        "snap share and targets say 'more coming'."
    )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Print the weekly waiver report")
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--week", type=int, default=None)
    args = ap.parse_args()
    print(build_report(args.season, args.week))


if __name__ == "__main__":
    main()
