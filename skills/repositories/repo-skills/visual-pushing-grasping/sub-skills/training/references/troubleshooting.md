# Training troubleshooting

Use the failure class to choose a safe next step. The source is a historical
Python 2/early-Python-3 program; a clean import or `-h` result does not promote
an unresolved full-loop issue to a supported configuration.

## Install and import failures

**Symptoms:** no package can be installed, `import torch` fails, or a source
module cannot be imported.

1. Confirm the application environment's Python and package versions without
   modifying the skill tree. There is no `setup.py`, `pyproject.toml`, or
   supported package install contract in the source artifact.
2. Install the README-level NumPy, SciPy, OpenCV-Python, Matplotlib, torch, and
   torchvision dependencies in a controlled environment. Do not install
   simulator, robot, or camera SDKs as a substitute for a Python import.
3. Let `<skill-root>` mean the directory containing the root `SKILL.md` and
   run the bundled, source-free check:
   `python <skill-root>/scripts/check_environment.py`. It reports only the
   current numerical stack and optional CUDA allocation; it does not prove the
   full loop. The named historical source imports were construction evidence
   only and are not a runtime instruction.
4. If the failure is a Python 3 slice error, removed torch argument, or
   torchvision constructor/API error in an operator-supplied application, stop
   rather than patching silently. The generated skill documents behavior from
   the pinned source; a compatibility port is a separate change and requires
   new tests.

**Do not** run source scripts from the historical checkout as a substitute for
this helper. The named source scripts are evidence artifacts; the bundled
validator has no source imports and remains safe after the checkout disappears.

## CPU and CUDA selection

**Symptoms:** CUDA is unavailable, out-of-memory, or CPU is unexpectedly slow.

- Run with `--cpu` for parser, log, and carefully bounded functional checks.
  The source explicitly supports this mode and prints whether CUDA was
  detected/overridden. Expect much slower inference/training; do not infer a
  hang from a long first forward.
- Without `--cpu`, the trainer chooses CUDA whenever `torch.cuda.is_available()`
  is true and moves the model/loss/tensors to the default device. Verify the
  device and free memory before starting a loop. A small GPU tensor smoke passed
  during construction, but no full model loop or snapshot was validated.
- A GPU OOM can be caused by four DenseNet trunks, 16 rotations, visualization,
  or replay. Stop the loop, preserve the session, then retry with `--cpu` or a
  bounded non-training check. Do not delete snapshots to make an OOM appear
  resolved.
- A CUDA-only load failure may be a serialization/device mapping problem, not
  a bad path. The historical code does not pass `map_location` to `torch.load`;
  do not claim that a CPU run can load every GPU snapshot.

## Snapshot and torch/torchvision mismatch

**Symptoms:** `load_state_dict` reports missing/unexpected keys or shape
mismatches; `torch.load` fails; model construction tries to fetch weights; or a
pretrained demo snapshot behaves differently from a new model.

1. Confirm `--method` matches the snapshot family. Reactive heads have three
   output channels; reinforcement heads have one. Never load a reactive state
   dict into a reinforcement trainer or vice versa.
2. Confirm the snapshot was produced by the same historical model layout,
   trunk naming, and compatible torch/torchvision serialization behavior. The
   source README explicitly warns that its pretrained models were trained with
   PyTorch 0.3, while training from scratch was expected to work with later
   versions; this is not a current compatibility guarantee.
3. Check file size and provenance with the validator, but do not use `torch.load`
   in the validator. If state keys are incompatible, stop and obtain a matching
   environment/snapshot pair or run a separately approved migration experiment.
4. Prevent unintended weight downloads by ensuring the required pretrained
   artifacts are already present or by using a deliberately offline test. The
   four `pretrained=True` DenseNet constructors can trigger network access at
   model construction; the skill never downloads weights automatically.

A valid `.pth` suffix, non-zero size, and matching method suffix are necessary
checks, not proof of loadability.

## Missing or inconsistent logs

**Symptoms:** resume raises `FileNotFoundError`, `loadtxt` shape errors, replay
cannot read an image, or iteration jumps unexpectedly.

- Use `--continue_logging` only with a session root containing `transitions/`
  and all seven required logs: executed-action, label-value, predicted-value,
  reward-value, use-heuristic, is-exploit, and clearance.
- Check that action rows are four columns `[primitive, rotation, y, x]`, IDs are
  0/1, and scalar histories are non-empty and at least as long as the action
  history. Check for a trailing partial line and for a session written by a
  different method.
- Replay additionally requires matching color/depth heightmap PNGs for the
  selected iteration and its next iteration. A transition log without those
  images is not replay-ready.
- Do not create empty files to satisfy the path check. Restore a backup or
  start a new session without `--continue_logging`; report that continuity was
  lost.

The logger can create missing directories for a new session, but a continuation
path is treated as existing state. Keep old sessions read-only while debugging.

## Invalid flag combinations and misleading no-ops

The source parser accepts combinations whose effect is easy to misunderstand.
The safe validator reports these conditions:

- `--load_snapshot` without `--snapshot_file`: source will fail at load time.
- `--continue_logging` without `--logging_directory`: source cannot resolve
  the prior session path.
- `--snapshot_file` without `--load_snapshot`: the value is ignored.
- `--logging_directory` without `--continue_logging`: the source uses the
  default `logs` parent instead; do not assume the supplied directory is used.
- `--test_preset_file` without `--test_preset_cases`: the file is ignored.
- `--push_rewards` with `--method reactive`: `main.py` sets it to `None`.
- `--experience_replay` or `--explore_rate_decay` with `--is_testing`: replay
  is skipped and exploration starts at zero.
- `--is_sim` with real TCP flags, or real mode with simulation mesh/object
  flags: the inactive branch ignores those values. Remove them unless an
  external wrapper intentionally records them.
- `--continue_logging` without `--load_snapshot`: technically parsable but
  unsafe for a normal model resume; the validator warns so the operator can
  make the choice explicit.

For a first test, use `--is_testing --max_test_trials 1 --load_snapshot` and
`--cpu`, then add only the flags required by the known environment. Do not use
`--grasp_only` to conceal a broken push map unless that is the intended
experiment.

## Preprocessing and shape symptoms

**Symptoms:** empty predictions, index errors, NaNs, or a map/action mismatch.

- Verify color is RGB `uint8`-like `(H,W,3)` and depth is `(H,W)` in meters.
  Empty depth is zeroed by the main loop; NaNs left in a direct trainer call
  can corrupt normalization and action maxima.
- Verify depth scale and saved-depth reconstruction. A heightmap PNG is in
  `1e-5` meter units, not camera-native units.
- Keep prediction indexing `(rotation, y, x)`. A swapped x/y can select a valid
  but incorrect robot position.
- The source's output crop and backprop label sizes reflect old assumptions
  and Python-2 division behavior. If current Python produces float slice
  indices or returned maps do not align with the heightmap, stop and record an
  unresolved compatibility gap; do not resize predictions ad hoc in a live
  experiment.

## Safe stop boundaries

Stop before any action when a snapshot warning, missing frame, missing log,
shape mismatch, unexpected primitive, or external-service error appears. Stop
and preserve the session on CUDA OOM, repeated empty-table resets, repeated
no-change heuristics, or an unexplained iteration jump. Never “test” recovery
by running calibration, camera-server startup, simulator startup, or a physical
push/grasp from this route. Those actions require the sibling workflow,
explicit prerequisites, and an operator-approved abort plan.
