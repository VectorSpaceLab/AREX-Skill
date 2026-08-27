# Export artifact contract

## Source artifacts versus bundled helper

| Item | Owner and purpose | Input | Output |
| --- | --- | --- | --- |
| `export_policy_dh.py` | Repository checkpoint → JIT exporter | `model_<iteration>.pt` mapping with `model_state_dict` | scripted `policy_dh.jit` |
| `export_onnx_dh.py` | Repository JIT → ONNX converter | previously exported `policy_dh.jit` | fixed-shape `x1_policy.onnx` |
| [`scripts/preflight_export.py`](../scripts/preflight_export.py) | Safe advisory helper | paths plus an optional trusted checkpoint or serialized artifact | diagnostics only; never exports or trains |

The bundled helper intentionally does not import the project package,
`humanoid.envs`, or Isaac Gym. It may use already-installed PyTorch, ONNX, or
ONNX Runtime to inspect trusted local artifacts. Never run `torch.load` on an
untrusted checkpoint: checkpoint deserialization can execute pickle payloads.
The helper deserializes a checkpoint only when `--inspect-checkpoint` is set.

## Exact command arguments

The shared source parser exposes these relevant arguments:

| Flag | Checkpoint → JIT | JIT → ONNX | Contract |
| --- | --- | --- | --- |
| `--task` | required in practice | required in practice | Registry key; use `x1_dh_stand`. The parser's default is not a registered X1 task. |
| `--load_run` | run under `exported_data` | timestamp/run under `exported_policies` | Omit for source latest behavior or pass an exact name. Literal CLI `-1` is a string and may be treated as a directory name. |
| `--checkpoint` | checkpoint integer | ignored by local ONNX loader | `-1` chooses latest model filename for JIT; explicit `N` maps to `model_N.pt`. |
| `--experiment_name` | parsed, but exporter obtains experiment from registered config | same | It does not override `task_registry.get_cfgs`; source uses `train_cfg.runner.experiment_name`. |
| `--resume`, `--run_name`, `--num_envs`, `--seed`, `--max_iterations` | unused | unused | Training/runtime flags; omit them from export commands. |

Neither source exporter accepts an output path or filename. Both create a
second-resolution timestamp directory. Avoid concurrent same-task exports in
the same second because they can target the same directory (`exist_ok=True`)
and filename.

## X1 DH dimension and architecture facts

The registered `x1_dh_stand` contract is:

| Quantity | Value | Derivation |
| --- | ---: | --- |
| history frames (`frame_stack`, policy `in_channels`) | 66 | X1 environment/policy config |
| scalar observations per frame | 47 | `num_single_obs` |
| flattened policy input | 3102 | `66 × 47` |
| short-history frames | 5 | `short_frame_stack` |
| short-history width | 235 | `5 × 47` |
| estimator output | 3 | fixed state-estimator output |
| compressed long history | 64 | `lh_output_dim` |
| actor input | 302 | `235 + 3 + 64` |
| actions | 12 | `num_actions` |

The policy wrapper expects a floating tensor whose final width is 3102. It takes
the last 235 values as short history, reshapes the complete flattened history
to `(-1, 66, 47)`, estimates three velocity values, compresses long history to
64 values, concatenates width 302, and returns the deterministic actor mean. It
does not sample action noise and does not include observation normalization or
clipping. The caller must preserve training-time frame order, feature order,
scales, dtype, and preprocessing.

The X1 actor is `302 → 512 → 256 → 128 → 12` with ELU between hidden layers.
The state estimator is `235 → 256 → 128 → 64 → 3`, also with ELU hidden
activations. The long-history encoder is:

```text
Conv1d(66→32, kernel=6, stride=3) → ReLU
Conv1d(32→16, kernel=4, stride=2) → ReLU
Flatten(16×6=96) → Linear(96→128) → ELU → Linear(128→64)
```

A checkpoint from a different observation history, action count, network width,
or policy class is not compatible merely because it is a PyTorch state mapping.
Require strict successful loading and artifact shape checks.

## JIT artifact

- Path convention:
  `logs/x1_dh_stand/exported_policies/<timestamp>/policy_dh.jit`.
- Serialization: `torch.jit.script` of the CPU `ExportedDH` wrapper.
- Input contract: floating tensor with shape `(batch, 3102)`; the helper checks
  batch 1 with a zero input.
- Output contract: deterministic action mean with shape `(batch, 12)`.
- Contents: actor, state estimator, and long-history encoder. Critic,
  action-noise state, and optimizer are absent.
- Acceptance: nonempty file, `torch.jit.load(..., map_location='cpu')` succeeds,
  a `(1, 3102)` float input returns a tensor of shape `(1, 12)`, and all values
  are finite. The source exporter itself does not run this post-save check.

## ONNX artifact

- Path convention:
  `logs/x1_dh_stand/exported_onnx/<timestamp>/x1_policy.onnx`.
- Source: a JIT artifact, never the training checkpoint.
- Export contract: random example input `(1, 3102)`, opset 11, constant folding,
  embedded parameters, input name `input`, and output name `output`.
- Shape contract: fixed input `(1, 3102)` and output `(1, 12)`; source does not
  set `dynamic_axes`, so do not assume variable batch size.
- Acceptance: nonempty file, `onnx.checker.check_model` succeeds, graph I/O
  names and shapes match, and—when ONNX Runtime is an approved target—a CPU
  `(1, 3102)` inference returns finite output with shape `(1, 12)`.

For a stronger parity check, run several fixed random inputs through the loaded
JIT module and ONNX Runtime and compare outputs with recorded tolerances. Save
PyTorch, ONNX, and ONNX Runtime versions with that evidence. Parity validates
conversion, not upstream observation semantics.

## Helper result contract

- Exit `0`: every requested check that could run passed.
- Exit `1`: path, load, graph, shape, name, or finite-value check failed.
- Exit `2`: CLI usage or unknown strict task contract.
- Exit `3`: a requested artifact/checkpoint validation was skipped because an
  optional inspection library was unavailable.

`SKIP` and path-only success are not full artifact validation.

## Verification status

- Source parsing, X1 config dimensions, checkpoint layout, architecture, output
  naming, stage boundaries, and helper behavior are statically evidenced.
- Safe helper parser, selection, and synthetic artifact checks can validate only
  their stated model-side contracts.
- Full source checkpoint → JIT and JIT → ONNX runs are
  `BLOCKED_REQUIRED_BACKEND` wherever Isaac Gym Preview 4 is unavailable,
  because both scripts import the environment registry before conversion.
- Never promote a bundled-helper pass to full repository export verification.
