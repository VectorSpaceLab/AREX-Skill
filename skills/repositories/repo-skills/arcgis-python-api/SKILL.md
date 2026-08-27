---
name: arcgis-python-api
description: "Use ArcGIS API for Python for GIS administration, spatial
  dataframes, feature/raster analysis, mapping, location services, geospatial
  deep learning, app automation, and Knowledge Graph workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ArcGIS API for Python repo skill

Use this skill when a task involves the `arcgis` Python package, ArcGIS Online or ArcGIS Enterprise automation, GIS content administration, spatially enabled dataframes, feature layers, maps, geocoding, routing, geoenrichment, imagery/raster analysis, `arcgis.learn`, StoryMaps, Experience Builder, item dependency graphs, Knowledge Graphs, or ArcGIS AI-powered services.

This repository is a documentation and sample-gallery checkout for the separately distributed `arcgis` package. Use the bundled references and scripts here instead of reopening the original checkout's notebooks or scripts.

## Start safely

1. Read [installation and runtime notes](references/installation-and-runtime.md) before choosing a package/runtime.
2. Run `python scripts/check_arcgis_environment.py` for a local import/signature smoke. The script never opens credentials, calls ArcGIS services, downloads data, trains models, or mutates content.
3. Identify whether the user task is read-only, service-backed, credentialed, credit-consuming, or destructive.
4. If credentials, target portal, service privileges, data, or hardware are missing, provide a dry-run plan or local validation only.
5. Route to exactly the sub-skill that owns the main workflow, then combine sub-skills only for cross-workflow tasks.

## Install baseline

The repository version evidence pins the `2.4.1` family. For a local user-managed environment:

```bash
python -m pip install "arcgis==2.4.1.*"
python -m pip install "arcgis-mapping==4.31.*"  # needed for map widget workflows
python scripts/check_arcgis_environment.py
```

Prefer conda/Pixi or ArcGIS Pro-managed environments when the workflow depends on compiled geospatial libraries, ArcGIS Pro, local geodatabases, or notebook widgets. Never mutate a user's ArcGIS Pro or conda `base` environment without approval.

## Route map

| User task | Use this sub-skill | Read first |
| --- | --- | --- |
| Connect to ArcGIS Online/Enterprise, manage profiles, content, items/resources, users/groups, org admin, servers, collaboration, clone/offline backups | [gis-admin-content](sub-skills/gis-admin-content/SKILL.md) | Its admin/content workflow and troubleshooting references |
| Query/edit/append feature layers, work with `FeatureSet`, Spatially Enabled DataFrames, geometry, replicas/sync, branch versioning, or feature/spatial analysis services | [features-dataframes-analysis](sub-skills/features-dataframes-analysis/SKILL.md) | Its workflows reference and `local_geometry_smoke.py` |
| Build maps/web maps/scenes, configure symbols/renderers/popups, geocode/reverse/batch geocode, route/VRP/service areas/OD matrices, or enrich/report demographics | [mapping-location-services](sub-skills/mapping-location-services/SKILL.md) | Its service API reference and import smoke |
| Use image services, `ImageryLayer`, raster functions/chains, raster analytics jobs, multidimensional rasters, or orthomapping | [imagery-raster-analysis](sub-skills/imagery-raster-analysis/SKILL.md) | Its workflow guide and raster import smoke |
| Use `arcgis.learn` for imagery/text/tabular/time-series/point-cloud geospatial ML, choose model families, train/infer/export/deploy, or fix `torchvision`/GPU dependency issues | [deep-learning](sub-skills/deep-learning/SKILL.md) | Its optional dependency probe and model catalog |
| Automate StoryMaps, Experience Builder, Hub, dashboards, Tracker/Workforce/Survey URLs, item dependency graphs, Knowledge Graphs, or AI-powered ArcGIS services | [apps-knowledge-ai-services](sub-skills/apps-knowledge-ai-services/SKILL.md) | Its module probe and app/Knowledge workflow reference |

## Shared references

- [Repository provenance](references/repo-provenance.md): source commit, package versions, evidence paths, and refresh baseline.
- [Installation and runtime notes](references/installation-and-runtime.md): package names, runtime choices, optional dependencies, credentials, services, and backend limitations.
- [Deployment and sample operations](references/deployment-and-sample-operations.md): distilled Docker, Lambda, Azure Functions, notebook gallery, and unsafe sample-maintenance script guidance.
- [Cross-cutting troubleshooting](references/troubleshooting.md): import/version, optional dependency, credentials, service, and cross-sub-skill failure handling.
- [Router metadata](references/repo-routing-metadata.json): structured placement for managed repo-skill routing.

## Non-negotiable safety rules

- Never fabricate ArcGIS credentials, profiles, item ids, organization URLs, service privileges, or credit availability.
- Treat create, publish, update, delete, clone, share, analyze, route, enrich, raster, app save, Knowledge Graph edit, and model publish calls as potentially mutating, billable, or both.
- Do not run credentialed or destructive source sample scripts as a shortcut. Their safe patterns are distilled into this skill's references.
- Do not claim that imports prove hosted service support, widget rendering, GPU training, raster analytics, network analysis, geoenrichment, Knowledge Graph service access, or ArcGIS AI services.
- Use `verify_cert=True` by default. Only use `verify_cert=False` for a controlled diagnostic against a known non-production/self-signed endpoint after warning the user.
- Keep passwords, tokens, API keys, OAuth secrets, certificate passwords, and profile contents out of code, logs, and final answers.

## Cross-workflow patterns

- CSV to hosted feature layer to map: content/publish with `gis-admin-content`, schema/edit validation with `features-dataframes-analysis`, visualization with `mapping-location-services`.
- Imagery model inference and publishing: dependency/GPU/model checks with `deep-learning`, image-service/raster output decisions with `imagery-raster-analysis`, portal publish/share with `gis-admin-content`.
- StoryMap clone with dependent layers: app relationship logic with `apps-knowledge-ai-services`, item ownership/resources/sharing with `gis-admin-content`, feature-layer schema only if data edits are needed.
- Enriched routing or territory analysis: geocode/network/enrich with `mapping-location-services`, local geometry/SEDF or hosted feature prep with `features-dataframes-analysis`.

## Verification status to preserve

The generated skill was verified for base CPU/import/signature behavior of the installed `arcgis` and `arcgis-mapping` packages. No live ArcGIS service calls, destructive admin scripts, cloud deployments, notebook executions, large downloads, or GPU model training were run during production. Optional surfaces such as `arcgis.learn`, `arcgis.ai`, and dashboard module names are explicitly probed by sub-skill scripts before use.
