# Go-Explore Phase 1, Demo Extraction, and Robustification

This reference covers deterministic Go-Explore Phase 1 workflow label `2-go-explore.py`, demo extraction workflow label `extract_demo.py`, robustification/backward-algorithm workflow label `3-robustify.py`, and their raw-ALE restore plumbing labels `env_go_explore.py` and `env_robustify.py`.

## Protocol separation

There are two distinct hard-Atari protocols:

| Workflow | Protocol | Comparable to |
| --- | --- | --- |
| PPO+RND | Sticky-action RL policy, `repeat_action_probability=0.25` | Other sticky-action RL policy scores under the same evaluation rules |
| Go-Explore Phase 1 | Deterministic restore-based trajectory search, sticky actions off, no no-op variation | Other deterministic Go-Explore/search archive results only |
| Robustification | Sticky-action RL policy distilled from a deterministic demo | Sticky-action RL policy scores after from-reset evaluation |

Do not compare a deterministic Phase 1 score with PPO+RND or robustification scores as if they are the same benchmark. Phase 1 answers "what trajectory did archive search find?" Robustification answers "can a policy execute robustly from reset under stochastic sticky actions?"

## Go-Explore Phase 1 mechanics

Phase 1 has no neural network. It builds a cell archive and repeatedly returns to promising cells via emulator state restore, then explores from that state.

Core loop:

```text
archive: cell_key -> best snapshot, raw score, trajectory length, trajectory tail pointer
repeat until budget exhausted:
  sample archive cells with novelty weighting
  restore each sampled cell snapshot in a worker
  execute a short random exploration episode
  update archive when a new or better cell is reached
  append every accepted step to the experience log
```

### Environment contract

- environment key: `montezuma_goexplore`;
- raw Gymnasium/ALE env, unwrapped so restore-based mid-episode entries are not blocked by wrappers;
- frameskip 4;
- `repeat_action_probability=0.0` for deterministic Phase 1;
- no stochastic no-op starts;
- emulator reset seed is canonicalized; random exploration comes from the algorithm's action RNGs;
- episodes abort on life loss or game over for archive-transition purposes.

Envpool is not used for Phase 1 because envpool does not expose ALE `cloneState` and `restoreState`.

### Cell key

The distilled cell key matches the Go-Explore image-cell idea:

1. take a grayscale Atari frame returned by a real environment step;
2. resize to `11 x 8` pixels with area interpolation;
3. quantize to 9 possible values using `floor(8 * pixel / 255)`;
4. serialize the 88 quantized bytes as the key;
5. pair the key with a done flag; the virtual done cell is `(b"DONE", True)` and is never sampled.

The room RAM byte can be logged as a diagnostic, but the screen key is the archive identity.

### ALE restore pitfall

After `restoreState`, RAM and screen reads may still reflect the pre-restore state until the next emulator action. Therefore:

- do not compute a cell key from immediate post-restore RAM or screen data;
- compute keys only from frames returned by `step` after a real action;
- carry the lives baseline in the sampled cell metadata so life-loss termination is based on the restored state's lives, not a stale post-restore read.

### Archive accept rule

A cell is inserted or replaced when the new trajectory has:

1. a strictly higher raw score; or
2. equal raw score and shorter trajectory length.

When a cell is updated, reset its selection counters. If exploring from a sampled cell discovers anything new, reset that sampled cell's `chosen_since_new` counter.

### Cell sampling

Select cells with replacement using weight approximately:

```text
weight(cell) = 1 / sqrt(seen_times + 1)
```

Exclude the virtual done cell from sampling. Capture the sampled cell's snapshot, lives, score, trajectory length, and trajectory tail at sampling time. Do not stitch actions generated from an old snapshot onto a newer live cell prefix after another result updates the same cell; that fabricates an impossible trajectory.

## Experience log and demo reconstruction

The experience log is an append-only linked list:

```text
entry_id -> {prev_id, action, reward, done}
```

Each archive cell stores only `traj_last`, the tail entry id. Reconstruct a trajectory by walking `prev_id` back to `-1`, collecting actions, and reversing them. Large runs flush log chunks to compressed files; if resuming into a new run directory, the resumed log may need access to the ancestor chunk directory.

Use the smoke script for pure-data archive/log checks:

```bash
python scripts/hard_atari_smoke.py --section go-explore
```

## Demo extraction schema

A robustification demo pickle is replayable evidence extracted from a Go-Explore run. It should contain:

| Key | Required type/shape | Meaning |
| --- | --- | --- |
| `actions` | 1-D int array, length `T` | Agent actions at frameskip-4 step granularity |
| `rewards` | 1-D float array, length `T` | Raw, unclipped rewards from deterministic replay |
| `returns` | 1-D float array, length `T` | Cumulative raw return-to-here; should equal `cumsum(rewards)` |
| `checkpoints` | non-empty list/tuple of bytes | Pickled ALE states used as restore points |
| `checkpoint_action_nr` | 1-D int array | Action index for each checkpoint, sorted and within `[0, T)` |
| `score` | float | Sum of raw rewards in the truncated demo |
| `env_id` | string | ALE env id, usually `ALE/MontezumaRevenge-v5` |
| `protocol` | mapping | Should state `frameskip: 4`, `sticky: 0.0`, `seed: 0` for Phase 1 replay |
| `source_run` | optional string | Provenance label for the run that produced the demo |
| `ale_py` | optional string | ALE package version used during extraction |

The extraction workflow reconstructs actions from the DONE cell, replays them deterministically, checks that replay score equals the archived DONE score, then truncates after a reward boundary. A mismatch means the demo is not replayable and should not be used for robustification.

Validate a real demo pickle without launching ALE:

```bash
python scripts/hard_atari_smoke.py --section demo --demo path/to/demo.pkl
```

This schema check cannot prove emulator replayability; it only catches malformed or internally inconsistent pickle contents before an expensive robustification attempt.

## Robustification / backward algorithm

Robustification trains a recurrent policy to reproduce a deterministic demo under sticky actions. Episodes start from points along the demo and move backward toward reset as the policy succeeds.

### Environment wrapper contract

- raw ALE env with built-in sticky probability disabled;
- a custom sticky-action filter applies `p=0.25` below frameskip so the demo replay path can remain deterministic;
- each episode restores to a demo checkpoint, replays deterministic demo actions up to the sampled starting point, then gives control to the agent under sticky actions;
- score is initialized with the demo prefix return so success can be tested against the full demo score;
- the frame returned after reset comes after a real no-op action to avoid stale post-restore reads;
- when starting from reset, use 0-30 no-ops for sticky-action policy evaluation.

### Curriculum contract

The reset manager tracks `max_starting_point`:

```text
max_starting_point = demo length - 1   # starts near the demo end
success at suffixes accumulates        # policy matches demo return from late starts
max_starting_point moves backward      # smaller index means harder start
max_starting_point -> 0                # policy can attempt whole task from reset
```

The main progress metric during training is curriculum progress:

```text
curriculum_progress = 1 - max_starting_point / max_demo_index
```

A high deterministic Phase 1 demo score does not imply the robustified policy can score from reset. The final from-reset sticky-action evaluation is the policy result.

### Recurrent policy contract

The robustification model is a GRU actor-critic:

- input: `(batch, 4, 105, 80)` grayscale frame stacks;
- CNN trunk followed by a fully connected layer and layer norm;
- GRUCell hidden state, typically 256 units in the full workflow;
- outputs policy logits and a scalar value;
- rollout training uses done-masked recurrent unrolls for truncated BPTT;
- artificial success-cutoff/reset steps are masked out of GAE/loss.

CPU shape check:

```bash
python scripts/hard_atari_smoke.py --section robustify
```

### Robustification run template

The exact executable name is implementation-specific; the flags below describe the expected CLI contract.

```bash
python <robustification-workflow> \
  --demo demos/montezuma_first_key.pkl \
  --seed 0 \
  --n-envs 16 \
  --total-frames 20000000 \
  --device auto \
  --run-dir runs/robustify-seed0 \
  --ckpt-every 1000000

python <robustification-workflow> \
  --demo demos/montezuma_first_key.pkl \
  --run-dir runs/robustify-seed0 \
  --resume auto
```

Treat a single-machine plateau as a scale/optimization signal, not proof that the demo is invalid. The original robustification method relied on substantial parallelism and many reset environments; a small run may never reach from-reset success.
