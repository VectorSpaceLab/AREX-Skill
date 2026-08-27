# Sample Dataset Loaders

All loaders in `orbit.utils.dataset` read remote CSV URLs with `pandas.read_csv`. They are useful for public examples, but they are not safe for offline smoke checks. Use the synthetic helpers or bundled smoke script when network access is unavailable.

## Loader map

| Loader | Signature | What it returns | Notes |
| --- | --- | --- | --- |
| `load_iclaims` | `load_iclaims(end_date="2018-06-24", transform=True)` | Weekly US initial-claims sample with Google trend and market regressors | Filters rows by `week <= end_date`. When `transform=True`, logs `claims` and the regressors, then demeans the regressors. Typical columns: `week`, `claims`, `trend.unemploy`, `trend.filling`, `trend.job`, `sp500`, `vix`. |
| `load_m4weekly` | `load_m4weekly()` | Weekly M4 sample | Typical columns: `key`, `week_num`, `value`, `date`. |
| `load_m5daily` | `load_m5daily()` | Aggregated M5 daily demand sample | Typical columns: `date`, `sales`, plus holiday/event indicator columns such as `Christmas`, `Thanksgiving`, `Sporting`, and similar flags. |
| `load_m3monthly` | `load_m3monthly()` | Monthly M3 sample | Typical columns: `key`, `value`, `date`. |
| `load_electricity_demand` | `load_electricity_demand()` | Turkish daily electricity demand sample | Builds `date` locally after reading the remote series. Typical columns: `date`, `electricity`. |
| `load_air_passengers` | `load_air_passengers()` | Prophet-style air passengers sample | Parsed on `ds`. Treat it as a network-backed tutorial dataset and inspect the returned frame before assuming any further schema. |
| `load_energy_hourly` | `load_energy_hourly()` | Hourly California demand sample | Combines `Date` and `hour` into a datetime column and drops `Date` and `HR`. Typical output columns: demand series columns plus `hour` datetime (`PGE`, `SCE`, `SDGE`, `VEA`, `CAISO`, `hour`). |

## Practical use

- Use loaders for notebook-style exploration or when a user explicitly wants one of Orbit’s public sample datasets.
- Use synthetic helpers for offline smoke checks, CI-safe examples, or any task that should not depend on the network.
- For loaders that produce a date column, normalize it with `pd.to_datetime` before calling helpers that expect a datetime series.
