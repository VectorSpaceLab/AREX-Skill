# city2graph provenance

`schema: disco.repo-provenance.v1`

- **Package:** `city2graph`
- **Version:** `1.0.0`
- **Source commit:** `1fc5321770cdc4df4cf9cee21e3e41ff6e0e5cd2`
- **Branch:** `main`
- **Snapshot state:** The source checkout was clean before generated `skills/` output was added; the generated runtime tree is intentionally separate from source evidence.
- **Evidence used:** `city2graph/__init__.py`; `city2graph/base.py`; `city2graph/graph.py`; `city2graph/metapath.py`; `city2graph/proximity.py`; `city2graph/morphology.py`; `city2graph/mobility.py`; `city2graph/transportation.py`; `city2graph/data.py`; `city2graph/utils/conversion.py`; `city2graph/utils/spatial.py`; `city2graph/utils/topology.py`; `docs/installation.md`; `docs/api/`; `docs/examples/index.md`; distilled tutorial notebook evidence; `tests/`; `pyproject.toml`; `uv.lock`; and CI test-command evidence.
- **Generated coverage:** graph conversion; spatial topology; urban morphology; mobility and transport; Overture data ingestion; and package-wide troubleshooting/routing.
- **Verification boundary:** Core Python and CPU PyTorch Geometric paths are selected for native verification. Live Overture/Nominatim/GTFS/GBFS services, large downloads, training-scale execution, and CUDA/ROCm/MPS execution are not runtime requirements and are not claimed as verified.
- **Staleness rule:** Refresh this skill when the package version, public signatures, index/CRS contracts, dependency extras, or the listed source commit changes materially.

The runtime skill contains distilled operating guidance only. It must remain usable when the original checkout, its notebooks, fixtures, and local Python environment are unavailable.
