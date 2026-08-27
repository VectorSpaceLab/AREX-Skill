# Actuator workflow

Use the [data contract](data-format.md) first, then [troubleshooting](troubleshooting.md)
if a check fails. The source evidence is `scripts/actuator_net/utils.py`,
`train.py`, `eval.py`, the example deployment log, and the
`resources/actuator_nets/unitree_go1.pt` artifact. The source `eval.py` is
reference material only: it assumes source-relative paths and always reaches
interactive Matplotlib plotting.

## 1. Inspect, then prepare

Start with a read-only validation:

```bash
python scripts/inspect_actuator_log.py path/to/log.pkl
python scripts/inspect_actuator_log.py fixture.json
```

The command reports the envelope, record count, required-key/shape status, and
sample count. It never imports Torch, loads a network, trains, plots, or writes
an output. It rejects a missing `tau_est`, an incomplete pickle (`EOFError`),
malformed 12-joint arrays, non-finite values, and fewer than four complete
records.

For a portable deterministic representation, run:

```bash
python scripts/prepare_actuator_data.py fixture.json
python scripts/prepare_actuator_data.py fixture.json --output prepared.json
```

The default output is JSON on stdout. `--output` writes only to a new explicit
path; an existing file requires `--force`. The extractor emits feature names,
target name, joint count, history, aligned time indices, and feature/target
rows. It does not mutate the input and does not train, load a model, plot, or
access a network.

## 2. CPU evaluation (default)

Use CPU for the smallest safe model check. Load the supplied artifact with
`torch.jit.load(path, map_location="cpu").eval()`, create a float32 tensor of
shape `(N, 6)`, and run it under `torch.no_grad()`. The expected output is
`(N, 1)`, one predicted torque per prepared row. Check finiteness and report
input/output shapes; do not interpret a forward pass as a robot safety or
closed-loop performance guarantee.

The repository artifact `resources/actuator_nets/unitree_go1.pt` was loaded on
CPU during construction and accepted `(3, 6)` input with `(3, 1)` float output.
It is an artifact contract, not a binary to copy into the generated skill.
Keep any user-supplied model outside the skill tree and validate its interface
before use. If the artifact is absent or incompatible, use
[troubleshooting](troubleshooting.md); do not silently build a randomly
initialized replacement for evaluation.

A no-plot evaluation path is intentional. Do not call the source helper's
Matplotlib code, `plt.show()`, or a display backend just to validate the model.
If visual comparison is explicitly requested, make plotting opt-in, cap the
number of points, use a headless backend such as `Agg`, and save to an explicit
new path. Plotting is never a prerequisite for data validation or CPU
inference.

## 3. Optional bounded training and TorchScript export

Training is an opt-in experiment, not the default workflow. First validate and
prepare data, confirm the output path, and obtain explicit approval for the
compute budget and overwrite policy. Use a small synthetic/fixture smoke or a
bounded subset before any real log.

The source `build_mlp` call is:

```python
build_mlp(in_dim=6, units=32, layers=2, out_dim=1, act="softsign")
```

It means two hidden `Linear(…, 32)` layers, a `softsign` activation after each
hidden layer, and a final linear output of one torque value. The source uses
Adam with `lr=8e-4`, `eps=1e-8`, and `weight_decay=0.0`, batch size 128, and
MSE loss. The source function hard-codes `device = "cuda:0"` and **100
epochs**; those 100 epochs are opt-in only and must not be launched
implicitly. Prefer an adapted harness with an explicit device, epoch cap,
seed, batch limit, and output path rather than calling the source-relative
launcher directly.

CUDA is optional. If CUDA is unavailable, do CPU extraction/evaluation and
report training as blocked or deferred; do not install drivers, switch
machines, or claim a CUDA result. If CUDA is approved, verify
`torch.cuda.is_available()` and the selected device before allocating data,
then bound memory, records, epochs, and wall-clock time. Never use physical
robot control as a training smoke test.

After an explicitly approved run, export with `torch.jit.script(model)` and
save to the requested new path. Re-load the saved artifact on CPU and check
`(N, 6) -> (N, 1)` before handing it off. Saving inside a training loop, as the
source function does, is unnecessary for a safe adapted run; save once after
the bounded run. Never overwrite a supplied model or log unless the caller
explicitly passes a force/overwrite decision.

## Route boundaries and non-goals

- Robot data collection, LCM, calibration, deployment, and physical safety:
  [`robot-deployment`](../../robot-deployment/SKILL.md).
- Policy/PPO training or checkpoint playback: [`training-and-policy`](../../training-and-policy/SKILL.md).
- Source scripts are evidence, not runtime dependencies; their relative
  `../../logs/` and `../../resources/` assumptions are deliberately not copied.
- Full training, long benchmarks, interactive plots, network access, and
  hardware actuation are outside this sub-skill and are not run here.

See [api-reference.md](api-reference.md) for source API details and
[data-format.md](data-format.md) for exact time alignment.
