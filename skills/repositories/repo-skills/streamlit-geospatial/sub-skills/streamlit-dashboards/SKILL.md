---
name: streamlit-dashboards
description: "It guides a later agent through composing Streamlit multipage
  dashboards, validating local data contracts, joining U.S. housing metrics to
  geographies, comparing historical tile layers, and deploying safely without
  mutating the host."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Streamlit dashboards

Use this sub-skill when the task is to build or repair the app shell, a data-backed
U.S. housing view, or a historical Ordnance Survey comparison in the
`streamlit-geospatial` operating graph.

## Route first

- For `Home.py` and `pages/` composition, follow
  [dashboard-workflows.md](references/dashboard-workflows.md).
- Before joining a local CSV to a boundary file, apply
  [data-contracts.md](references/data-contracts.md) and run the bundled
  [dashboard input validator](scripts/validate_dashboard_inputs.py).
- For deployment failures or unsafe host mutation, use
  [troubleshooting.md](references/troubleshooting.md).
- Route low-level Leafmap/Folium map API questions to
  [interactive-maps](../interactive-maps/SKILL.md). Route Earth Engine questions
  to [remote-geospatial-data](../remote-geospatial-data/SKILL.md).

## Operating guardrails

1. Treat remote housing and tile endpoints as versioned, drift-prone inputs. Do
   not assume a successful HTTP response has the expected schema or that every
   selected period has a matching geography.
2. Keep identifiers as strings during ingestion. Preserve leading zeroes for
   county FIPS and postal codes, and report unmatched or null geometry rather
   than silently coercing it into a map.
3. Use the validator for deterministic local checks only. It performs no remote
   downloads and writes only when an explicit `--output` path is supplied.
4. Keep the Streamlit app's working-directory assumptions explicit. Prefer an
   app-root-derived path in new code; do not make a shared host's home
   configuration part of deployment.
5. Keep the dashboard router-like: select the page workflow, data contract,
   and recovery path, then load only the reference needed for that branch.
