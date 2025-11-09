# Green-Matchday
Open-source estimator for football away-day travel emissions (clubs &amp; fans).

## Quick test (local)
If you clone the repo locally, you can run a quick Python check:

```python
from green_matchday.engine import estimate_fixture
res = estimate_fixture("West Ham United","Leeds United","data/clubs.csv",away_fans=3000)
print(res)
