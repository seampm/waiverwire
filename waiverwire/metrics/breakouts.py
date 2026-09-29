"""Breakout detection: find waiver-wire targets from usage trends.

The edge is timing. Fantasy points follow usage with a lag: snap share
and targets climb first, touchdowns come later. A player whose usage is
spiking but who hasn't scored yet is usually still sitting on waivers.
This module scores that gap.
"""
from __future__ import annotations

import pandas as pd

SKILL_POSITIONS = ("WR", "RB", "TE")
MIN_SNAP_SHARE = 0.25  # must actually be on the field


def _recent_vs_prior(
    df: pd.DataFrame, week: int, column: str, window: int = 2
) -> pd.DataFrame:
    """Per-player recent average and prior average for `column`.

    Recent = last `window` weeks up to and including `week`.
    Prior = the `window` weeks before that (whatever exists).
    """
    recent_weeks = list(range(max(1, week - window + 1), week + 1))
    prior_weeks = list(range(max(1, week - 2 * window + 1), week - window + 1))

    recent = (
        df[df["week"].isin(recent_weeks)]
        .groupby("player_id")[column]
        .mean()
        .rename(f"{column}_recent")
    )
    prior = (
        df[df["week"].isin(prior_weeks)]
        .groupby("player_id")[column]
        .mean()
        .rename(f"{column}_prior")
    )
    out = pd.concat([recent, prior], axis=1)
    # No prior data (early season): no trend to measure, not a breakout.
    has_prior = out[f"{column}_prior"].notna()
    out[f"{column}_prior"] = out[f"{column}_prior"].fillna(0)
    out[f"{column}_recent"] = out[f"{column}_recent"].fillna(0)
    out[f"{column}_trend"] = (
        out[f"{column}_recent"] - out[f"{column}_prior"]
    ).where(has_prior, 0.0)
    return out.reset_index()


def score_breakouts(df: pd.DataFrame, week: int) -> pd.DataFrame:
    """Rank players by breakout score ahead of `week`'s waivers.

    Uses only data from weeks <= `week` (no lookahead). Returns one row
    per skill-position player with a 0-100 score and a plain-English
    reason. Higher = stronger waiver claim.
    """
    df = df[df["week"] <= week].copy()
    df["touches"] = df["targets"].fillna(0) + df["carries"].fillna(0)

    touches = _recent_vs_prior(df, week, "touches")
    snaps = _recent_vs_prior(df, week, "snap_share")
    targets = _recent_vs_prior(df, week, "targets")
    points = _recent_vs_prior(df, week, "fantasy_points_ppr")

    info = (
        df[df["week"] == week]
        .groupby("player_id", as_index=False)
        .agg(
            player_name=("player_name", "first"),
            position=("position", "first"),
            recent_team=("recent_team", "first"),
        )
    )

    out = info
    for t in (touches, snaps, targets, points):
        out = out.merge(t, on="player_id", how="left")
    out = out.fillna(0)

    out = out[out["position"].isin(SKILL_POSITIONS)]
    out = out[out["snap_share_recent"] >= MIN_SNAP_SHARE]

    # Normalize trends to 0-1 across the candidate pool so one loud
    # metric can't drown out the others.
    for col in ("touches_trend", "snap_share_trend", "targets_trend"):
        lo, hi = out[col].min(), out[col].max()
        out[col + "_n"] = (out[col] - lo) / (hi - lo) if hi > lo else 0.0

    out["breakout_score"] = (
        100
        * (
            0.45 * out["touches_trend_n"]
            + 0.35 * out["snap_share_trend_n"]
            + 0.20 * out["targets_trend_n"]
        )
    ).round(1)

    # Flag the real edge: usage surging while points lag behind.
    # Compares recent points to what that touch volume usually scores.
    out["points_per_touch"] = out["fantasy_points_ppr_recent"] / out[
        "touches_recent"
    ].replace(0, pd.NA)
    median_ppt = out["points_per_touch"].median()
    out["before_points"] = (
        (out["touches_trend"] > 0)
        & (out["points_per_touch"] < median_ppt)
        & (out["fantasy_points_ppr_recent"] < out["fantasy_points_ppr_recent"].median())
    )

    out["reason"] = out.apply(_explain, axis=1)
    return out.sort_values("breakout_score", ascending=False).reset_index(drop=True)


def _explain(row: pd.Series) -> str:
    bits = []
    if row["targets_trend"] >= 1:
        bits.append(
            f"targets {row['targets_prior']:.1f} to {row['targets_recent']:.1f}/wk"
        )
    if row["touches_trend"] >= 1 and row["targets_trend"] < 1:
        bits.append(
            f"touches {row['touches_prior']:.1f} to {row['touches_recent']:.1f}/wk"
        )
    if row["snap_share_trend"] >= 0.1:
        bits.append(
            f"snaps {row['snap_share_prior']:.0%} to {row['snap_share_recent']:.0%}"
        )
    if row["before_points"]:
        bits.append("points have not caught up yet")
    return "; ".join(bits) if bits else "steady usage"
