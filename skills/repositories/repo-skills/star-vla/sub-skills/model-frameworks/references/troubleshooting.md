# Model-framework troubleshooting

Evidence basis: `starVLA/model/tools.py`, VLM/world-model dispatch modules, `base_framework.py`, `share_tools.py`, selected framework files, `docs/faq.md`, `docs/VM4A.md`, `docs/WM4A.md`, and `tests/test_config_overrides.py`.

## Fast triage table

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `Framework <name> is not implemented` | `framework.name` is missing, stale, misspelled, or not imported into the registry | Run `scripts/inspect_framework_registry.py`; use exact case-sensitive keys such as `QwenFast`, `QwenOFT`, `QwenPI_v3`, `QwenGR00T`, `ACT`, `DiffusionPolicy`, `CosmoPredict2OFT`, or `WanPI`. Replace stale `framework.framework_py` usage with `framework.name`. |
| `VLM model ... not implemented` | `framework.qwenvl.base_vlm` does not match a supported dispatch substring | Use a supported base signal (`Qwen2.5-VL`, `Qwen3-VL`, `Qwen3.5`, `gemma-4`, `minicpm-v`, `florence`, `molmo2`, `cosmos-reason2`, `egovla`/`vila`) or add a new VLM wrapper. |
| `World model ... not implemented` | `framework.world_model.base_wm` or fallback `base_vlm` does not match WM dispatch | Use a supported signal such as `cosmos-predict2`, `wan2`, `ti2v`, or `cosmos-reason2`, or add a world-model wrapper. |
| Missing `flash_attn` or `torch_npu` | Requested `flash_attention_2` but no compatible flash backend is installed | Qwen2.5/MiniCPM/Molmo wrappers can fall back to SDPA; Qwen3 currently forces SDPA. For smoke/debug, set `framework.qwenvl.attn_implementation=sdpa` or `eager`. Install flash/NPU packages only for a backend run that needs them. |
| Checkpoint loads wrong behavior or reproduces poorly | Released checkpoint may correspond to older code/config/preprocessing/eval semantics | Prefer the checkpoint-time code/config. If using current code, keep the checkpoint config and apply only explicit compatibility overrides. For historical QwenPI_v3/DiT forward semantics, use the checkpoint's `interleave_self_attention`/`use_canonical_forward` setting; launcher environments may expose `USE_CANONICAL_FORWARD=false` to pass `framework.action_model.diffusion_model_cfg.use_canonical_forward=false`. |
| `config_overrides` type error | A bare string was passed instead of a sequence | Pass repeated CLI `--config_override KEY=VALUE` flags or a Python list/tuple of strings. Empty lists/tuples are valid no-ops; empty strings are rejected. |
| `Invalid config_overrides entries` | Dotlist entry lacks `=` | Use exact `KEY=VALUE`, for example `framework.action_model.action_horizon=12`. Quote shell values that contain spaces or brackets. |
| Missing `config.yaml` or `dataset_statistics.json` near checkpoint | `from_pretrained` expects a StarVLA run layout | Put checkpoint under `<run_dir>/checkpoints/` with sibling run-level `config.yaml` and `dataset_statistics.json`, or load with a path matching that layout. |
| Missing pretrained VLM/world-model weights | `base_vlm`/`base_wm` points to a local path or model id that is not available | Confirm local paths/caches and download policy before instantiation. WM4A backbones are large; do not use registry inspection as proof that weights exist. |
| Strict state-dict key mismatch | Wrong framework key, stale checkpoint architecture, wrong DiT forward mode, or incompatible action head/backbone dims | Compare checkpoint config to current YAML. Check `framework.name`, hidden sizes, DiT shape fields, action head type, and `use_canonical_forward`/`interleave_self_attention`. Strict load intentionally re-raises mismatches. |
| Action loss shape error or action prediction shape mismatch | `action_dim`, `state_dim`, `action_horizon`, camera order, or data registry action window disagrees with config | Align dataset registry, `modality.json`, YAML action/state dims, image keys, and action horizon. Route dataset-layout fixes to data-integration. |
| `ACT` import succeeds but instantiation fails with missing `lerobot` | ACT guards optional LeRobot imports for registry discovery | Install the optional LeRobot dependency only if the task requires ACT instantiation, or choose a VLM4A/WM4A framework. |
| VM4A starts downloading ImageNet weights | ACT/DP defaults use ImageNet-pretrained ResNet-18 | Set ACT `pretrained_backbone_weights: null` or DiffusionPolicy `pretrained_backbone: false` for no-download from-scratch smoke. |
| Multiple dataset statistics but no `unnorm_key` | `FrameworkTools.check_unnorm_key` cannot infer which dataset stats to use | Pick one of the saved statistics keys. Policy-server/client handling belongs to policy-deployment; model-level check is only to ensure `norm_stats` contains the intended key. |

## Framework-name checklist

1. Inspect the config's `framework.name`.
2. Run the registry script and compare against `registered_framework_keys`.
3. Watch casing and historical aliases:
   - FAST is often written as QwenFAST in prose; registry key is `QwenFast`.
   - PI may appear as `QwenPI` or `QwenFM`; both are registered for the same class.
   - `PI0`/`Pi0` and `PI05`/`Pi05` are both registered spellings.
   - Current builder requires `framework.name`; older snippets that use `framework.framework_py` are stale for `build_framework`.
4. If the key exists in source but not the runtime registry, the installed package may be stale or missing optional import dependencies.

## Checkpoint/config compatibility checklist

Use this sequence before blaming model quality:

1. Confirm checkpoint layout and sibling `config.yaml`/`dataset_statistics.json`.
2. Confirm `framework.name` matches the checkpoint's original framework family.
3. Keep the checkpoint's saved `action_horizon`, `action_dim`, `state_dim`, `base_vlm`/`base_wm`, and DiT shape fields unless you know exactly why an override is needed.
4. For QwenPI_v3/layer-wise DiT checkpoints, check whether the checkpoint was trained with legacy all-cross attention or canonical interleaved self/cross attention. The compatibility alias is `framework.action_model.diffusion_model_cfg.use_canonical_forward`; the current canonical field is `interleave_self_attention`.
5. Use repeated `--config_override` flags rather than editing the checkpoint config on disk.
6. If strict state-dict loading fails, compare missing/unexpected keys against the selected framework/action head before trying a non-strict load.

## Dimension mismatch checklist

- Training `action` arrays must have shape `[T, action_dim]`; frameworks commonly slice the last `action_horizon` steps as the target chunk.
- Inference returns normalized action chunks shaped around `[B, action_horizon, action_dim]`.
- `state_dim` must match the proprioceptive vector if the framework uses state; some frameworks encode state into the instruction string, while VM4A consumes it directly.
- VM4A `image_keys` order must match the order of images in each example.
- GR00T-style heads need VLM hidden size alignment for `cross_attention_dim`; PI-style heads need layer count and hidden size alignment for every layer fed to the action DiT.

## When to route away

- If the fix requires changing dataset registries, action windows, `modality.json`, or statistics files, route to data-integration.
- If the fix concerns training command syntax, freezing, LR groups, W&B, Accelerate, or DeepSpeed, route to training-config.
- If the fix concerns served `actions`, `normalized_actions`, request schemas, ports, or `unnorm_key` in a running server, route to policy-deployment.
- If the fix requires simulator/benchmark installation, display/rendering libraries, or two-environment evaluation, route to benchmark-evaluation.
