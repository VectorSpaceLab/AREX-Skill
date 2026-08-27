---
name: training
description: "Route VPG model, training, testing, and resume work for reactive
  or reinforcement policies operating on RGB-D heightmaps; validate commands and
  artifacts before any long-running or hardware-bound loop."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# VPG training

Use this route when the task is to inspect, train, test, or resume a VPG
push/grasp policy from an RGB-D heightmap. The distilled evidence is pinned to
source commit `580e2334beec0d83b49e6ca89d7542b79d1d4350`, a historical Python
2/early-Python-3 checkout with no package metadata. It is an operating guide,
not a claim that the complete loop is compatible with current Python, PyTorch,
robot, or simulator stacks.

## Scope and routing

- **Own here:** `main.py` flags and defaults, `models.py`/`trainer.py` model
  behavior, reactive versus reinforcement targets, action choice, rotations,
  preprocessing, exploration, replay, heuristics, snapshots, and transition
  logs.
- **Route RGB-D projection, camera poses, workspace geometry, and heightmap
  construction to** [perception-geometry](../perception-geometry/SKILL.md).
- **Route simulator startup, scenes, meshes, and remote API failures to**
  [simulation](../simulation/SKILL.md).
- **Route metric aggregation and plots to** [evaluation](../evaluation/SKILL.md).
- **Route physical camera, UR5 motion, TCP services, and calibration to**
  [real-robot](../real-robot/SKILL.md).

Do not start the source application's `main.py` merely to inspect this skill.
It opens a camera/robot adapter, may create a simulator or physical action
loop, initializes networks, and runs indefinitely until an environment-specific
stop condition. The bundled validator is deliberately side-effect free:
[check_training_config.py](scripts/check_training_config.py).

## Install and import boundary

There is no package metadata or supported `pip install` target in the source
artifact. In a separately prepared application environment, install the
public README-level dependencies with an explicit environment policy rather
than relying on this skill to modify it:

```bash
python -m pip install numpy scipy opencv-python matplotlib torch torchvision
```

A bounded current-Python numerical-stack check can report imports and an
optional small CUDA allocation through
`<skill-root>/scripts/check_environment.py`; those are compatibility
observations, not full-loop or snapshot-compatibility proof. Historical source
imports and source `main.py`/`evaluate.py`/`plot.py` help probes were
construction evidence only and are not runtime instructions. `torchvision`
model construction may attempt a pretrained-weight download; do not allow
that network side effect during a safe check.

If this graph is imported into an agent skill directory, import the containing
repo skill graph as one transaction through its root workflow; do not copy or
import this sub-skill alone, and do not import it into a live router without
separate approval. The runtime files here contain no source-checkout or
machine-specific inspection dependency.

## Operating procedure

1. **Choose the method and environment.** Use `--method reactive` for the
   classification/label variant, or `--method reinforcement` for the Q-value
   variant (the source default). Use `--cpu` for a correctness-oriented,
   slower path. CUDA is optional but practically important; verify it before
   allocating a long run.
2. **Preflight without starting the loop.** Run the validator with the same
   method, testing flags, snapshot, and session paths. It checks flag
   combinations, file types, continuation logs, and numeric ranges without
   importing torch, loading a state dict, downloading weights, opening a
   socket, or creating directories.
3. **Prepare RGB-D inputs.** The upstream geometry route must supply an RGB
   heightmap `(H,W,3)` and depth heightmap `(H,W)` in meters. Empty depth cells
   are converted to zero before the trainer; retain geometry/calibration
   provenance separately.
4. **Select and execute actions.** A volatile forward pass produces push and
   grasp maps for 16 rotations. The main loop selects the maximum map entry,
   maps `(rotation, y, x)` to an action, and sends it to the environment. Keep
   the simulator/robot prerequisite and safety confirmation outside this
   route.
5. **Train or test deliberately.** Testing disables exploration and replay in
   the loop and stops only after the simulator/test clearance count reaches
   `--max_test_trials`; it still needs a real environment. Training writes a
   backup snapshot every iteration and a numbered snapshot every 50 steps.
   Testing does not save snapshots.
6. **Resume only from a complete pair.** Use a compatible model state dict
   plus `--continue_logging` pointing at the exact prior session. Validate all
   transition logs before allowing the loop to read them. Stop if the snapshot
   cannot load, a log is missing/truncated, or the method differs from the
   snapshot architecture.

## Safe test template

First validate a bounded, one-trial configuration; this command does not run
training or testing:

Let `<skill-root>` mean the directory containing the root `SKILL.md`. This
side-effect-free preflight uses only the bundled helper; `<MESH_DIR>`,
`<CASE>`, `<SNAPSHOT>`, and `<LOG_DIR>` are operator-supplied external paths:

```bash
python <skill-root>/sub-skills/training/scripts/check_training_config.py \
  --method reinforcement --is_testing --max_test_trials 1 --cpu \
  --is_sim --obj_mesh_dir <MESH_DIR> --test_preset_cases \
  --test_preset_file <CASE> --load_snapshot --snapshot_file <SNAPSHOT> \
  --logging_directory <LOG_DIR>
```

Only after an operator has verified the external simulator/scene, object
assets, snapshot provenance, and stop plan should a separately prepared
application launch be attempted. Use `python <APP_ROOT>/main.py` with the
same flags, where `<APP_ROOT>` is an operator-supplied, separately reviewed
application root—not this runtime graph. A live command is intentionally not
presented as a successful recipe: the graph supplies no simulator, robot,
pretrained weights, or historical application loop. Use one trial and stop on
the first unexpected action, missing frame, or load warning.

## References and helper

- [CLI flags and safe recipes](references/cli-reference.md)
- [Model, preprocessing, rewards, and updates](references/model-and-training.md)
- [Logging, snapshots, and resume](references/logging-and-snapshots.md)
- [Training troubleshooting and stop boundaries](references/troubleshooting.md)
- [Safe flag/snapshot/log validator](scripts/check_training_config.py)

Source files named in these references are source artifacts used for evidence;
they are not bundled runtime modules and should not be invoked from the
original checkout as a verification shortcut.
