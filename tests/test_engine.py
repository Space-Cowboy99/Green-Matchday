from green_matchday.engine import estimate_fixture

def test_basic_estimate_runs():
    res = estimate_fixture(
        home="West Ham United",
        away="Leeds United",
        clubs_csv_path="data/clubs.csv",
        away_fans=3000,
        mode_share={"train": 0.5, "coach": 0.3, "car": 0.2},
    )
    assert res.distance_km > 200
    assert res.per_fan_kg > 1
    assert res.total_kg >= 0
