---
name: hard-atari-exploration
description: "Use hard-exploration Atari workflows for PPO plus RND,
  deterministic Go-Explore Phase 1, demo extraction, and sticky-action
  robustification."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Hard Atari Exploration

Use this sub-skill when the task involves sparse-reward Atari workflows such as Montezuma's Revenge, Pitfall, or Private Eye; PPO with Random Network Distillation (RND); deterministic Go-Explore Phase 1 archive search; extracting a replayable demo; or robustifying a deterministic demo into a sticky-action policy. This sub-skill is self-contained and does not require the original checkout at runtime.

## Route here for

- Running, adapting, or debugging the PPO+RND workflow label `1-ppo-rnd.py` for hard-exploration Atari under sticky actions.
- Running, adapting, or debugging deterministic Go-Explore Phase 1 workflow label `2-go-explore.py`, including archive cell keys, snapshots, experience logs, and replay verification.
- Extracting and validating a demo pickle workflow label `extract_demo.py` before robustification.
- Running, adapting, or debugging robustification/backward-algorithm workflow label `3-robustify.py`, including demo resets, recurrent PPO, curriculum progress, and from-reset sticky-action evaluation.
- Explaining why deterministic restore-based Go-Explore scores are not cross-comparable with sticky-action RL scores.

## Route away from

- Standard Breakout/Pong DQN or PPO, `FireResetEnv`, life-loss terminal training, replay buffers, or standard Atari W&B runs: use the standard Atari sub-skill.
- CartPole DQN/A2C/PPO: use the CartPole sub-skill.
- GridWorld dynamic programming, tabular control, Deep SARSA, or REINFORCE: use the GridWorld sub-skill.

## Start here

1. Read [`references/rnd-and-envpool-guide.md`](references/rnd-and-envpool-guide.md) for PPO+RND model/RMS details, envpool versus render-env split, sticky-action assumptions, hard environment keys, and safe run templates.
2. Read [`references/go-explore-and-robustification.md`](references/go-explore-and-robustification.md) for deterministic Go-Explore Phase 1, archive/cell/log mechanics, ALE restore pitfalls, demo pickle schema, extraction checks, and robustification curriculum.
3. Read [`references/run-management.md`](references/run-management.md) before launching long jobs, resuming checkpoints, interpreting `metrics.jsonl` or `final.json`, or moving run directories.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) for protocol mismatches, missing ROMs, envpool/ALE installation problems, demo validation errors, RND novelty collapse, robustification plateaus, and checkpoint issues.
5. Run the bundled smoke script for self-contained CPU checks that do not import source files, launch envpool/ALE, require Atari ROMs, use W&B, or consume real run artifacts:

```bash
python scripts/hard_atari_smoke.py --help
python scripts/hard_atari_smoke.py
python scripts/hard_atari_smoke.py --section rnd
python scripts/hard_atari_smoke.py --section go-explore
python scripts/hard_atari_smoke.py --section demo --demo path/to/demo.pkl
python scripts/hard_atari_smoke.py --section robustify
```

The smoke script reimplements tiny model, RMS, archive/log, final-summary, and demo-schema fixtures. It validates interfaces and invariants only; it does not claim benchmark progress or first-key discovery.

## Critical facts to preserve

- PPO+RND uses sticky-action Atari (`repeat_action_probability=0.25`) and a vectorized envpool training backend for breadth. Its single-env render/test path is a separate Gymnasium/ALE path and is not a replacement for high-throughput training.
- Go-Explore Phase 1 is deterministic restore-based search: frameskip 4, sticky actions off, no no-ops, raw ALE `cloneState`/`restoreState`, and archive scores from replayable trajectories. It is not an RL-policy score.
- Robustification turns a deterministic demo into a recurrent policy trained and evaluated under sticky actions. Only the from-reset sticky-action evaluation is comparable to sticky-action RL methods such as PPO+RND.
- `run-dir` outputs use `metrics.jsonl`, `ckpt/latest.pt`, optional milestone/best checkpoints, and `final.json`. Resume should restore optimizer/model state plus normalizers, archive/log state, curriculum state, and RNG state as applicable.
- RND depends on single-last-frame observation RMS, intrinsic-return RMS, non-episodic intrinsic GAE, dual value heads, frozen random target network, and throttled predictor updates.
- Go-Explore archive cells store low-resolution quantized screen keys, snapshots, score, trajectory length, trajectory tail pointer, selection counters, and lives. The experience log is a `prev_id` linked list used to reconstruct demos.
- After an ALE restore, RAM/screen reads may be stale until a real action executes. Derive Go-Explore cell keys and demo replay frames from step returns, not immediate post-restore reads.
