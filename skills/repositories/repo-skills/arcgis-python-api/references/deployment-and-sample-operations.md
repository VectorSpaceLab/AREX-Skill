# Deployment and Sample Operations

Read this when a task is about running the repository's notebooks in managed venues, packaging ArcGIS API for Python into containers/serverless functions, or interpreting the repository's sample-maintenance scripts.

## Notebook gallery execution venues

The repository documents several venues for its guide, sample, and lab notebooks:

| Venue | Best for | Preflight |
| --- | --- | --- |
| Local Anaconda/conda or Pixi | Exploratory notebooks with local files and package control. | Verify `arcgis`, optional `arcgis-mapping`, Jupyter kernel, and any local geospatial IO dependencies. |
| ArcGIS Pro notebooks | Workflows that need ArcGIS Pro, ArcPy, local geodatabases, Pro licensing, or Pro-managed credentials. | Do not mutate the Pro environment without approval; check Pro version compatibility. |
| ArcGIS Online/Enterprise notebooks | Hosted GIS services, organization content, server-side analysis, and GPU runtimes. | Confirm runtime tier, credentials, privileges, credits, and target org. |
| Docker/Jupyter image | Reproducible notebook server with package pins. | Build only with an approved Docker daemon, image registry, and package source. |
| Binder/public notebooks | Lightweight demos without private services. | Avoid private data, credentials, and expensive service calls. |

## Docker and serverless patterns

The repo's Docker evidence uses these patterns:

- Notebook image: create a Python environment, install geospatial foundations, install `arcgis`, install `arcgis-mapping` for 2.4+ mapping widgets, fetch sample notebooks, and register a Jupyter kernel.
- Lambda image: start from a Python Lambda base image, install OS libraries needed by authentication/native dependencies, `pip install arcgis` into the Lambda task root, and provide a handler such as:

```python
import arcgis

def handler(event, context):
    return f"ArcGIS API for Python {arcgis.__version__}"
```

- Azure Functions sample: a function handler imports `arcgis` and returns its version, but actual deployment requires the Azure Functions runtime and cloud configuration.

Use these as patterns, not as a command to run automatically. Building or pushing images and deploying functions requires explicit cloud credentials, a target project, and approval.

## Runtime deployment checklist

1. Identify the target: local notebook, ArcGIS Pro, hosted notebook, Docker, Lambda, or Azure Functions.
2. Verify package versions with `scripts/check_arcgis_environment.py` before adding service calls.
3. Confirm the target has the required credentials, profiles, certificates, service credits, and network reachability.
4. For map widgets, check both `arcgis-mapping` import and front-end/JupyterLab compatibility.
5. For `arcgis.learn`, run the deep-learning optional dependency probe before scheduling GPU work.
6. For serverless, avoid workflows that need browser widgets, interactive passwords, GPU training, long-running jobs, or large local data unless the platform explicitly supports them.
7. For hosted analysis/raster/geocoding/network/enrichment, design idempotency and output cleanup before running jobs.

## Sample maintenance scripts are not runtime helpers

The source repository includes scripts used to maintain or stage Esri sample content. Future agents should not run them as part of ordinary ArcGIS API usage unless the user explicitly asks for repository/sample-gallery maintenance and accepts the side effects.

| Source operation class | Why it is risky | Safe use in this skill |
| --- | --- | --- |
| Notebook gallery item upload/update | Uploads notebooks and resources to a portal, modifies item metadata, can change sharing and runtime stamps. | Use only as evidence for metadata, item/resource, and upload workflows. |
| Profile replacement in notebooks | Rewrites notebooks and can insert demo credentials. | Do not run; explain profile concepts without copying credentials. |
| Portal cleanup/setup/teardown | Deletes or creates users, groups, items, services, and tracking configuration. | Use only as safety evidence for admin preflight/rollback. |
| Portal clone scripts | Create users/groups/items and remap dependencies across portals. | Distill migration checklists; require explicit credentials and dry-run inventory before mutation. |
| Cloud/container builds | Pull packages, build images, or deploy to cloud services. | Provide patterns and preflight only until the user supplies a target and credentials. |

## Safe alternatives bundled in this skill

- Root `scripts/check_arcgis_environment.py`: local import/signature smoke.
- `sub-skills/features-dataframes-analysis/scripts/local_geometry_smoke.py`: local geometry, FeatureSet, and SEDF smoke.
- `sub-skills/mapping-location-services/scripts/check_location_service_imports.py`: map/location/geocoding/network/enrich import/signature smoke.
- `sub-skills/imagery-raster-analysis/scripts/raster_import_smoke.py`: raster/imagery import/signature smoke.
- `sub-skills/deep-learning/scripts/check_learn_optional_deps.py`: optional deep-learning dependency/CUDA probe.
- `sub-skills/apps-knowledge-ai-services/scripts/check_apps_modules.py`: app/graph/AI module availability probe.

These helpers are deterministic and avoid network, credentials, destructive mutations, model downloads, and cloud deployment.
