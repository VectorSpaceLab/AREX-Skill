# Repo provenance

This skill was distilled from RoboSat source evidence at the repository snapshot below. Use this file to decide whether the skill should be refreshed for a newer checkout.

| Field | Value |
| --- | --- |
| Repository | `mapbox/robosat` |
| Public remote | `https://github.com/mapbox/robosat.git` |
| Branch | `master` |
| Commit | `4eecaff9023f6f684111b82fefa7d1dea384065a` |
| Exact tag | none detected |
| Package distribution | `robosat` |
| Package version | `1.2.0` |
| License | MIT |
| Maintenance note | The project README says RoboSat is no longer actively developed by Mapbox. Treat it as legacy software. |

## Working tree state at skill generation

The checkout was dirty because local production artifacts were present or created under `skills/`, and editable installation created `robosat.egg-info/` during private environment inspection. Source evidence used for this skill came from the committed package, docs, configs, Docker/CI files, and tests listed below; no source package file modifications were used as evidence.

Relative dirty paths observed during generation:

- `skills/`
- `robosat.egg-info/`

## Evidence paths

The generated skill distilled the following relative evidence paths:

- `README.md`
- `setup.py`
- `requirements.in`
- `requirements.txt`
- `.travis.yml`
- `Makefile`
- `rs`
- `config/dataset-parking.toml`
- `config/model-unet.toml`
- `docker/Dockerfile.cpu`
- `docker/Dockerfile.gpu`
- `robosat/`
- `robosat/tools/`
- `robosat/features/`
- `robosat/graph/`
- `robosat/osm/`
- `robosat/spatial/`
- `tests/`

## Environment verification summary

Private setup verified a CPU inspection environment with Python 3.6, RoboSat `1.2.0`, installed `rs` CLI help, all subcommand help, `rtree` with `libspatialindex`, `pyproj` ESRI CRS lookup, torch CPU import, and a `UNet(pretrained=False)` CPU forward smoke. CUDA/GPU behavior was not verified for this skill generation.

Do not copy private environment prefixes, local checkout paths, or setup logs into user-facing runtime instructions.
