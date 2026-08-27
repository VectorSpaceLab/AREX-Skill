# Repo Provenance

This OmegaFold repo skill was generated from repository evidence and live package inspection so future agents can detect staleness before using it.

## Source Snapshot

| Field | Value |
| --- | --- |
| Repository branding | OmegaFold |
| Canonical skill id | `omega-fold` |
| VCS | git |
| Commit | `313c873ad190b64506a497c926649e15fcd88fcd` |
| Branch | `main` |
| Exact tag | none detected |
| Remote URL | `https://github.com/HeliXonProtein/OmegaFold.git` |
| Working tree state | dirty: generated `skills/` directory was untracked during skill creation |
| Distribution metadata name | `OmegaFold` |
| Package version observed | `0.0.0` |
| Import module verified | `omegafold` |

## Evidence Paths

The runtime skill was based on these repository-relative evidence paths:

- `README.md`
- `setup.py`
- `requirements.txt`
- `main.py`
- `omegafold/__init__.py`
- `omegafold/__main__.py`
- `omegafold/pipeline.py`
- `omegafold/config.py`
- `omegafold/model.py`
- `omegafold/confidence.py`
- `omegafold/modules.py`
- `omegafold/embedders.py`
- `omegafold/omegaplm.py`
- `omegafold/decode.py`
- `omegafold/utils/__init__.py`
- `omegafold/utils/torch_utils.py`
- `omegafold/utils/protein_utils/functions.py`
- `omegafold/utils/protein_utils/aaframe.py`
- `omegafold/utils/protein_utils/residue_constants.py`
- `LICENSE`

## Live Inspection Baseline

Verified package facts included:

- `omegafold` imports successfully in a compatible Python 3.10 inspection environment.
- `omegafold --help` exposes the expected CLI flags.
- `omegafold.make_config(1)` and `omegafold.make_config(2)` work; `make_config(3)` raises `ValueError`.
- `pipeline.fasta2inputs` runs on a tiny CPU FASTA fixture.
- `pipeline.save_pdb` is safe to exercise with synthetic atom14 tensors.
- Torch 1.12 with NumPy 2.x is a compatibility pitfall; `numpy<2` was required for clean legacy inspection.

## Refresh Triggers

Refresh this skill when any of these change:

- CLI flags, default checkpoint URLs, model ids, or weight cache behavior.
- FASTA parsing, residue normalization, output naming, or PDB/confidence writing.
- Public APIs such as `make_config`, `OmegaFold.forward`, `pipeline.fasta2inputs`, or `pipeline.save_pdb`.
- Python/Torch/Biopython compatibility or installation metadata.
- New examples, tests, docs, model releases, or supported workflows are added.
