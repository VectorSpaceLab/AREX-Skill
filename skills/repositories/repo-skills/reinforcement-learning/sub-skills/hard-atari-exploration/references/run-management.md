# Run Management for Hard Atari Workflows

Use this reference for long-run layout, checkpointing, resume, local result summaries, and safe bookkeeping across PPO+RND, Go-Explore Phase 1, demo extraction, and robustification.

## Shared run-directory contract

When a hard Atari workflow accepts `--run-dir`, it should use this layout:

```text
run-dir/
  metrics.jsonl
  final.json
  ckpt/
    latest.pt
    best.pt
    step_<N>M.pt
```

Expected semantics:

- `metrics.jsonl`: append-only structured rows with `frames`, speed, gate/progress metrics, losses or archive metrics, and `nan_flag` where applicable.
- `ckpt/latest.pt`: most recent resume checkpoint.
- `ckpt/best.pt`: best checkpoint according to a workflow-specific gate metric, if a gate is available.
- `ckpt/step_<N>M.pt`: milestone checkpoint at implementation-defined frame intervals.
- `final.json`: local summary of the completed or stopped run, independent of W&B or external reports.

Use atomic checkpoint writes (`tmp` file then rename) to avoid corrupting `latest.pt` after a crash.

## `final.json` schema

A compatible final summary should look like:

```json
{
  "frames_total": 10000000,
  "frames_unit": "agent_steps",
  "gate_metric": "game_return_mean_lastK",
  "K": 100,
  "value_mean": 3120.0,
  "value_std": 0.0,
  "episodes_counted": 20
}
```

Workflow-specific interpretation:

| Workflow | `value_mean` meaning | `K` expectation | Caveat |
| --- | --- | --- | --- |
| PPO+RND | Mean of recent sticky-action RL episode returns | Recent return window, often up to 100 | Sparse-return estimates are noisy and seed-specific. |
| Go-Explore Phase 1 | Best deterministic end-of-episode DONE-cell score | Usually `1` | Search score, not an RL-policy score. |
| Robustification | Mean from-reset sticky-action policy evaluation return | Evaluation episode count | Comparable to sticky-action RL only after from-reset eval. |

Run a schema-only check without reading real run artifacts:

```bash
python scripts/hard_atari_smoke.py --section final-json
```

## Resume semantics by workflow

### PPO+RND

A faithful resume should restore:

- actor-critic weights;
- RND predictor weights;
- frozen RND target weights;
- optimizer state;
- observation RMS: mean, variance, count;
- intrinsic-return RMS: mean, variance, count;
- intrinsic discounted-return filter per environment;
- update counter and derived global step;
- recent episode returns for logging/gates.

If RMS state is missing or reset, the intrinsic reward scale changes and the resumed campaign is not comparable to a continuous run.

### Go-Explore Phase 1

A faithful resume should restore:

- total frames executed and batch counter;
- archive cells, including snapshots, scores, trajectory lengths, trajectory tails, counters, lives, rooms, and recent done scores;
- experience-log state and access to any flushed chunks;
- random generator state.

If resuming into a new run directory, old flushed experience-log chunks may still live in the previous run directory. Preserve or point to those chunks; otherwise demo reconstruction from older cells can fail.

### Robustification

A faithful resume should restore:

- GRU actor-critic weights;
- optimizer state;
- frame/update counters;
- reset manager `max_starting_point` and success statistics;
- NumPy/Torch RNG states;
- per-environment RNG states for sticky actions and starting-point sampling.

After resume, reassign environments from the reset manager so starting points match the restored curriculum.

## Safe launch patterns

Use distinct run directories per workflow, environment, seed, and protocol. Do not reuse a deterministic Phase 1 run directory for a sticky-action robustification job.

```bash
runs/
  rnd-montezuma-seed0/
  ge-montezuma-phase1-seed0/
  demos/
    montezuma-first-key.pkl
  robustify-montezuma-seed0/
```

Template flag contracts:

```bash
# PPO+RND sticky-action RL
python <ppo-rnd-workflow> --env montezuma --seed 0 --run-dir runs/rnd-montezuma-seed0 --ckpt-every 1000000
python <ppo-rnd-workflow> --env montezuma --run-dir runs/rnd-montezuma-seed0 --resume auto

# Deterministic Go-Explore Phase 1
python <go-explore-workflow> --env montezuma_goexplore --seed 0 --run-dir runs/ge-montezuma-phase1-seed0 --ckpt-every 50000000
python <go-explore-workflow> --env montezuma_goexplore --run-dir runs/ge-montezuma-phase1-seed0 --resume auto

# Extract demo from a Phase 1 run. The workflow should prefer best.pt, fall back to latest.pt,
# replay actions deterministically, and refuse to write on score mismatch.
python <demo-extraction-workflow> --run-dir runs/ge-montezuma-phase1-seed0 --out runs/demos/montezuma-first-key.pkl

# Robustify a demo into a sticky-action policy.
python <robustification-workflow> --demo runs/demos/montezuma-first-key.pkl --seed 0 --run-dir runs/robustify-montezuma-seed0 --ckpt-every 1000000
python <robustification-workflow> --demo runs/demos/montezuma-first-key.pkl --run-dir runs/robustify-montezuma-seed0 --resume auto
```

The placeholders are intentional: this skill does not depend on a private checkout path. Use the implementation that matches the named workflow label in your current environment.

## Metrics to monitor

### PPO+RND

| Metric | Healthy signal | Debug if |
| --- | --- | --- |
| `game_return_mean_lastK` / recent return | May stay at 0 for long periods, then jump after sparse events | Drops to NaN or resets unexpectedly after resume |
| `int_rew_mean`, `int_rew_std` | Nonzero early curiosity, gradually decreasing with learning | Zero from the start or exploding to NaN |
| `predictor_loss` | Finite and decreasing slowly | Collapses too fast while score stays flat |
| `entropy` | Does not collapse immediately | Near-zero before any sparse reward |
| `approx_kl` | Small finite PPO updates | Explodes or NaNs |

### Go-Explore Phase 1

| Metric | Healthy signal | Debug if |
| --- | --- | --- |
| `n_cells` | Generally grows as exploration expands | Stalls at root or tiny count |
| `best_done_score` | Improves only when full end-of-episode trajectory is found | Reported without a DONE cell |
| `max_archive_score` | Can improve before an end-of-episode trajectory exists | Treated as final score without caveat |
| `rooms_found` | Diagnostic only | Used as an archive key instead of screen cell |
| `explog_entries` | Tracks action log growth | Missing chunks after resume |

### Robustification

| Metric | Healthy signal | Debug if |
| --- | --- | --- |
| `curriculum_progress` | Moves from near 0 toward 1 as starts move backward | Stuck at a plateau for long runs |
| `max_starting_point` | Decreases as policy masters suffixes | Resets after resume |
| `as_good_as_demo_rate` | Positive on practiced suffixes | Always zero even near demo end |
| final eval return | From-reset sticky-action policy result | Reported from curriculum starts instead of reset |

## W&B and network behavior

External logging is optional. A run should be usable without network access. If W&B is enabled, still treat local `metrics.jsonl`, checkpoints, and `final.json` as the canonical artifacts for recovery and comparison.

## Artifact movement and cleanup

- Keep `ckpt/` and `explog/` together for Go-Explore. A checkpoint without its experience-log chunks may be unable to reconstruct demos.
- Do not copy only `best.pt` for Phase 1 if the experience log lives elsewhere.
- Keep demo pickles immutable once robustification starts; changing `actions`, `returns`, or checkpoints invalidates resume comparability.
- Store protocol in names or metadata: `rnd`/`sticky`, `ge-phase1`/`deterministic`, `robustify`/`sticky`.

## Bounded validation before expensive runs

Before launching a long run:

```bash
python scripts/hard_atari_smoke.py
```

This checks model shapes, RND normalizer invariants, pure-data archive/log reconstruction, demo schema validation, robustification GRU shapes, curriculum movement, and `final.json` schema. Passing it means only that the distilled contracts are internally consistent; it does not verify ROM availability, envpool throughput, ALE restore, W&B, or benchmark-scale learning.
