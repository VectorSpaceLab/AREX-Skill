---
schema: disco.repo-provenance.v1
---

# Repository provenance

- Repository: Megatron-LM / Megatron Core
- Public remote: `https://github.com/NVIDIA/Megatron-LM.git`
- Source commit: `78901d8a71b92ed19e3e31e00815e6bde558e9de`
- Branch: `main`
- Exact tag at source commit: none detected
- Package distribution: `megatron-core`
- Package version at source: `0.20.0` (installed inspection reported `0.20.0+78901d8` with VCS suffix)
- Python metadata: `>=3.12`
- Source package roots: `megatron/core`, `megatron/training`
- Checkout state: generated from a dirty working tree. The original source snapshot was clean except for production/review artifacts under `skills/`; those artifacts are not runtime evidence.
- Evidence families distilled: `README.md`, `pyproject.toml`, `setup.py`, `megatron/core`, `megatron/training`, selected top-level training entrypoints, `docs/get-started`, `docs/user-guide`, `docs/api-guide`, `docs/developer`, selected `examples`, `tools`, `tests`, `docker`, CI metadata, and existing repo-local skills.
- Optional/unverified surfaces: TransformerEngine/Apex/ModelOpt/Mamba/FlashMLA/DeepGEMM full installs, H100/GB200/FP8-specific execution, large multi-node jobs, credential/network-bound CI downloads, and the historical academic-paper scripts.
- Refresh trigger: compare the current package version, source commit, public API signatures, dependency groups, parallelism flags, checkpoint formats, and CI recipe conventions before relying on this graph for a newer checkout.
