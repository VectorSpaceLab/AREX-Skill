---
name: hardware-and-models
description: "Operate on ODS GPU/backend detection, hardware tiers, model
  catalogs, inference overlays, and model lifecycle safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ODS hardware and models sub-skill

Use this sub-skill when an ODS task touches GPU/backend detection, hardware class or tier mapping, backend contracts, model catalog/profile selection, inference backend compose overlays, model download/load/swap behavior, bootstrap-to-full model upgrades, or model-state lifecycle.

Do not use this sub-skill for dashboard model UI implementation details; route those to `dashboard-and-api`. Do not use it for end-user `ods model` command syntax or host-agent command dispatch; route those to `ops-cli-and-host-tools`. For broad release lane selection, route to `testing-and-release` after identifying the owning hardware/model files.

## Operating workflow

1. For backend, detection, tier, compose overlay, and exact file/test ownership, read [`references/backend-and-tier-reference.md`](references/backend-and-tier-reference.md).
2. For model catalog selection, downloads, bootstrap/full swaps, model-state, and lifecycle workflows, read [`references/model-management-workflows.md`](references/model-management-workflows.md).
3. For symptoms and repair decisions, read [`references/troubleshooting.md`](references/troubleshooting.md).
4. To inspect a local ODS source tree without mutation, run:

   ```bash
   python3 scripts/inspect_model_catalog.py --root <ODS_SOURCE_OR_PROJECT_ROOT>
   ```

   The helper is read-only. It summarizes `config/model-library.json`, `config/backends/*.json`, and hardware class data if those files are present.

## Safety and evidence rules

- Separate product capability claims from current verification. Source evidence documents ODS support for NVIDIA/CUDA, AMD/Lemonade/ROCm/Vulkan, Intel Arc/SYCL, Apple Metal/native llama-server, CPU fallback, and cloud/API modes, but a future agent may claim live GPU validation only after running the matching host-specific checks.
- Repo-skill verification for this sub-skill can use safe CPU/host static checks. GPU smoke tests, model downloads, installers, Docker lifecycle, and backend health probes are product validations that require explicit user intent and suitable hardware.
- Treat tier/model throughput estimates as catalog or source estimates until measured on the user's host.
- Prefer read-only inspection and focused native tests before any installer, download, compose, or model activation action.

## Common change routing

- Hardware classification or backend default: inspect/update detection, classifier, hardware class, backend contract, and compose selection facts; validate with the exact tests listed in the backend/tier reference.
- Tier-to-model or profile change: inspect/update Linux, macOS, and Windows tier maps plus catalog selector/catalog coherence; validate with tier-map parity, catalog, integrity, and Windows contracts.
- Model lifecycle or swap behavior: inspect model management workflow facts, model-state/switchboard contracts, bootstrap-upgrade behavior, and runtime adapter expectations; validate with focused model lifecycle and runtime tunable tests.
- Compose overlay for an inference backend: inspect overlay layering and llama.cpp/Lemonade command parity; validate overlay coherence and runtime tunable preservation.

## Source provenance

This runtime skill distills evidence from relative ODS source paths such as `ods/installers/lib/detection.sh`, `ods/installers/lib/tier-map.sh`, `ods/installers/macos/lib/tier-map.sh`, `ods/installers/windows/lib/tier-map.ps1`, `ods/config/backends/`, `ods/config/model-library.json`, `ods/config/hardware-classes.json`, `ods/config/gpu-database.json`, `ods/scripts/select-model.py`, `ods/scripts/detect-hardware.sh`, `ods/scripts/classify-hardware.sh`, `ods/scripts/load-backend-contract.sh`, `ods/bin/model_switchboard/`, compose overlays, and tier/model tests. Future usage should rely on this bundled guidance, the bundled read-only helper, and public ODS commands/tests rather than links to private inspection artifacts.
