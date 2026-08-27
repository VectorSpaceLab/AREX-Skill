# Troubleshooting

This file covers cross-cutting CubeStudio failures that do not belong to one narrow sub-skill.

## Common symptoms

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Backend import fails early | runtime overlay files are missing or wrong | confirm the overlay model rather than the placeholder files |
| Import error mentions `Myauthdbview` or similar | the runtime project overlay is not providing the custom auth view | inspect the deployment overlay, not the empty placeholder |
| SQLite with `pool_size` / `max_overflow` errors | the backend config was not adapted for the chosen database backend | use the documented runtime database path for the environment |
| Flask emits a `Markup` deprecation warning | the code path still references the older Flask export | treat it as a compatibility warning, not a platform outage |
| SQLAlchemy warns about `ab_user.active` being combined | the custom user model extends the FAB base model with a same-named column | note it in compatibility review; it does not by itself block startup |
| DB / Redis boot fails | the runtime database URL or Redis settings are wrong | verify the configured service endpoints and credentials |
| Pipeline / serving / notebook objects do not appear in the UI | model/view registration or runtime init did not complete | check app startup, permissions, and init order |
| Docker Compose renders but services do not boot | image, volume, or entrypoint assumptions are wrong | inspect the compose bundle and the overlay files |
| Kubernetes install path fails | CRD / namespace / secret / storage ordering is wrong | use the deployment sub-skill's manifest order reference |

## Recovery approach

1. Decide whether the symptom is about deployment, backend customization, notebook resources, pipelines, data, or serving.
2. Open the owning sub-skill's troubleshooting file for the detailed failure tree.
3. Use the bundled static helper scripts to inspect the checkout or payload shape before editing live systems.
4. Only after the static problem is understood should an operator touch Docker, Kubernetes, or live service endpoints.

## What to avoid

- Do not rely on the checked-in empty placeholders as though they were full runtime config files.
- Do not use a passing import check as proof that live services, databases, or clusters are healthy.
- Do not treat a successful static inventory as permission to run mutate-heavy install scripts.
- Do not duplicate sub-skill troubleshooting matrices here unless the issue is truly cross-cutting.

## Best follow-up references

- `configuration-and-catalogs.md` for runtime knobs and seed catalogs
- `platform-overview.md` for the repo structure and route map
- the relevant sub-skill `references/troubleshooting.md` for workflow-specific recovery paths
