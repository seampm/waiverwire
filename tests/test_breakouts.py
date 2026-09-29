import pandas as pd

from waiverwire.metrics.breakouts import score_breakouts


def _sample() -> pd.DataFrame:
    # p1: usage ramps hard in weeks 3-4, points lag (the breakout shape).
    # p2: steady high usage, already scoring (probably rostered).
    # p3: flat usage (not a breakout).
    # p4: a QB, should be filtered out of skill-position rankings.
    rows = []
    specs = {
        "p1": {"pos": "WR", "targets": [2, 2, 9, 11], "carries": [0, 0, 0, 0],
               "pts": [3.0, 3.0, 5.0, 6.0], "snaps": [0.2, 0.2, 0.7, 0.8]},
        "p2": {"pos": "WR", "targets": [10, 10, 10, 10], "carries": [0, 0, 0, 0],
               "pts": [20.0, 20.0, 20.0, 20.0], "snaps": [0.9, 0.9, 0.9, 0.9]},
        "p3": {"pos": "RB", "targets": [3, 3, 3, 3], "carries": [12, 12, 12, 12],
               "pts": [12.0, 12.0, 12.0, 12.0], "snaps": [0.6, 0.6, 0.6, 0.6]},
        "p4": {"pos": "QB", "targets": [0, 0, 0, 0], "carries": [2, 2, 5, 6],
               "pts": [18.0, 18.0, 25.0, 26.0], "snaps": [1.0, 1.0, 1.0, 1.0]},
    }
    for pid, s in specs.items():
        for i in range(4):
            rows.append(
                {
                    "player_id": pid,
                    "player_name": pid.upper(),
                    "position": s["pos"],
                    "recent_team": "A",
                    "week": i + 1,
                    "targets": float(s["targets"][i]),
                    "carries": float(s["carries"][i]),
                    "fantasy_points_ppr": s["pts"][i],
                    "snap_share": s["snaps"][i],
                }
            )
    return pd.DataFrame(rows)


def test_breakout_ranks_rising_usage_first():
    ranked = score_breakouts(_sample(), week=4)
    assert ranked.iloc[0]["player_id"] == "p1"


def test_breakout_flags_points_lagging():
    ranked = score_breakouts(_sample(), week=4)
    p1 = ranked[ranked["player_id"] == "p1"].iloc[0]
    assert bool(p1["before_points"])


def test_breakout_excludes_qb_and_low_snaps():
    ranked = score_breakouts(_sample(), week=4)
    assert "p4" not in set(ranked["player_id"])
    assert (ranked["snap_share_recent"] >= 0.25).all()


def test_breakout_uses_no_lookahead():
    # Scoring at week 2 must not see weeks 3-4: p3 is flat throughout,
    # so his trend is zero at week 2 despite later weeks existing.
    early = score_breakouts(_sample(), week=2)
    p3 = early[early["player_id"] == "p3"].iloc[0]
    assert p3["touches_trend"] == 0.0
    assert p3["targets_recent"] == 3.0
