# Backend and tier reference

This reference is the self-contained operating map for ODS hardware detection, backend contracts, tier maps, model profiles, and inference compose overlays.

## Verification boundary

ODS product behavior includes multiple GPU/runtime backends. This repo-skill can guide work on those backends from source evidence, but safe repo-skill verification does not prove that any live GPU runtime worked. Use precise wording:

- **Source-supported product backend**: the repository contains detection, config, compose, and tests for the backend.
- **Static/native check passed**: a safe shell/Python contract test passed on the current host.
- **Live backend validated**: a matching machine actually ran the runtime, health probe, and model completion path.

Do not collapse these levels. CPU/static checks can verify this operating skill; live CUDA/ROCm/Metal/SYCL/Lemonade claims require matching hardware and explicit authorization.

## Core source surfaces

| Surface | Relative files | Operating meaning |
| --- | --- | --- |
| Installer-local detection | `ods/installers/lib/detection.sh`, platform detection libraries | Detects GPU vendor, memory, runtime devices, CPU/RAM, backend, tier fallback, and backend contract variables. |
| Standalone hardware detection | `ods/scripts/detect-hardware.sh` | Read-only hardware summary command with JSON/text output; useful for support and diagnostics. |
| Hardware classifier | `ods/scripts/classify-hardware.sh`, `ods/config/gpu-database.json`, `ods/config/hardware-classes.json` | Maps detected hardware to `HW_CLASS_*`, recommended backend, tier, overlays, memory source, and bandwidth. |
| Tier maps | `ods/installers/lib/tier-map.sh`, `ods/installers/macos/lib/tier-map.sh`, `ods/installers/windows/lib/tier-map.ps1` | Fallback/default tier-to-model, GGUF, checksum, context, model profile, and runtime-image choices. |
| Catalog selector | `ods/scripts/select-model.py`, `ods/config/model-library.json` | Refines the tier-map model using a versioned model catalog and bounded memory-fit policy before download. |
| Backend contracts | `ods/config/backends/*.json`, `ods/scripts/load-backend-contract.sh` | Defines runtime identity, public health/API endpoint, provider route, and Lemonade details for backend-specific installer variables. |
| Compose overlays | `ods/docker-compose.base.yml`, backend overlays, multi-GPU overlays, macOS overlay, `ods/installers/lib/compose-select.sh`, `ods/scripts/resolve-compose-stack.sh` | Selects and merges inference runtime services and backend-specific devices/env/commands. |
| Model lifecycle | `ods/installers/lib/bootstrap-model.sh`, `ods/installers/lib/model-lifecycle-lock.sh`, `ods/scripts/bootstrap-upgrade.sh`, `ods/bin/model_switchboard/` | Fast-start model, serialized model changes, background full-model upgrade, state/adapter contracts. |

## Detection and classification pipeline

Typical Linux installer flow:

1. Capability profile loading attempts to run the builder and import `CAP_*` values. If that fails, installer-local detection continues.
2. `detect_gpu()` starts from CPU fallback and tries specialized hardware paths. It checks Jetson/Tegra only when the experimental Jetson flag is set, validates NVIDIA through sysfs before trusting `nvidia-smi`, detects Intel Arc from PCI/sysfs, and detects AMD from sysfs memory/runtime clues.
3. AMD runtime device checks distinguish product detection from usable acceleration. Missing `/dev/kfd` or `/dev/dri/renderD*` can force CPU fallback even when AMD hardware is visible, especially inside containers without GPU device passthrough.
4. Classifier output (`HW_CLASS_ID`, `HW_REC_BACKEND`, `HW_REC_TIER`, `HW_REC_COMPOSE_OVERLAYS`, bandwidth, memory source) comes from two passes: known GPU/device-name matching in `gpu-database.json`, then heuristic classes by vendor, memory type, VRAM/RAM thresholds.
5. Backend contracts load backend-specific runtime variables from `config/backends/<backend>.json`.
6. Tier maps set fallback model/GGUF/context variables. The catalog selector may then replace the fallback with a catalog-fit recommendation.
7. Compose selection starts with profile overlays when present, then falls back to backend/tier mappings and finally lets the compose resolver add extension/multi-GPU overlays.

## Backend contract summary

| Backend id | Runtime engine | Public port/health | Provider route | Important notes |
| --- | --- | --- | --- | --- |
| `nvidia` | `llama-server` | `8080`, `/health` | `http://llama-server:8080/v1` | Uses CUDA llama.cpp overlay by default. NVIDIA hardware validation must not rely on `nvidia-smi` alone when sysfs says no NVIDIA GPU. Blackwell-class hosts may require open kernel modules. |
| `cpu` | `llama-server` | `8080`, `/health` | `http://llama-server:8080/v1` | CPU fallback overlay has no GPU reservation and lower context defaults. This is the required repo-skill verification substitute. |
| `apple` | `llama-server` | `8080`, `/health` | `http://llama-server:8080/v1` | macOS Metal acceleration is native on the host. The macOS compose overlay disables the containerized `llama-server` and uses a readiness sidecar for the host process. |
| `amd` | `lemonade` | `8080`, `/api/v1/health` | `http://llama-server:8080/api/v1` | Linux container path uses Lemonade with ROCm; Windows runtime metadata points to Lemonade MSI/executable and Vulkan. Service name remains `llama-server` for compose dependency compatibility. |

Intel Arc/SYCL is tiered through `ARC` and `ARC_LITE` plus `GPU_BACKEND=sycl` in tier/compose logic. Compose selection prefers `docker-compose.arc.yml` (local oneAPI SYCL build) and can fall back to `docker-compose.intel.yml` if present. Treat Intel as a source-supported product path only after checking current overlay files and host prerequisites.

## Tier identifiers and profiles

ODS uses both normalized numeric tiers and `T*` class labels. Common mappings:

| Class label | Tier-map value | Meaning |
| --- | --- | --- |
| `T0` | `0` | Lightweight / CPU or very low VRAM fallback. |
| `T1` | `1` | Entry level / compact local model. |
| `T2` | `2` | Prosumer / mid-size local model. |
| `T3` | `3` | Pro / larger local model. |
| `T4` | `4` | Enterprise / long-context larger local model. |
| `NV_ULTRA` | `NV_ULTRA` | NVIDIA 90GB+ discrete or unified class. |
| `SH_LARGE` | `SH_LARGE` | Strix Halo / AMD unified memory 90GB+ class. |
| `SH_COMPACT` | `SH_COMPACT` | Strix Halo compact unified memory class. |
| `ARC` | `ARC` | Intel Arc 12GB+ / A770-class SYCL path. |
| `ARC_LITE` | `ARC_LITE` | Intel Arc 6-8GB SYCL path. |
| `CLOUD` | `CLOUD` | API/cloud mode; no local GGUF download. |

Model profiles are `qwen`, `gemma4`, and `auto`. The tier map normalizes aliases such as `gemma` and `gemma-4`. `auto` keeps `qwen` for cloud/Tier 0 and prefers `gemma4` elsewhere in the tier-map fallback. The catalog selector receives the effective profile during Linux install and may apply additional policy only inside that family selection.

### Notable tier-map rules

- Linux `qwen` profile maps high NVIDIA `NV_ULTRA` to `qwen3-coder-next`, except arm64 `NV_ULTRA` substitutes `qwen3.6-35b-a3b` because coder-next is documented as producing all-`?` tokens on Spark/Grace Blackwell aarch64 in the inspected source.
- Linux `qwen` profile maps `SH_LARGE` to `qwen3.6-35b-a3b` for the same unified-memory correctness/throughput reason, and `SH_COMPACT` to `qwen3-30b-a3b`.
- `ARC` and `ARC_LITE` set `GPU_BACKEND=sycl` and `N_GPU_LAYERS=99` in tier maps.
- `gemma4` tiers require a newer llama.cpp runtime image/tag (`server-cuda-b9014` / `b9014`) where the platform uses containerized llama.cpp. Preserve this runtime alignment when changing Gemma defaults.
- macOS tier maps keep Apple Silicon unified memory thresholds conservative because system memory is shared by macOS, Docker services, and the LLM.
- Windows tier maps duplicate Linux tier values in PowerShell and include unified-memory A3B substitution policy for Strix Halo/Lemonade.

## Compose overlay map

| Situation | Expected overlay pattern | Notes |
| --- | --- | --- |
| NVIDIA local | `docker-compose.base.yml` + `docker-compose.nvidia.yml` | CUDA llama.cpp image, NVIDIA device reservations. |
| AMD local / Strix Halo | `docker-compose.base.yml` + `docker-compose.amd.yml` | Lemonade service under the `llama-server` service name; ROCm/Vulkan details depend on platform. |
| CPU fallback | `docker-compose.base.yml` + `docker-compose.cpu.yml` | CPU llama.cpp image and lower context defaults. |
| Apple macOS | `docker-compose.base.yml` + `installers/macos/docker-compose.macos.yml` | Native host llama-server; compose has readiness sidecar. |
| Intel Arc | `docker-compose.base.yml` + `docker-compose.arc.yml` or `docker-compose.intel.yml` | SYCL/oneAPI path, `/dev/dri`, `video`/`render` groups, dashboard backend forced to `sycl`. |
| Tier 0 low memory | add `docker-compose.tier0.yml` | Layered on top of the chosen base/backend overlay when tier is `0`. |
| Multi-GPU NVIDIA/AMD | add multi-GPU overlay through resolver | Assignment env such as `GPU_ASSIGNMENT_JSON_B64`, `LLAMA_SERVER_GPU_UUIDS`, and tensor split values may be updated by model lifecycle flows. |

Compose command lists do not merge. Any overlay that replaces `llama-server.command` must repeat all documented llama.cpp tunables it intends to preserve (`CTX_SIZE`, `N_GPU_LAYERS`, batch/threads/parallel, metrics, KV cache/flash attention when applicable). AMD Lemonade overlays are different because their command starts Lemonade rather than raw llama.cpp.

## Exact file/test map for changes

Use this map before editing and when explaining validation.

### Add or change a hardware class / GPU tier

Likely files:

- `ods/config/gpu-database.json` and optionally `ods/config/gpu-database.schema.json` for known GPUs, heuristics, bandwidth, or new fields.
- `ods/config/hardware-classes.json` for class-to-backend/tier/overlay coherence.
- `ods/scripts/classify-hardware.sh` for classifier output or overlay-map logic.
- `ods/installers/lib/detection.sh` plus platform detection libraries when raw detection changes.
- `ods/installers/lib/tier-map.sh`, `ods/installers/macos/lib/tier-map.sh`, and `ods/installers/windows/lib/tier-map.ps1` if the tier is new or model defaults change.
- `ods/installers/lib/compose-select.sh`, backend compose overlays, and `ods/scripts/resolve-compose-stack.sh` if overlays change.

Focused tests:

```bash
cd ods
bash tests/test-tier-map.sh
bash tests/test-tier-map-parity.sh
bash tests/contracts/test-overlay-map-coherence.sh
bash tests/bats-tests/detection.bats        # if BATS is available and detection changed
bash tests/test-hardware-compatibility.sh   # if classifier/hardware compatibility changed
```

Add platform-specific tests when touched: Jetson detection, Windows Strix tier-map contract, macOS installer contracts, or WSL2 GPU support checks.

### Change tier-to-model, model profile, context, SHA, or GGUF URL

Likely files:

- `ods/installers/lib/tier-map.sh` and matching macOS/Windows tier maps.
- `ods/config/model-library.json` for catalog metadata, `gguf_*`, `vram_required_gb`, context, runtime profiles, install recommendation, and app compatibility metadata.
- `ods/scripts/select-model.py` if selection policy, fit estimate, runtime profile matching, or architecture override changes.
- `ods/.env.schema.json` if new runtime env variables are introduced.
- `ods/config/llama-server/models.ini`, renderer/bootstrap scripts, or Lemonade config only when the persisted runtime config contract changes.

Focused tests:

```bash
cd ods
bash tests/test-tier-map.sh
bash tests/test-tier-map-parity.sh
python3 tests/test-model-library-coverage.py
python3 tests/test-model-library-verdicts.py
bash tests/test-model-integrity.sh
python3 tests/test-offline-model-validation.py
bash tests/contracts/test-windows-strix-tier-map.sh
```

### Change backend contract or inference overlay behavior

Likely files:

- `ods/config/backends/<backend>.json` and `ods/scripts/load-backend-contract.sh`.
- `ods/docker-compose.base.yml`, backend overlays, multi-GPU overlays, macOS overlay, Intel Arc/Intel fallback overlays.
- `ods/installers/lib/compose-select.sh`, `ods/scripts/resolve-compose-stack.sh`, and generated config renderers if compose flags or runtime URLs change.
- `ods/.env.schema.json` for tunables and backend env defaults.

Focused tests:

```bash
cd ods
bash tests/contracts/test-overlay-map-coherence.sh
python3 tests/contracts/test-llama-runtime-tunables.py
bash scripts/validate-compose-stack.sh      # requires Docker/compose suitability
bash tests/test-resolve-compose-resilient.sh # if resolver behavior changed
python3 tests/test-gpu-layer-contract.py     # if N_GPU_LAYERS or platform generators changed
```

### Change model activation or lifecycle behavior

Likely files:

- `ods/installers/lib/bootstrap-model.sh`, `ods/installers/lib/model-lifecycle-lock.sh`, `ods/scripts/bootstrap-upgrade.sh`.
- Host-agent/model activation code, model switchboard modules, and model state schema when present in the change.
- Runtime config renderers for `.env`, `models.ini`, LiteLLM, Hermes, Perplexica, OpenCode, or OpenWebUI when model routes are propagated.

Focused tests depend on the touched owner. Start with safe model lifecycle tests:

```bash
cd ods
bash tests/test-linux-installer-model-lifecycle-lock.sh
python3 tests/contracts/test-llama-runtime-tunables.py
bash tests/contracts/test-ods-cli-model-activation.sh
bash tests/test-windows-model-activation.ps1   # Windows host only
```

Route broad command/test lane choice to `testing-and-release` after identifying these owner files.
