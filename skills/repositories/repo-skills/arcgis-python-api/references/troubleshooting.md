# Cross-Cutting Troubleshooting

Read this before diagnosing an ArcGIS API for Python failure that is not clearly owned by one sub-skill.

## 1) Import or version failure

Symptoms:
- `ModuleNotFoundError: No module named 'arcgis'`
- `ModuleNotFoundError: No module named 'arcgis.map'`
- map widgets fail after installing only `arcgis`
- an example mentions a module that is absent in the installed distribution

Recovery:
1. Run `python scripts/check_arcgis_environment.py --json` from the skill root.
2. Confirm `arcgis` version and whether `arcgis-mapping` is installed.
3. Install the version family that matches the task or repo snapshot, for example `arcgis==2.4.1.*` and `arcgis-mapping==4.31.*` for this skill's baseline.
4. If the task comes from a newer/older notebook, check the current package docs or refresh the repo skill rather than inventing an API.
5. For app/AI/dashboard/deep-learning modules, use the owning sub-skill probes because those surfaces are version-sensitive.

## 2) Optional dependency or backend failure

Symptoms:
- `import arcgis.learn` fails with `No module named 'torchvision'`
- GPU notebook code starts but CUDA is unavailable
- widget imports pass but no map renders
- raster or network analysis imports pass but service calls are unsupported

Recovery:
- Deep learning: use `sub-skills/deep-learning/scripts/check_learn_optional_deps.py`; install a compatible `torch`/`torchvision` and model-specific stack before training.
- Mapping widgets: verify `arcgis-mapping`, `ipywidgets`, JupyterLab/front-end extension compatibility, and browser display context.
- Hosted services: distinguish local package import from remote service availability. Confirm privileges, credits, and service URLs.
- GPU examples: a CPU import is not a substitute for GPU training/inference evidence.

## 3) Credentials, profiles, and certificates

Symptoms:
- `GIS(profile=...)` cannot find a profile or opens the wrong org
- login works interactively but fails in a notebook/serverless runtime
- certificate/PFX or Kerberos/IWA authentication fails
- SSL verification errors lead the user to ask for `verify_cert=False`

Recovery:
1. Never print or store credentials in generated code.
2. Confirm the target ArcGIS Online/Enterprise URL and authenticated identity.
3. Recreate or repair profiles outside the response if profile contents are unknown.
4. Keep `verify_cert=True` by default. Only use `verify_cert=False` as a temporary diagnostic against a known self-signed/non-production endpoint.
5. For admin/content tasks, use the `gis-admin-content` troubleshooting reference.

## 4) Service call unexpectedly mutates content or consumes credits

Symptoms:
- A geocode/network/enrich/analysis/raster call creates hosted outputs or charges credits.
- A content/admin script deletes or republishes items.
- A map/app/StoryMap/Experience Builder operation saves changes to the wrong item.

Recovery:
- Treat every create, publish, update, delete, clone, share, analyze, route, enrich, raster, save, duplicate, or apply-edits call as potentially mutating or billable.
- Before running, collect target portal, owner/folder, output name, sharing, service credit expectations, and rollback/cleanup plan.
- Use a dry-run inventory or local validation when credentials or approval are missing.
- Use unique output names for server-side analysis and raster jobs.

## 5) User task crosses sub-skill boundaries

Use the root router and then combine the relevant sub-skills:

- Publish a CSV, update a feature layer, then map it: `gis-admin-content` for content/publish, `features-dataframes-analysis` for schema/edits, `mapping-location-services` for map/widget.
- Run object detection on imagery and publish results: `deep-learning` for model/data/gpu, `imagery-raster-analysis` for image services/raster outputs, `gis-admin-content` for publish/share.
- Clone a StoryMap with dependent maps and feature layers: `apps-knowledge-ai-services` for app/relationship semantics, `gis-admin-content` for item ownership/sharing/cloning, `features-dataframes-analysis` for hosted layers if edited.
- Build an enriched route/territory analysis: `mapping-location-services` for geocode/network/enrich, `features-dataframes-analysis` for layer schema/local geometry.

## 6) When to stop instead of trying a workaround

Stop and ask for more information when:

- credentials, tokens, certificates, or target portal are missing for a service call;
- the operation could delete, overwrite, share, publish, clone, or bill credits and the user has not approved it;
- the required service backend is unavailable (`raster analytics`, `network analysis`, `geoenrichment`, `Knowledge Graph`, AI services, GPU runtime);
- the package version lacks the module the user requested;
- the user asks to run a repository sample script that contains hard-coded credentials or destructive side effects;
- a notebook requires large data/model downloads or training-scale compute.

Provide a bounded dry-run plan, validation checklist, or import smoke result instead of fabricating live success.
