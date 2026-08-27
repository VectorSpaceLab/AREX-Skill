# Export troubleshooting

Use this table before changing code. Preserve the exact command, selected run,
checkpoint, source/target paths, package versions, and whether Isaac Gym was
available in the handoff record.

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| `ModuleNotFoundError: isaacgym` or an import failure below `humanoid.envs` | Isaac Gym Preview 4 is absent or not on `PYTHONPATH`; both source exporters import the environment registry | Record `BLOCKED_REQUIRED_BACKEND`. Install/configure the approved Isaac Gym Preview 4 environment, verify an Isaac Gym example, then rerun. Do not stub the module. |
| Task lookup reports `x1_dh_stand` is not registered | `humanoid.envs` did not finish importing, wrong checkout/install, or task spelling differs | Use the exact registered name and verify editable installation plus the required backend. Do not invent a task config in the exporter. |
| `No runs in this directory` | Wrong experiment name, wrong logs root, or no training output | Run `preflight_export.py` with explicit `--logs-root`, `--experiment-name`, and `--load-run`; inspect only the supplied artifact handoff. Do not let `-1` choose an unrelated run. |
| Latest run is not the intended run | `-1` sorts directory names and chooses the last one; it is not metric-aware | Pass the exact run directory name and record it. |
| Explicit checkpoint cannot be found | Source expects the exact filename `model_<N>.pt` under the chosen run | Check the checkpoint handoff and use `--checkpoint N`; do not rename a checkpoint to hide a mismatch. |
| `model_state_dict` missing | The file is not a runner checkpoint, is corrupted, or came from another serialization path | Stop and inspect the trusted checkpoint producer. The JIT exporter cannot consume a bare actor or optimizer-only file. |
| `Missing key(s)` / `Unexpected key(s)` in `load_state_dict` | Wrong task/policy class, changed network dimensions, or incompatible checkpoint | Compare the dimensions in `artifact-contract.md`; use the matching task/config. Do not set `strict=False` in the source exporter. |
| Preflight reports a layer shape mismatch | Checkpoint is not the verified X1 DH architecture, or the selected run is wrong | Select the correct checkpoint; for a deliberately changed architecture, create a new task-specific contract rather than exporting under this route. |
| JIT export fails at `torch.jit.script` | Unsupported TorchScript construct/version, device tensor, or a changed wrapper | Reproduce with the repository's supported PyTorch family and a CPU copy. Do not replace scripting with an unrecorded trace; tracing can hide shape/control-flow errors. |
| JIT file is absent after a successful-looking run | Output path was inferred from a fresh timestamp or the process stopped before save | Use the printed `Export policy to:` line, check the timestamp directory, and rerun with a unique start time. |
| ONNX script loads a directory instead of a JIT module | The ONNX helper's local loader picks the last directory entry/file entry and does not validate suffix | Pass an explicit `--load_run=<jit_timestamp>` and preflight the selected `policy_dh.jit` first. |
| `--checkpoint` appears to have no effect for ONNX | The ONNX script consumes a JIT artifact and its local `get_load_path` ignores `checkpoint` | Select the JIT timestamp via `--load_run`; do not expect ONNX to reopen `model_N.pt`. |
| `No module named onnx` during ONNX export | Optional ONNX exporter dependency is missing | Install an approved PyTorch-compatible `onnx` package explicitly, verify `import onnx`, then rerun. No model download is required. |
| ONNX checker fails after a file was written | Unsupported op, incomplete save, or incompatible exporter/runtime | Keep the file as failed evidence, run `onnx.checker.check_model`, compare opset 11 and package versions, and regenerate only after fixing the dependency/compatibility cause. |
| ONNX Runtime rejects the model | Runtime lacks an exported operator, provider mismatch, or input name/shape mismatch | Use the graph's `input`/`output` names and `(1, 3102)` shape, try the approved CPU provider, and record runtime versions. Do not silently change the graph. |
| JIT/ONNX output has unexpected action width | Wrong task or stale artifact; X1 DH should return 12 actions | Validate the artifact directly with the bundled helper and trace the task/config/checkpoint handoff. |
| Output path collides with another export | Both source scripts use second-resolution timestamps and `exist_ok=True` | Avoid concurrent same-task exports in one second; copy completed artifacts to a uniquely named handoff directory only after validation. |
| CPU model check passes but robot behavior is wrong | Model serialization passed, while observation history/order/scales or action interpretation differ | Check the environment observation producer and downstream controller contract. This route excludes playback, MuJoCo, and safety validation. |

## Minimal diagnostics

These commands do not import the repository or Isaac Gym:

```bash
python sub-skills/export/scripts/preflight_export.py --help
python sub-skills/export/scripts/preflight_export.py \
  --task x1_dh_stand --kind jit --artifact path/to/policy_dh.jit
python sub-skills/export/scripts/preflight_export.py \
  --task x1_dh_stand --kind onnx --artifact path/to/x1_policy.onnx
```

For an input checkpoint, add `--inspect-checkpoint`; this invokes
`torch.load(..., map_location='cpu')` only on the path you supplied. Use only
trusted local files. The helper never creates a model, downloads a dependency,
starts training, or claims Isaac Gym verification.

## Stop conditions

Stop with `BLOCKED_REQUIRED_BACKEND` when the source import chain cannot load
Isaac Gym Preview 4. Stop with `BLOCKED_ARTIFACT_INPUT` when the required
checkpoint or JIT handoff is absent. Stop with `FAILED_ARTIFACT_CHECK` when a
serialized file exists but its load, graph, shape, or optional runtime check
fails. Keep these states distinct in downstream reports.
