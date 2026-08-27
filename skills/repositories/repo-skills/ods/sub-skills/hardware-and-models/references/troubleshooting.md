# Hardware and model troubleshooting

Use this guide to reason from symptoms to the right ODS files, safe checks, and ownership boundaries. It is self-contained guidance; run product installers, model downloads, Docker lifecycle, or live GPU tests only with explicit user intent.

## First triage

1. Identify whether the question is about **detection**, **tier/model recommendation**, **compose/runtime selection**, **model download**, **activation/swap**, or **consumer compatibility**.
2. Separate product support from current proof. A source path or catalog entry is not the same as live hardware validation.
3. Inspect persisted values first: `GPU_BACKEND`, `LLM_BACKEND`, `ODS_MODE`, `TIER`, `MODEL_PROFILE`, `LLM_MODEL`, `GGUF_FILE`, `MAX_CONTEXT`/`CTX_SIZE`, `MODEL_RECOMMENDATION_*`, and backend-specific env.
4. Use read-only summaries before mutating anything:

   ```bash
   python3 scripts/inspect_model_catalog.py --root <ODS_SOURCE_OR_PROJECT_ROOT>
   ```

5. Choose focused native tests from the backend/tier and model workflow references.

## Symptom: hardware detected but backend falls back to CPU

Likely causes:

- AMD GPU/APU is visible through sysfs, but runtime device nodes are unavailable (`/dev/kfd`, `/dev/dri`, `renderD*`). This is common inside LXD/LXC/other containers without GPU device passthrough.
- NVIDIA tools are installed but sysfs does not show NVIDIA hardware; ODS intentionally does not trust `nvidia-smi` alone.
- Low discrete VRAM falls into explicit CPU fallback classes.
- Capability profile generation failed and installer-local detection selected a safer fallback.

Inspect:

- `ods/installers/lib/detection.sh` for fallback and device guidance.
- `ods/scripts/detect-hardware.sh --json` output when the user is willing to run a read-only host command.
- `ods/scripts/classify-hardware.sh` arguments and class output.
- `ods/config/gpu-database.json` / `ods/config/hardware-classes.json` thresholds.

Safe checks:

```bash
cd ods
bash tests/bats-tests/detection.bats
bash tests/test-hardware-compatibility.sh
bash tests/contracts/test-overlay-map-coherence.sh
```

Do not claim GPU backend validation unless the matching runtime actually started and completed a model probe.

## Symptom: NVIDIA GPU path fails

Likely causes:

- Secure Boot blocks kernel modules.
- Blackwell-class GPU is using proprietary modules when open kernel modules are required.
- WSL2 host driver/Docker Desktop GPU passthrough is not set up.
- `nvidia-smi` exists from container tooling but no NVIDIA sysfs vendor device is present.
- Model chosen exceeds available VRAM or context/KV headroom.

Inspect:

- Detection logs/host read-only output for sysfs vendor and `nvidia-smi` consistency.
- `GPU_BACKEND`, `TIER`, selected model, and `MODEL_RECOMMENDATION_REASON`.
- `docker-compose.nvidia.yml` command/tunables when overlay behavior changed.

Safe checks:

```bash
cd ods
bash tests/test-tier-map.sh
python3 tests/contracts/test-llama-runtime-tunables.py
```

Live checks such as Docker CUDA samples, llama-server health, or completion probes are product validation and require a suitable NVIDIA host.

## Symptom: AMD/Strix Halo/Lemonade issues

Likely causes:

- Missing `/dev/kfd` or `/dev/dri` passthrough.
- Strix Halo unified-memory class selected a model/runtime that bypassed the A3B substitution policy.
- Lemonade state was changed manually outside the ODS transaction.
- `LEMONADE_LLAMACPP_ROCM_BIN` is set for the wrong AMD architecture; inspected schema documents this override as only appropriate for detected `gfx1151`.
- Windows Lemonade and Linux ROCm paths diverged; do not assume one validates the other.

Inspect:

- `TIER` should be `SH_LARGE` or `SH_COMPACT` for Strix Halo-style AMD unified memory.
- `MODEL_RECOMMENDATION_POLICY` should include the unified-memory A3B policy when qwen/coder-next would otherwise be selected on the problematic class.
- Backend contract `amd.json` for Lemonade route and health endpoint.
- `docker-compose.amd.yml` for Lemonade service, ROCm devices, and context env.

Safe checks:

```bash
cd ods
bash tests/test-tier-map.sh
bash tests/contracts/test-windows-strix-tier-map.sh
bash tests/contracts/test-overlay-map-coherence.sh
```

Live Lemonade validation requires the target AMD/Windows/Linux host and should prove runtime identity plus completion.

## Symptom: Intel Arc/SYCL path is selected but runtime fails

Likely causes:

- Host lacks Level Zero/OpenCL packages or user is not in `video`/`render` groups.
- `/dev/dri` is not passed into the container.
- First oneAPI SYCL build from source is long-running; a failure may be build/toolchain rather than model selection.
- `ARC`/`ARC_LITE` tier did not preserve `GPU_BACKEND=sycl` or `N_GPU_LAYERS=99`.

Inspect:

- `TIER`, `GPU_BACKEND`, and selected overlay (`docker-compose.arc.yml` or `docker-compose.intel.yml`).
- Whether compose command tunables are preserved in the Intel overlay.

Safe checks:

```bash
cd ods
bash tests/test-tier-map.sh
python3 tests/contracts/test-llama-runtime-tunables.py
```

## Symptom: macOS model works in docs but not in Docker

ODS macOS Metal acceleration runs llama-server natively on the host; Docker Desktop cannot pass Metal acceleration into a Linux container in the same way. The macOS overlay disables the containerized `llama-server` and adds a readiness sidecar that waits for the native host process.

Inspect:

- `installers/macos/lib/tier-map.sh` for Apple unified-memory thresholds.
- `installers/macos/docker-compose.macos.yml` for the disabled container and readiness sidecar.
- Port expectations: native llama-server normally uses port `8080` unless changed.

Safe checks include macOS tier-map parity and macOS launch/check tests when the host supports them.

## Symptom: selected model differs from tier-map expectation

This is often correct: tier map is fallback, while the catalog selector can refine the selection.

Inspect:

- `MODEL_PROFILE` and `MODEL_PROFILE_EFFECTIVE` semantics.
- `ODS_DISABLE_CATALOG_MODEL_SELECTOR`; if true, expect tier-map fallback behavior.
- `MODEL_RECOMMENDATION_SOURCE`, `MODEL_RECOMMENDATION_POLICY`, and `MODEL_RECOMMENDATION_REASON`.
- `config/model-library.json` fields: `install_recommendation`, `runtime_profiles`, `vram_required_gb`, `context_length`, app compatibility, and GGUF metadata.
- `scripts/select-model.py` policy and architecture/unified-memory overrides.

Safe checks:

```bash
cd ods
bash tests/test-tier-map.sh
python3 tests/test-model-library-coverage.py
python3 tests/test-model-library-verdicts.py
```

Do not report selector token/sec estimates as benchmarked speed.

## Symptom: context window mismatch or app rejects a model

Likely causes:

- `.env`, `models.ini`, Lemonade config, and app-specific model route were updated inconsistently.
- Catalog runtime profile reduced context for a constrained host.
- User requested a context above declared model/runtime capability.
- Hermes/ODS Talk or agent workflows require a 65,536-token floor or app compatibility verdict the model does not satisfy.
- Overlay command replaced `llama-server.command` without preserving `CTX_SIZE` or related tunables.

Inspect:

- `MAX_CONTEXT`, `CTX_SIZE`, `MODEL_RUNTIME_PROFILE`, `LLAMA_ARG_CACHE_TYPE_*`, `LLAMA_ARG_FLASH_ATTN`, and `LLAMA_PARALLEL`.
- Catalog `app_compatibility` and runtime profiles.
- Compose overlay command lists.

Safe checks:

```bash
cd ods
python3 tests/contracts/test-llama-runtime-tunables.py
python3 tests/test-model-library-coverage.py
python3 tests/test-gpu-layer-contract.py
```

## Symptom: model download appears complete but ODS cannot load it

Likely causes:

- GGUF SHA mismatch or corrupt/incomplete file.
- Multipart GGUF metadata is incomplete or only one part is present.
- Downloaded model is in a Hugging Face cache layout but the runtime expects a single configured GGUF.
- Offline validation correctly skips cloud/Lemonade host GGUF, so the failing path is an app/runtime route instead.
- Manual Lemonade app load changed Lemonade state but did not update ODS persisted model route.

Inspect:

- `GGUF_FILE`, file presence, non-zero size, and checksum when available.
- `config/model-library.json` artifact metadata.
- `data/model-imports.json` for imported Hugging Face GGUFs in an installed system.
- Bootstrap status if the system is still using fast-start.

Safe checks:

```bash
cd ods
bash tests/test-model-integrity.sh
python3 tests/test-offline-model-validation.py
```

## Symptom: bootstrap model never upgrades to full model

Likely causes:

- Full-model download failed or checksum failed.
- Another model lifecycle operation holds the lock.
- Full model failed readiness/identity/completion, so bootstrap was retained as recovery.
- Windows Lemonade metadata still points at bootstrap until refresh succeeds.
- Manual cleanup removed the recovery model or active config snapshot.

Inspect via public product diagnostics/commands and bootstrap status before deleting any model files. The correct product behavior is to leave bootstrap serving until full-model serving is verified.

Relevant files for code review: `installers/lib/bootstrap-model.sh`, `installers/lib/model-lifecycle-lock.sh`, `scripts/bootstrap-upgrade.sh`, phase 11 service startup, and model activation transaction code.

## Symptom: backend API/auth route confusion

Backend contracts use port `8080` for local backend health/API details, while many ODS apps normally talk through the stable LiteLLM or model-router route. For AMD Lemonade, the backend health path is `/api/v1/health`; for llama-server backends it is `/health`. Do not invent or expose credentials while debugging. Use public product diagnostics and sanitized configuration summaries.

Route dashboard/API authentication implementation questions to `dashboard-and-api`; route CLI invocation and host-agent command syntax to `ops-cli-and-host-tools`.

## Symptom: compose overlay mismatch

Likely causes:

- Hardware class recommended overlays disagree with classifier overlay map.
- `CAP_COMPOSE_OVERLAYS` points to a file that does not exist.
- A backend overlay replaced a command list and dropped a tunable.
- Apple macOS needs its special overlay path rather than generic `docker-compose.apple.yml`.
- Tier 0 overlay was not layered after backend overlay.

Safe checks:

```bash
cd ods
bash tests/contracts/test-overlay-map-coherence.sh
python3 tests/contracts/test-llama-runtime-tunables.py
bash tests/test-resolve-compose-resilient.sh
```

Use `testing-and-release` for final lane selection after identifying which overlay/contract files changed.
