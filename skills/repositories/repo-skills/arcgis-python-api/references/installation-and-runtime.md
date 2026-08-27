# Installation and Runtime Notes

Read this when choosing or troubleshooting an ArcGIS API for Python runtime before using any sub-skill.

## Package identity

- Python import root: `arcgis`
- Primary distribution: `arcgis`
- Mapping widget distribution used by this checkout: `arcgis-mapping`
- Repository version evidence: workspace/package pin `2.4.1`; inspection installed `arcgis 2.4.1.3` and `arcgis-mapping 4.31.0`.
- The checkout is a documentation/sample gallery and does not vendor the `arcgis` package source tree. Verify live API facts from an installed distribution.

## Runtime choices

| Runtime | Use when | Notes |
| --- | --- | --- |
| Conda/Pixi environment | You need the package plus Jupyter, mapping widgets, compiled geospatial dependencies, or repeatable notebooks. | The repository metadata pins Python 3.11 with `arcgis` and optionally `arcgis-mapping`. Prefer a private environment over mutating `base`. |
| Pip environment | You need a lightweight local import/runtime check or serverless package install. | Install `arcgis==2.4.1.*`; install `arcgis-mapping==4.31.*` when map widgets are needed. Some geospatial or deep-learning workflows may still need extra native dependencies. |
| ArcGIS Pro Python | You need integration with ArcGIS Pro, ArcPy, local geodatabases, or Pro-managed notebooks. | Use the Pro-managed environment and respect its package constraints. Do not blindly upgrade packages in that environment. |
| ArcGIS Online/Enterprise notebooks | You need managed credentials, hosted services, GPU notebook runtimes, or organization resources. | Choose Standard/Advanced/Advanced GPU runtimes according to the workflow. GPU notebooks and service calls require explicit access. |
| Docker, Lambda, Azure Functions | You need container or serverless deployment. | Use the deployment reference for distilled package/version and runtime constraints; do not run cloud deployment steps without cloud credentials and target approval. |

## Minimal install examples

Use one of these public patterns in a user-owned environment:

```bash
python -m pip install "arcgis==2.4.1.*"
python -m pip install "arcgis-mapping==4.31.*"  # map widget workflows
```

or with conda-style package management:

```bash
conda create -n arcgis-api python=3.11
conda activate arcgis-api
python -m pip install "arcgis==2.4.1.*" "arcgis-mapping==4.31.*"
```

If a corporate or ArcGIS Pro environment already owns the package stack, inspect it read-only first. Ask before upgrading, downgrading, or reinstalling.

## Safe import smoke

From the generated skill root, run:

```bash
python scripts/check_arcgis_environment.py
python scripts/check_arcgis_environment.py --json
```

The helper performs only local imports, signature inspection, and a tiny `Geometry`/`FeatureSet` construction. It does not contact ArcGIS services, open credentials, train models, download data, or mutate portal content.

Expected base surfaces for this version include:

- `arcgis.gis`
- `arcgis.features`
- `arcgis.geometry`
- `arcgis.geocoding`
- `arcgis.map`, `arcgis.map.symbols`, `arcgis.map.renderers`
- `arcgis.raster`, `arcgis.raster.functions`, `arcgis.raster.analytics`, `arcgis.raster.orthomapping`
- `arcgis.network`, `arcgis.network.analysis`
- `arcgis.geoenrichment`
- `arcgis.apps.storymap`, `arcgis.apps.expbuilder`, `arcgis.apps.itemgraph`
- `arcgis.graph`
- `arcgis.geoprocessing`

## Optional and version-sensitive surfaces

- `arcgis.learn` is optional and import-heavy. In the inspection environment, it failed with `ModuleNotFoundError: No module named 'torchvision'`. Install a compatible `torch`/`torchvision` and model-specific stack before claiming deep-learning runtime readiness.
- `arcgis.apps.dashboard` may exist while `arcgis.apps.dashboards` does not. Probe the exact module before writing dashboard code.
- `arcgis.ai` was not available in the inspected 2.4.1.3 distribution. Treat AI utility services as service/version-sensitive, not as a guaranteed local module.
- Map widgets require both Python packages and a compatible notebook front end. Import success alone does not prove browser rendering.

## Credentials and services

Most meaningful ArcGIS API workflows require one or more of:

- ArcGIS Online or ArcGIS Enterprise URL
- user credentials, token, OAuth client id, profile, or certificate files
- privileges to create, publish, share, administer, edit, analyze, or delete
- service credits, hosted locators, network-analysis services, raster analytics, image services, Knowledge Graph services, or AI services

If those are missing, provide a dry-run plan, local validation, or import/signature diagnostics only. Never invent credentials or switch to destructive operations.

## Backend summary

- Required for this generated skill: CPU/base package imports and safe local API smoke.
- Optional: GPU/deep-learning runtime for `arcgis.learn` notebooks, live ArcGIS services, Jupyter front-end rendering, and cloud/container/serverless targets.
- A CPU import is not proof of GPU training, hosted geocoding/routing/enrichment, raster analytics, or portal administration.
