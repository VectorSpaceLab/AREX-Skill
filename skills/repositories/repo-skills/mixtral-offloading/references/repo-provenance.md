# Repository provenance

Schema: `disco.repo-provenance.v1`

## Source snapshot

- Repository: `dvmazur/mixtral-offloading`
- Public remote: `https://github.com/dvmazur/mixtral-offloading.git`
- Branch: `master`
- Commit: `ce545188b804238f0b23a59fc45e6a8f8b390c40`
- Exact tag: none detected
- License: MIT
- Package version: not declared; repository is source-only and has no package metadata

## Dirty-state note

At generation time, the checkout had untracked `skills/` outputs created by the
skill-production workflow. Source evidence files used for this skill were the
tracked repository files at the commit above.

## Evidence paths

- `README.md`
- `requirements.txt`
- `notebooks/demo.ipynb`
- `src/build_model.py`
- `src/custom_layers.py`
- `src/expert_cache.py`
- `src/expert_wrapper.py`
- `src/packing.py`
- `src/triton_kernels.py`
- `src/utils.py`
- `LICENSE`

## Runtime dependency facts verified during creation

A private inspection environment verified imports and CUDA readiness for:

- PyTorch 2.13.0 with CUDA runtime available
- Transformers 4.36.1
- HQQ 0.1.1 from the repository-pinned HQQ commit
- Triton 3.7.1
- safetensors 0.8.0
- NumPy 1.24.4
- tqdm 4.66.1

The public skill does not depend on that private environment. Future agents
should verify their own environment with the bundled scripts.

## Known verification limits

- Full Mixtral generation was not run during creation because it requires large
  external model artifacts, network/disk approval, CUDA memory, and an
  interactive or long-running workload.
- Tiny CUDA and source-level smokes were used to verify the environment and the
  generated guidance.
- HQQ may warn that `hqq_aten` is not installed. This skill covers the repo's
  Triton-backed path and does not claim ATEN backend support.
