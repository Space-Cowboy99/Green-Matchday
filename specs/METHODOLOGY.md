# Methodology (draft)
- Distance: haversine (Earth radius 6371.0 km)
- Per-fan: distance_km × Σ(mode_share[m] × factor[m])
- Total: per_fan × away_fans
- Rounding: distance 2–3 dp; per_fan 2 dp; total in kg
- Future toggles: flight radiative forcing, occupancy models, country factors
