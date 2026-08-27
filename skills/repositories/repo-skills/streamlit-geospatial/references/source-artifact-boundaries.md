# Source artifact boundaries

This reference records how repository evidence was converted into the
self-contained operating graph. Future agents should use the bundled runtime
files below rather than reopening the original checkout.

| Source artifact | Runtime replacement | Decision |
|---|---|---|
| `Home.py` and numbered `pages/*.py` | Root and sub-skill routers, API/workflow references, and safe validators | Distilled/adapted; full page scripts depend on Streamlit session state, external services, or local working-directory assumptions |
| `requirements.txt` | `references/installation-and-deployment.md` and `scripts/check_environment.py` | Distilled with observed Python 3.11 import facts |
| `packages.txt`, `setup.sh`, `Procfile` | Installation/deployment reference and troubleshooting | Reference-only because host package installation and home-directory config mutation are side effects |
| `data/cog_files.txt` and `data/scotland_xyz.tsv` | Interactive-map data-format and historical-layer guidance | Distilled; external URLs remain prerequisites, not checkout dependencies |
| `data/realtor_data_dict.csv` and `data/us_*.geojson` | Dashboard data-contract reference and local validator contract | Distilled; no runtime instruction points to source data paths |
| `.github/FUNDING.yml` and `skills/streamlit-geospatial.log` | None | Excluded as non-workflow metadata/process artifact |

No runtime file instructs a later Researcher to run an original source page,
read an original repository document, or use an absolute checkout path.
