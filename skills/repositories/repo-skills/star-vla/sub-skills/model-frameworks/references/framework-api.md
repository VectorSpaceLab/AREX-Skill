# Framework API, registry, and checkpoint compatibility

Evidence basis: `starVLA/model/framework/base_framework.py`, `starVLA/model/framework/share_tools.py`, `starVLA/model/tools.py`, framework decorators, and `tests/test_config_overrides.py`.

## Build path and registry auto-discovery

The public builder is `build_framework(cfg)`.

Required config shape:

```yaml
framework:
  name: QwenGR00T
```

Important behavior:

- `build_framework` requires `cfg.framework.name`; missing that field raises a clear `ValueError`.
- Before lookup it auto-imports public modules under the framework package, including VLM4A, VM4A, and WM4A subpackages. Underscore-prefixed modules such as VM4A vendored internals are skipped.
- If the key is absent from `FRAMEWORK_REGISTRY`, it raises `NotImplementedError` and includes the available registered keys.
- It emits a reproducibility warning: StarVLA is under active development, so released checkpoints may require the code/config revision from their release or training time for exact reproduction.

Use the bundled script to inspect an installed environment without constructing a model:

```bash
python scripts/inspect_framework_registry.py --config-yaml config.yaml
```

Run this from the `model-frameworks` sub-skill directory, or invoke the same script by its path inside the imported skill tree. The script does not depend on the original checkout.

## `baseframework` contract

All StarVLA framework classes are expected to subclass `baseframework` and implement the same high-level calls.

| API | Purpose | Expected contract |
| --- | --- | --- |
| `forward(examples, **kwargs)` | Training forward for VLA batches | Returns a dict containing `action_loss` as a scalar tensor. Examples usually contain `image`, `lang`, `action`, and optionally `state`. |
| `predict_action(examples, **kwargs)` | Inference action prediction | Returns a dict containing `normalized_actions` with shape `[B, T, action_dim]` or equivalent action-chunk shape. |
| `forward_vlm(batch)` | Optional VLM-only training path | Defaults to `self.qwen_vl_interface(**batch)` when that component exists, returning `vlm_loss`. Override for non-Qwen or custom VLM logic. |
| `supports_training_tag(tag)` | Trainer routing guard | Supports `vla` when `forward` is overridden and `vlm` when VLM support exists. |
| `compute_loss(tag, batch, loss_scale=None)` | Unified trainer entry point | Routes `vla` to `forward`, `vlm` to `forward_vlm`, scales tensor losses by tag, and returns `None` for unsupported tags. |
| `from_pretrained(pretrained_checkpoint, config_overrides=None, **kwargs)` | Restore a saved StarVLA model | Loads config/statistics, applies dotlist overrides, builds the framework, loads weights strictly, and attaches normalization stats. |

Typical raw example schema:

```text
image: list[PIL.Image] or compatible image arrays, often one entry per camera view
lang:  instruction string
action: np.ndarray shaped [T, action_dim] for training
state: optional np.ndarray shaped [1, state_dim] or [state_dim]
```

Frameworks intentionally own model-specific preprocessing. The dataloader supplies raw model-agnostic fields; the framework converts images, instructions, state, and actions into backbone/action-head tensors.

## Checkpoint loading semantics

`baseframework.from_pretrained(...)` expects a checkpoint file under a StarVLA run directory:

```text
<run_dir>/checkpoints/<checkpoint>.pt or <checkpoint>.safetensors
<run_dir>/config.yaml
<run_dir>/dataset_statistics.json
```

Behavior to preserve:

1. Load `config.yaml` and `dataset_statistics.json` from the run directory.
2. Apply config compatibility normalization (`apply_config_compat`) before building the model.
3. Apply `config_overrides` after the checkpoint config and before `build_framework`.
4. Set `trainer.pretrained_checkpoint = None` in the loaded config to avoid recursive reload.
5. Build the selected framework and attach `norm_stats` for later action unnormalization.
6. Load `.safetensors` or PyTorch state dict with `strict=True`; missing/unexpected keys are logged and then the runtime error is re-raised.

`read_model_config(...)` exists for older `config.json` layouts, but `from_pretrained` uses `read_mode_config(...)`, which reads `config.yaml`.

## Config overrides

`merge_config_overrides(model_config, config_overrides)` consumes OmegaConf dotlist items. Test-backed facts:

- `config_overrides` must be a sequence of strings such as `['framework.action_model.action_horizon=12']`.
- A bare string is rejected even if it looks like one override.
- Entries without `=` are rejected with a clear error.
- Repeated keys are accepted; the later value wins.
- Boolean strings such as `false` resolve to real booleans before `build_framework`.
- Unrelated OmegaConf interpolations are not resolved just because an override is applied.
- Applying overrides in `from_pretrained` does not modify the checkpoint's on-disk `config.yaml`.

Shell-safe examples:

```bash
--config_override framework.action_model.action_horizon=12
--config_override framework.action_model.diffusion_model_cfg.use_canonical_forward=false
```

## Config compatibility layer

`apply_config_compat(cfg)` normalizes older configs toward the current schema:

- `framework.action_model.action_horizon` is the canonical action chunk length.
- Legacy `future_action_window_size` is reconciled with `action_horizon` as `future_action_window_size = action_horizon - 1`.
- Missing `diffusion_model_cfg.output_dim`, `diffusion_model_cfg.cross_attention_dim`, `action_hidden_dim`, and `past_action_window_size` can be filled from framework/VLM defaults when enough information exists.
- The config is stamped with `version_id: "0.21"`.

For old checkpoints, use the checkpoint's own config first, then add only necessary overrides. Do not blindly rewrite `action_horizon`, `state_dim`, or `action_dim` without checking the dataset registry and saved statistics.

## `FrameworkTools` helpers

`starVLA.model.tools.FrameworkTools` contains model-agnostic helpers:

| Helper | Use |
| --- | --- |
| `check_unnorm_key(norm_stats, unnorm_key)` | Resolve/validate the statistics key used for action unnormalization. Raises when multiple datasets exist and no key is supplied, or when the key is absent. |
| `get_action_stats(norm_stats, unnorm_key=None)` | Return the action statistics block for a dataset key. |
| `unnormalize_actions(normalized_actions, action_norm_stats, gripper_channel_idx=6)` | Clamp normalized actions, threshold the gripper channel, and map masked dimensions from `[-1, 1]` back to dataset quantiles. |
| `get_trainable_module_keys(model, max_depth=1)` | Inspect trainable module names without hand-walking every parameter. |
| `has_flash_attn()` | Return whether `torch_npu` or `flash_attn` imports, allowing VLM modules to fall back to SDPA when no flash backend exists. |

Deployment-specific ownership of final action unnormalization belongs to the policy-deployment sub-skill, but model-level debugging often starts by checking that `norm_stats`, `action_dim`, and the requested `unnorm_key` are compatible.

## Adding a new framework safely

For a new StarVLA framework, keep this boundary:

1. Put the public framework module in the right family package (`VLM4A`, `VM4A`, or `WM4A`) rather than editing training code.
2. Register the class with `@FRAMEWORK_REGISTRY.register("ExactKey")`.
3. Subclass `baseframework` and implement `forward` and `predict_action` with the shared example schema.
4. Merge a dataclass default config with the incoming `cfg.framework`; let YAML values win.
5. Align hidden sizes before creating the action head. For example, GR00T-style heads need `diffusion_model_cfg.cross_attention_dim` to match the loaded backbone hidden size.
6. Keep all downloads, checkpoint paths, and accelerator requirements explicit in the config or user plan; do not hide them inside registry inspection.
