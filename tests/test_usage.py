import pandas as pd

from waiverwire.metrics.usage import add_opportunity_shares, add_trends


def _sample() -> pd.DataFrame:
    # Two teams (A, B), four weeks. p1's usage ramps in weeks 3-4 (breakout shape).
    p1_targets = [6, 6, 12, 14]
    rows = []
    for w, t in enumerate(p1_targets, start=1):
        rows.append(
            {
                "player_id": "p1",
                "player_name": "Alpha",
                "position": "WR",
                "recent_team": "A",
                "week": w,
                "targets": t,
                "carries": 0,
                "fantasy_points_ppr": float(t),
            }
        )
        rows.append(
            {
                "player_id": "p2",
                "player_name": "Beta",
                "position": "WR",
                "recent_team": "A",
                "week": w,
                "targets": 20 - t,
                "carries": 0,
                "fantasy_points_ppr": 5.0,
            }
        )
        rows.append(
            {
                "player_id": "p3",
                "player_name": "Gamma",
                "position": "RB",
                "recent_team": "B",
                "week": w,
                "targets": 4,
                "carries": 15,
                "fantasy_points_ppr": 12.0,
            }
        )
    return pd.DataFrame(rows)


def test_target_share_sums_to_one():
    df = add_opportunity_shares(_sample())
    sums = df.groupby(["recent_team", "week"])["target_share"].sum()
    assert ((sums - 1.0).abs() < 1e-9).all()


def test_rising_usage_has_positive_trend():
    df = add_trends(add_opportunity_shares(_sample()), column="touches", window=2)
    p1_w4 = df[(df["player_id"] == "p1") & (df["week"] == 4)].iloc[0]
    assert p1_w4["touches_trend"] > 0


def test_flat_usage_has_zero_trend():
    df = add_trends(add_opportunity_shares(_sample()), column="touches", window=2)
    p3 = df[df["player_id"] == "p3"]
    assert (p3["touches_trend"].abs() < 1e-9).all()
