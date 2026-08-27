# Model management workflows

This reference distills ODS model catalog selection, download, activation, bootstrap upgrade, context policy, and model-state behavior. Dashboard page implementation details belong to `dashboard-and-api`; command syntax and host-agent command dispatch belong to `ops-cli-and-host-tools`.

## Model identity and storage

ODS local language models are GGUF files under `data/models/` in an installed ODS tree. The active local model is represented by persisted runtime configuration such as:

- `LLM_MODEL`: logical model name consumed by ODS services.
- `GGUF_FILE`: concrete GGUF filename in `data/models/`.
- `MAX_CONTEXT` / `CTX_SIZE`: context window committed to installer/runtime config.
- `GGUF_URL` and `GGUF_SHA256`: acquisition and integrity metadata where available.
- `MODEL_PROFILE`, `MODEL_RECOMMENDATION_SOURCE`, `MODEL_RECOMMENDATION_POLICY`, and `MODEL_RECOMMENDATION_REASON`: selection provenance.
- `LLAMA_SERVER_IMAGE` / runtime-profile env values when a model family or profile needs a specific runtime.

The active route may also be propagated into `config/llama-server/models.ini`, LiteLLM/Lemonade/Hermes/app config, and model-state data. Direct manual edits to these files bypass the product transaction and should be treated as recovery-only unless the user explicitly asks for manual repair.

## Tier-map fallback then catalog selector

ODS uses a two-step model recommendation path during install:

1. **Tier-map fallback** resolves `TIER` + `MODEL_PROFILE` to a model, GGUF file, URL, checksum, context, and optional runtime image. This path is shell/PowerShell and remains the no-Python fallback.
2. **Catalog selector** reads `config/model-library.json` and refines the pre-download choice when Python is available and `ODS_DISABLE_CATALOG_MODEL_SELECTOR` is not true.

The selector is deterministic and offline. It does not download metadata and does not treat throughput estimates as measured performance.

### Catalog selector policy facts

The inspected selector policy is `context-aware-largest-capable-general-v1`, with architecture/memory overrides for Spark-class arm64 `NV_ULTRA` and unified-memory coder-next exclusion.

Selection pipeline:

1. Load curated catalog entries from `model-library.json` that have usable GGUF metadata.
2. Normalize the requested profile to `qwen`, `gemma4`, or `auto`; then compute the effective profile.
3. Estimate usable memory:
   - unified-memory or Apple backend: about 55% of system RAM;
   - CPU/no GPU: bounded share of system RAM, clipped to small-model territory;
   - discrete GPU: reported GPU VRAM.
4. Filter by installability when `--installable-only` is used: a model needs a download URL and must not set `install_recommendation=false`.
5. Apply runtime profiles for special cases such as NVIDIA 8GB hosts using 64K context with Q4 KV cache and specific llama.cpp env values.
6. Estimate required memory from declared VRAM, file size, and a context/KV estimate; accept fits with a small tolerance.
7. Rank by specialty, family preference, context, capability/size, and headroom.
8. Apply architecture or unified-memory override if the selected qwen model would be `qwen3-coder-next` on a known problematic unified-memory class.
9. Emit JSON or shell assignments such as `LLM_MODEL`, `GGUF_FILE`, `MAX_CONTEXT`, `MODEL_RECOMMENDATION_*`, and runtime-profile env.

When debugging a mismatch, compare tier-map fallback output, catalog selector output, and the final persisted `.env` values. The bundled helper can summarize catalog and backend inventory but intentionally does not mutate model state.

## Model catalog data contract

Important catalog fields:

| Field | Meaning |
| --- | --- |
| `id` | Stable catalog identifier used by selection and lifecycle decisions. |
| `llm_model_name` | Runtime/logical model name written into active config. |
| `gguf_file`, `gguf_url`, `gguf_sha256`, `gguf_parts` | Download artifact identity and integrity. Multipart models must have complete part metadata. |
| `size_mb`, `size_bytes`, `vram_required_gb` | Fit metadata used by selector and dashboard. |
| `context_length`, `max_context_length` | Declared usable context. App floors, especially agent/Hermes use cases, depend on this. |
| `family`, `specialty`, `quantization` | Profile/ranking and operator display metadata. |
| `llama_server_image` | Optional runtime image override, especially for models requiring newer llama.cpp. |
| `runtime_profiles` | Host/backend-specific overrides for context/memory/tunable env. |
| `install_recommendation` | If false, the selector must not recommend the model for installation. |
| `app_compatibility` | Product viability/verdict metadata for consumers such as OpenAI chat, Hermes/ODS Talk, Perplexica, OpenCode, and agent viability. |

Catalog app compatibility is product data. Do not “fix” selection by hiding model names in harness logic; update the product catalog/verdict metadata and tests.

## Download and integrity workflow

Safe operating sequence for model acquisition changes:

1. Confirm the model is cataloged or tier-mapped with GGUF filename, URL, size, and checksum where available.
2. If changing the installer path, ensure phase 11 download verifies `GGUF_SHA256` when non-empty and removes corrupt files on mismatch.
3. For offline mode, remember local GGUF validation is skipped for cloud/Lemonade modes and disabled services, but required configured local GGUFs must exist and be non-empty.
4. For Hugging Face imports, preserve the rule that import metadata is separate from `config/model-library.json` and installer reruns do not rewrite the curated catalog.
5. Run model integrity/offline validation tests when touching this flow.

## Bootstrap-to-full model lifecycle

ODS fast-start installs can run a small bootstrap model while the full tier model downloads in the background.

Bootstrap constants from the inspected source:

- Bootstrap GGUF: `Qwen3.5-2B-Q4_K_M.gguf`.
- Bootstrap logical model: `qwen3.5-2b`.
- Bootstrap context floor: `65536` tokens, kept high enough for Hermes/agent consumers during fast-start.
- Bootstrap size metadata: about 1.22 GiB.

`bootstrap_needed()` returns true only when the full model is larger than Tier 0, the full GGUF is absent, bootstrap is not disabled, offline mode is false, cloud mode is false, and external Lemonade mode is not selected.

`bootstrap-upgrade.sh` is the background full-model path. Its key operating contract:

1. Acquire the model lifecycle lock so foreground installer and background model activation do not race.
2. Download the full GGUF and verify SHA when provided.
3. Snapshot active config before promotion.
4. Patch `.env` and runtime/app configs to the full model and context.
5. Restart/stage the backend as needed and verify identity plus a real completion where the path supports it.
6. Keep the bootstrap model until full-model serving is verified; rollback should restore the previous active route and keep bootstrap available.
7. Clean up bootstrap only after verified full-model serving, with Lemonade refresh where needed so stale metadata is dropped.

If a user is stuck on bootstrap, inspect status and logs via public ODS diagnostics/commands rather than deleting files first. A failed or partial full-model upgrade should be retried through the product path because manual deletion can remove the recovery model.

## Activation and swap transaction

Dashboard activation and supported `ods model`/Windows model swap operations are intended to use the same model activation transaction. The command surface belongs to `ops-cli-and-host-tools`; the hardware/model contract is:

1. Resolve selected catalog/tier model and context.
2. Validate enabled consumers and backend capability floors.
3. Persist `.env`, `models.ini`, and app-owned model routes consistently.
4. Stage or restart the selected backend.
5. Prove runtime identity and completion, not merely configuration echoes.
6. Update multi-GPU assignment when the model requires a larger GPU subset and rollback both model and assignment on failure.
7. Restore the previous proven route if activation fails.

For Linux NVIDIA and managed Linux AMD/ROCm multi-GPU installs, the transaction may update assignment variables such as `GPU_ASSIGNMENT_JSON_B64`, `LLAMA_SERVER_GPU_UUIDS`, `LLAMA_SERVER_GPU_INDICES`, `LLAMA_ARG_SPLIT_MODE`, and `LLAMA_ARG_TENSOR_SPLIT`. Apple, Windows-native AMD/Lemonade, externally managed inference, and unpersisted all-GPU fallback paths are separate behavior classes.

## Model switchboard and state contract

The model switchboard modules define the emerging stable-route contract:

- Public local model alias: `ods/current`.
- State path in an installed tree: `data/model-state.json`.
- Schema version: `ods.model-state.v1`.
- Host agent is the only writer.
- Writes are atomic; readers must not observe partial JSON.
- `seq` increments on every mutation; `routeSeq` increments only when active route changes.
- `active` remains the last proven route. Reconstruction from legacy config is marked unproven and must not masquerade as verified proof.
- Runtime adapters must return typed result dictionaries. Expected runtime failures are result values; success must carry concrete identity/completion evidence.

This contract is useful when reviewing lifecycle changes even if a particular branch still writes legacy config for compatibility.

## Context policy and app viability

Context selection is a compatibility decision, not a raw “largest number wins” rule.

- `MAX_CONTEXT` and `CTX_SIZE` must stay consistent across `.env`, llama-server/Lemonade runtime config, model state, and dependent app routes.
- A catalog model may have a declared context and a smaller runtime-profile context for constrained hosts.
- Requests above the model declaration can be warning-gated but do not imply the backend can serve them.
- Hermes/ODS Talk and agent workflows may require at least 65,536 tokens plus instruction-following viability. Catalog app compatibility determines whether a model is agent viable.
- If a backend cannot establish requested context, activation should fail and restore the previous model configuration.

## Safe validation checklist

When editing hardware/model behavior, pick focused checks before broad gates:

```bash
cd ods
bash tests/test-tier-map.sh
bash tests/test-tier-map-parity.sh
python3 tests/test-model-library-coverage.py
python3 tests/test-model-library-verdicts.py
bash tests/test-model-integrity.sh
python3 tests/test-offline-model-validation.py
python3 tests/contracts/test-llama-runtime-tunables.py
bash tests/contracts/test-overlay-map-coherence.sh
```

Add host-specific checks only when the touched path demands them and the host is suitable: Windows model activation/Strix contracts, macOS native llama-server launch checks, Linux NVIDIA/AMD smoke tests, Intel Arc SYCL overlay checks, or Docker compose validation.
