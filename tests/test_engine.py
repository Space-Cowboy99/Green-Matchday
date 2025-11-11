from green_matchday.engine import estimate_fixture

def test_estimate_fixture_basic():
    r = estimate_fixture("West Ham United","Leeds United","data/clubs.csv", away_fans=3000)
    assert hasattr(r, "total_kg")
    assert r.total_kg > 0
