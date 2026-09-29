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

import pandas as pd

from waiverwire.data.weekly import build_weekly
from waiverwire.metrics.breakouts import score_breakouts

OUT = Path(__file__).parent / "data.json"
TOP_N = 150


def build_pool(df, scored) -> list[dict]:
    """Every player with 2026 offensive stats, with season aggregates.

    Powers the matchup comparison tool: compact per-player numbers
    (no weekly series) so any rostered player can be looked up,
    not just the top-150 signal board.
    """
    scores = dict(zip(scored["player_id"], scored["breakout_score"]))
    pool = []
    for pid, w in df.groupby("player_id"):
        w = w.sort_values("week")
        last = w.iloc[-1]
        if pd.isna(last["player_name"]) or pd.isna(last["position"]):
            continue
        if last["position"] not in ("QB", "RB", "WR", "TE"):
            continue
        pool.append(
            {
                "name": last["player_name"],
                "position": last["position"],
                "team": last["recent_team"],
                "games": int(len(w)),
                "avg_ppr": round(float(w["fantasy_points_ppr"].mean()), 1),
                "avg_snap": round(float(w["snap_share"].mean()), 3),
                "avg_tgt_shr": round(float(w["target_share"].mean()), 3),
                "avg_tch_shr": round(float(w["touch_share"].mean()), 3),
                "avg_wopr": round(float(w["wopr"].mean()), 2),
                "rz": int(w["redzone_touches"].sum()),
                "deep": int(w["deep_targets"].sum()),
                "avg_pass_yds": round(float(w["passing_yards"].mean()), 1),
                "pass_tds": int(w["passing_tds"].sum()),
                "score": round(float(scores[pid]), 1)
                if pid in scores
                else None,
            }
        )
    return pool


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2026)
    args = ap.parse_args()

    df = build_weekly(args.season)
    week = int(df["week"].max())
    scored = score_breakouts(df, week)
    top = scored.head(TOP_N)

    players = []
    for _, r in top.iterrows():
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
        "pool": build_pool(df, scored),
        "backtest": backtest,
    }
    OUT.write_text(json.dumps(data))
    print(
        f"wrote {OUT}: {len(players)} players, "
        f"{len(data['pool'])} in pool, "
        f"backtest={'kept' if backtest else 'missing'}"
    )


if __name__ == "__main__":
    main()
