# AlphaFold Package Overview

AlphaFold 2.3.2 is an implementation of the AlphaFold v2 inference pipeline for protein structure prediction, including monomer, monomer pTM, CASP14-style monomer, and AlphaFold-Multimer v3 presets.

## Public Surfaces

| Surface | Use for | Skill route |
| --- | --- | --- |
| `run_alphafold` console script | Direct local prediction command planning and flag validation | `sub-skills/prediction-cli/` |
| Docker image/entrypoint | Documented containerized prediction path with GPU and mounted data | `sub-skills/docker-and-data-setup/` |
| `alphafold.data` | FASTA, MSA, template, monomer, and multimer feature pipelines | `sub-skills/input-data-and-formats/` |
| `alphafold.model` | Model presets, config objects, parameter loading, feature processing, JAX/Haiku model execution | `sub-skills/model-config-and-api/` |
| `alphafold.common` | Protein object, PDB/mmCIF conversion, pLDDT, PAE, pTM/ipTM confidence helpers | `sub-skills/outputs-and-confidence/` |
| `alphafold.relax` | Amber/OpenMM relaxation and structural violation analysis | `sub-skills/relaxation/` |
| AFDB and Server JSON docs | Prediction database file formats and AlphaFold Server automation JSON | `sub-skills/outputs-and-confidence/` |

## Runtime Requirements

A complete prediction run needs more than the Python package:

- Linux host or compatible Linux container path.
- Model parameter files under a data directory `params/`.
- Genetic/template databases such as UniRef90, MGnify, PDB mmCIF, obsolete PDB map, PDB70 or PDB SeqRes/UniProt, plus BFD/UniRef30 or small BFD depending on `db_preset`.
- External binaries: JackHMMER, HHblits, HHsearch, HMMsearch, HMMbuild, and Kalign for the direct local pipeline.
- JAX/Haiku/TensorFlow/NumPy dependency compatibility.
- OpenMM/PDBFixer for relaxation.
- Substantial CPU, RAM, disk, and normally NVIDIA GPU resources for practical full inference.

## Safe Helper Strategy

Bundled helper scripts are intentionally dry-run or local-inspection tools:

- `scripts/check_install.py` verifies imports, versions, entry points, external binary discovery, and optional OpenMM/Docker/JAX signals.
- `sub-skills/docker-and-data-setup/scripts/plan_docker_command.py` plans a `docker run` command and mount map without contacting Docker.
- `sub-skills/docker-and-data-setup/scripts/plan_data_downloads.py` prints database/model-parameter layout and update plans without downloading.
- `sub-skills/prediction-cli/scripts/check_prediction_inputs.py` validates direct CLI flags and data-path expectations without inference.
- `sub-skills/input-data-and-formats/scripts/validate_fasta.py` validates FASTA files without external searches.
- `sub-skills/model-config-and-api/scripts/inspect_model_presets.py` prints presets/config fields without loading weights.
- `sub-skills/outputs-and-confidence/scripts/inspect_confidence_json.py` summarizes local confidence/PAE JSON without importing AlphaFold.
- `sub-skills/relaxation/scripts/check_relaxation_inputs.py` triages PDB-like files without minimization.

## Model and Database Presets

| Preset | Meaning | Key data implication |
| --- | --- | --- |
| `monomer` | Standard five monomer models | Uses PDB70 templates and monomer database flags |
| `monomer_casp14` | Monomer models with CASP14-style ensembling | Slower; mostly reproducibility-oriented |
| `monomer_ptm` | Monomer pTM models that can emit PAE/pTM confidence | Uses monomer database flags |
| `multimer` | AlphaFold-Multimer v3 models | Requires multimer input and UniProt plus PDB SeqRes paths |
| `full_dbs` | Full BFD plus UniRef30 | Larger disk/time; no `small_bfd_database_path` |
| `reduced_dbs` | Small BFD path instead of BFD/UniRef30 | Lower disk/time; no `bfd_database_path` or `uniref30_database_path` |

## Expensive or External Operations

Ask for explicit approval before running or recommending immediate execution of:

- Full or reduced database downloads.
- Model parameter downloads.
- Docker image builds or Docker container runs.
- Full `run_alphafold` inference, benchmark mode, or relaxation minimization.
- AFDB GCS/BigQuery bulk queries or downloads that may incur costs.

Use the bundled planners and validators first so command proposals are precise and auditable.
