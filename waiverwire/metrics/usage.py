"""Usage metrics: the leading indicators of fantasy production.

Points follow usage. Target share, rush share, and touch trends move
before touchdowns do, which is what makes them useful on the waiver wire.
Everything here is computed from nflverse weekly player_stats.
"""
from __future__ import annotations

import pandas as pd

REQUIRED = {
    "player_id",
    "player_name",
    "position",
    "recent_team",
    "week",
    "targets",
    "carries",
    "fantasy_points_ppr",
}


def _check(df: pd.DataFrame) -> None:
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"player_stats is missing columns: {sorted(missing)}")


def add_opportunity_shares(df: pd.DataFrame) -> pd.DataFrame:
    """Add team-relative opportunity shares per player-week.

    target_share = player targets / team targets that week
    rush_share   = player carries / team carries that week
    touches      = targets + carries
    """
    _check(df)
    out = df.copy()
    team_targets = out.groupby(["recent_team", "week"])["targets"].transform("sum")
    team_carries = out.groupby(["recent_team", "week"])["carries"].transform("sum")
    out["target_share"] = out["targets"] / team_targets.replace(0, pd.NA)
    out["rush_share"] = out["carries"] / team_carries.replace(0, pd.NA)
    out["touches"] = out["targets"] + out["carries"]
    return out


def add_trends(df: pd.DataFrame, column: str = "touches", window: int = 2) -> pd.DataFrame:
    """Add a simple trend signal: recent average vs prior average.

    Positive means usage is rising. This is the breakout primitive
    the waiver report builds on in Phase 1.
    """
    out = df.sort_values(["player_id", "week"]).copy()
    recent = out.groupby("player_id")[column].transform(
        lambda s: s.rolling(window, min_periods=1).mean()
    )
    prior = out.groupby("player_id")[column].transform(
        lambda s: s.shift(window).rolling(window, min_periods=1).mean()
    )
    out[f"{column}_trend"] = (recent - prior).fillna(0.0)
    return out
