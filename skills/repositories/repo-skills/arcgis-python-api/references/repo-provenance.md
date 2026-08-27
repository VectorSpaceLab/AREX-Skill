# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of `Esri/arcgis-python-api`. If the current repository commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the skill for new work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:24:27Z",
  "repository": {
    "name": "arcgis-python-api",
    "remote_url": "https://github.com/Esri/arcgis-python-api.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "40959e7c315af675b1323152db0c9b5f5e9a3fae",
    "working_tree": "dirty-generated-artifacts-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "arcgis",
      "version": "2.4.1.3",
      "import_names": ["arcgis"]
    },
    {
      "name": "arcgis-mapping",
      "version": "4.31.0",
      "import_names": ["arcgis.map", "arcgis.mapping"]
    }
  ],
  "evidence": {
    "source_roots": [],
    "docs": [
      "README.md",
      "apidoc/README.md",
      "guide/01-getting-started",
      "guide/02-api-overview",
      "guide/03-the-gis",
      "guide/04-feature-data-and-analysis",
      "guide/05-working-with-the-spatially-enabled-dataframe",
      "guide/06-imagery-and-raster-analysis",
      "guide/08-using-geoprocessing-tools",
      "guide/09-finding-places-with-geocoding",
      "guide/10-mapping-and-visualization",
      "guide/11-performing-network-analyses",
      "guide/12-enrich-data-with-thematic-information",
      "guide/13-managing-arcgis-applications",
      "guide/14-deep-learning",
      "guide/15-working-with-geometries",
      "guide/16-introduction-to-data-engineering-in-python",
      "guide/17-working-with-knowledge-graphs",
      "guide/18-working-with-AI-capabilities"
    ],
    "examples": [
      "samples/01_get_started",
      "samples/02_power_users_developers",
      "samples/03_org_administrators",
      "samples/04_gis_analysts_data_scientists",
      "samples/05_content_publishers",
      "labs"
    ],
    "tests": [],
    "configs": [
      "environment.yml",
      "pixi.toml",
      "items_metadata.yaml",
      "docker/README.md",
      "docker/NotebookImage.Dockerfile",
      "docker/LambdaBaseImage.Dockerfile",
      "samples/devops_azure_functions/requirements.txt"
    ],
    "scripts": [
      "update_items.py",
      "misc/_common.py",
      "misc/setup.py",
      "misc/teardown.py",
      "misc/tools/replace_profiles.py",
      "samples/03_org_administrators/AdminCreatePortal",
      "samples/03_org_administrators/AdminClonePortal/clone_portal.py",
      "samples/devops_azure_functions/function_app.py"
    ]
  },
  "notes": [
    "This checkout is a documentation, guide, lab, and sample-gallery repository. It does not contain the arcgis package source tree, so live API facts were verified from installed public distributions.",
    "The dirty skills/ path is production output, not upstream source evidence.",
    "No ArcGIS credentials were available during generation, so service-backed notebooks/scripts were not executed."
  ]
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If upstream docs, notebooks, package pins, Docker recipes, or major sample directories change, refresh even if the high-level package name stays the same.
- If the installed `arcgis` or `arcgis-mapping` versions differ from the recorded versions, rerun the bundled environment checks and update version-sensitive module notes.
- If a future environment exposes `arcgis.learn`, `arcgis.ai`, or dashboard modules differently, refresh the affected sub-skill references before claiming support.
- If the current checkout has dirty paths outside generated `skills/` artifacts, refresh or inspect those changes before using this skill as current evidence.
