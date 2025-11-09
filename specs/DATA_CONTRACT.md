# Data Contract (v0)

## 1) clubs.csv
Required:
- club (string, unique, case-insensitive)
- stadium (string)
- lat (float −90..90)
- lon (float −180..180)

Rules:
- No duplicate club keys; trim whitespace.
- WGS84 decimal; ≥ 4 dp preferred.

## 2) factors.yaml
```yaml
version: 2025.1
units: kg_co2e_per_pkm
factors:
  default:
    train: 0.041
    coach: 0.027
    car: 0.120
    flight:
      short_haul: 0.255
notes: "Starter defaults; replace with sourced, country profiles."
