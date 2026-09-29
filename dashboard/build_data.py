"""Build dashboard/data.json from computed weekly stats and breakout scores.

Reads the cached weekly parquet for the season, scores breakouts ahead of
the next waiver run, and writes the top 30 players with weekly usage series
(targets, touches, snap share, PPR plus target/touch share, air yards,
WOPR, red-zone touches, deep targets). The 2025 backtest section is carried
over unchanged from the previous data.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from waiverwire.data.weekly import build_weekly
from waiverwire.metrics.breakouts import score_breakouts

OUT = Path(__file__).parent / "data.json"
TOP_N = 30


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2026)
    args = ap.parse_args()

    df = build_weekly(args.season)
    week = int(df["week"].max())
    scored = score_breakouts(df, week).head(TOP_N)

    players = []
    for _, r in scored.iterrows():
        pid = r["player_id"]
        w = df[(df["player_id"] == pid) & (df["week"] <= week)].sort_values("week")

        def col(name: str) -> list[float]:
            return [round(float(x), 3) for x in w[name].tolist()]

        players.append(
            {
                "name": r["player_name"],
                "position": r["position"],
                "team": r["recent_team"],
                "score": float(r["breakout_score"]),
                "priority": bool(r["before_points"]),
                "reason": r["reason"],
                "weeks": [int(x) for x in w["week"].tolist()],
                "targets": col("targets"),
                "touches": col("touches"),
                "snap_share": col("snap_share"),
                "ppr": col("fantasy_points_ppr"),
                "target_share": col("target_share"),
                "touch_share": col("touch_share"),
                "air_yards": col("receiving_air_yards"),
                "redzone_touches": col("redzone_touches"),
                "deep_targets": col("deep_targets"),
                "wopr": col("wopr"),
            }
        )

    backtest = None
    if OUT.exists():
        backtest = json.loads(OUT.read_text()).get("backtest")

    data = {
        "season": args.season,
        "week": week,
        "pickup_week": week + 1,
        "players": players,
        "backtest": backtest,
    }
    OUT.write_text(json.dumps(data))
    print(f"wrote {OUT}: {len(players)} players, backtest={'kept' if backtest else 'missing'}")


if __name__ == "__main__":
    main()
