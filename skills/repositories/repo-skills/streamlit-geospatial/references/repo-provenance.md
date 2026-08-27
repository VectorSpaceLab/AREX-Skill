# Repository Provenance

## Purpose

Read this before deciding whether the operating graph matches a checkout of
`streamlit-geospatial`. If the source commit, dirty state, package dependency
surface, or major evidence paths differ, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T21:06:34Z",
  "repository": {
    "name": "streamlit-geospatial",
    "remote_url": "https://github.com/opengeos/streamlit-geospatial.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "b327acc3d82380ae298cf90bee6beec471a450aa",
    "working_tree": "clean at extraction start",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "streamlit-geospatial application requirements",
      "version": null,
      "import_names": [
        "streamlit", "leafmap", "geemap", "geopandas", "fiona", "folium",
        "pydeck", "ee", "rasterio", "localtileserver", "keplergl"
      ]
    }
  ],
  "evidence": {
    "source_roots": [],
    "docs": ["README.md"],
    "examples": ["Home.py", "pages"],
    "tests": [],
    "configs": ["requirements.txt", "packages.txt", "setup.sh", "Procfile", "index.html"]
  },
  "inspection": {
    "python": "3.11",
    "verified_distributions": {
      "streamlit": "1.62.0",
      "leafmap": "0.63.1",
      "geemap": "0.37.2",
      "geopandas": "1.1.4",
      "fiona": "1.10.1",
      "earthengine-api": "1.7.40",
      "localtileserver": "1.0.0",
      "keplergl": "0.3.7",
      "rasterio": "1.4.4"
    },
    "important_runtime_note": "Set USE_FOLIUM=1 before importing geemap.foliumap in the inspected workflow."
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the graph as
  potentially stale and run `refresh-repo-skill`.
- If the checkout changes from the clean extraction baseline, especially
  `Home.py`, `pages/`, `requirements.txt`, `packages.txt`, `setup.sh`, or
  `Procfile`, refresh before relying on version-sensitive details.
- If Leafmap/geemap signatures, Streamlit backend behavior, or external-data
  contracts change, refresh the affected sub-skill even when the source commit
  is unchanged.
