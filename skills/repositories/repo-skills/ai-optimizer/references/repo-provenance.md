# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of AI-Optimizer. If the current repository commit, branch, checked-in submodule state, source paths, or public command/API surfaces differ from this snapshot, refresh the skill before relying on detailed routes.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:32:24Z",
  "repository": {
    "name": "AI-Optimizer",
    "remote_url": "https://github.com/TJU-DRL-LAB/AI-Optimizer.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4a4e74e505356e5d16ba5ddcfb6ea368c5863ef7",
    "working_tree": "dirty-generated-output-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "ai-optimizer-collection",
      "version": null,
      "import_names": []
    },
    {
      "name": "planetrl",
      "version": "1.0.0",
      "import_names": ["planet"]
    },
    {
      "name": "ed2-mbpo",
      "version": "0.0.1",
      "import_names": ["mbpo"]
    },
    {
      "name": "mbpo",
      "version": "0.0.1",
      "import_names": []
    },
    {
      "name": "pex",
      "version": "0.0.1",
      "import_names": ["pex"]
    }
  ],
  "evidence": {
    "source_roots": [
      "modelbased-rl/BMPO",
      "modelbased-rl/Dreamer",
      "modelbased-rl/MBPO/ED2-MBPO",
      "modelbased-rl/MuZero",
      "modelbased-rl/PlaNet/planet",
      "modelbased-rl/SampledMuZero",
      "multiagent-rl/easy-marl",
      "offline-rl-algorithms",
      "offline-rl-algorithms/E2O/d3rlpy_new/d3rlpy",
      "offline-rl-algorithms/E2O/PEX-main/pex"
    ],
    "docs": [
      "README.md",
      "modelbased-rl/README.md",
      "multiagent-rl/README.md",
      "multiagent-rl/easy-marl/README.md",
      "offline-rl-algorithms/README.md",
      "algorithm-specific README files under modelbased-rl and offline-rl-algorithms"
    ],
    "examples": [
      "modelbased-rl/MBPO/ED2-MBPO/examples/config",
      "modelbased-rl/CaDM/run_scripts",
      "multiagent-rl/easy-marl/test",
      "offline-rl-algorithms/E2O/PEX-main README command recipes"
    ],
    "tests": [
      "modelbased-rl/PlaNet/planet/scripts/test_planet.py",
      "modelbased-rl/PlaNet/planet/training/test_running.py",
      "modelbased-rl/PlaNet/planet/tools/test_nested.py",
      "modelbased-rl/PlaNet/planet/tools/test_overshooting.py",
      "modelbased-rl/MuZero/core/test.py",
      "multiagent-rl/easy-marl/test/test.py"
    ],
    "configs": [
      "modelbased-rl/BMPO/config",
      "modelbased-rl/MBPO/ED2-MBPO/examples/config",
      "modelbased-rl/MuZero/config",
      "modelbased-rl/PlaNet/planet/scripts/configs.py",
      "multiagent-rl/easy-marl/hyperparameters",
      "modelbased-rl/MBPO/ED2-MBPO/environment/gpu-env.yml"
    ],
    "submodules": {
      "cornerstone": "not-initialized-empty",
      "self-supervised-rl": "not-initialized-empty",
      "transfer-and-multi-task-reinforcement-learning": "not-initialized-empty",
      "multiagent-rl/core": "not-initialized-empty"
    }
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If any empty submodule listed above is initialized in the target checkout, refresh before claiming coverage for that submodule.
- If root package metadata is added, command-line entry points change, or train scripts move, refresh command-builder references and helper scripts.
- If package versions or dependency pins change for TensorFlow, Ray, Gym, MuJoCo, dm_control, D4RL, or PyTorch, refresh the troubleshooting and backend notes.
