# Troubleshooting actuator logs and models

Start with the read-only validator:

```bash
python scripts/inspect_actuator_log.py INPUT
```

Then use [data-format.md](data-format.md) for the exact schema and
[workflow.md](workflow.md) for the CPU/optional-CUDA boundary. Do not solve
collection, LCM, calibration, or robot-controller problems here; route those
to [`robot-deployment`](../../robot-deployment/SKILL.md).

## Log and data failures

### File missing or path is wrong

- Confirm the input path exists and is a file; do not rely on the source
  `log_dir_root + log_dir + "log.pkl"` concatenation.
- Pass the complete explicit path to the bundled validator. It accepts pickle
  and JSON fixtures and does not search or glob directories.
- Do not copy the repository's large example log into the generated skill.

### `hardware_closed_loop` or records are absent

The logger saves a top-level robot dictionary whose relevant value is
`[config, infos]`. Check that the selected robot key is
`hardware_closed_loop`, that it has two elements, and that its second element
is a non-empty record list. For a portable fixture use `{"records": [...]}` or
a JSON list. A configuration object without records is not training data.

### Missing `tau_est`

`tau_est` is the target and cannot be replaced by `torques`,
`joint_vel_target`, or a guessed zero vector. Collect/re-export a complete
log or choose CPU model evaluation on an already prepared dataset. The
validator and extractor intentionally return non-zero for the missing key.

### Incomplete pickle / EOFError

The source `eval.py` catches `EOFError` and labels the pickle incomplete. Do
not retry training against it. Re-copy or re-export the log from a trusted
source, validate it first, and treat a partial last record as invalid rather
than silently dropping it.

### Too short or malformed history

At least four complete records are required because the sample at `t=2` needs
`t`, `t-1`, and `t-2`, and the source alignment stops at `T-2`. Fewer than four
records yields no samples. A record with `joint_pos` shaped `(12, 1)`, a
length other than 12, a missing singleton dimension that still flattens to a
non-12 length, or a non-finite value is rejected. Fix the exporter rather than
padding, truncating, broadcasting, or changing the six-feature contract.

### Shape mismatch across fields or time

Every required field must have 12 values in every record. The first three
fields may be `(1, 12)` in the pickle; `tau_est` and `torques` may be `(12,)`.
The portable scripts normalize only nested wrappers and require exact lengths.
If model input is `(N, 6)` but output is not `(N, 1)`, inspect the model
architecture and artifact before attempting training.

### Non-finite values or surprising units

Reject NaN and infinity. This workflow does not infer units or normalize
positions, velocities, or torques; preserve the source conventions and make
any conversion an explicit, separately reviewed preprocessing step.

## Model and training failures

### Missing or invalid `unitree_go1.pt`

The source artifact is expected to be a TorchScript module accepting six
features and returning one value per row. Load it with
`torch.jit.load(..., map_location="cpu").eval()` and run a tiny finite tensor
check. If loading fails, report the artifact/version problem; do not evaluate
a random model or claim recovered actuator behavior.

### CUDA unavailable

CUDA training is optional, while extraction and pretrained evaluation are
CPU-safe. Check `torch.cuda.is_available()` and the selected device before
allocation. If false, defer training, use a bounded CPU experiment only if
explicitly approved, or stop with a clear optional-backend limitation. Do not
change drivers, start robot code, or claim the source's `cuda:0` training ran.

The source uses 100 epochs, batch size 128, and a 4/5 random split. These are
not safe implicit defaults for a generated-agent run; set an explicit budget
and seed in an adapted harness. Full training is not run by this skill.

### Output already exists / accidental overwrite

Choose a new output path, or make overwrite an explicit user-approved action.
`prepare_actuator_data.py` refuses an existing `--output` unless `--force` is
passed. Apply the same policy to TorchScript export. Never overwrite the
supplied model or original log as a side effect of evaluation.

### TorchScript export or reload fails

Check that the model has the expected 6-input/1-output structure, that all
parameters are on the intended device before scripting, and that the output
parent exists. Save once after a bounded run, then reload on CPU and run a
finite `(N, 6)` smoke input. A successful `torch.jit.script` call alone is not
an evaluation result.

## Plotting and environment issues

### Headless host / Matplotlib backend error

Plotting is not required. Use the validator, extractor, and CPU forward pass.
If a user explicitly needs a figure, select a headless `Agg` backend before
importing pyplot, cap plotted points, and save to an explicit new path; never
call `plt.show()` as a required diagnostic.

### Source script import or relative-path failure

The source `train.py`/`eval.py` assumes a particular working directory and
imports `utils` directly. Do not fix this by adding the repository root to
`sys.path` in the bundled scripts. Use their documented behavior as evidence
and use the self-contained standard-library helpers here.

See [api-reference.md](api-reference.md) for exact source signatures and
[data-format.md](data-format.md) for alignment details.
