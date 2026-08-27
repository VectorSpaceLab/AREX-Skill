# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of DRL-Pytorch. If the current repo commit, dirty state, package metadata, algorithm folders, or public launcher behavior differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T19:34:04Z",
  "repository": {
    "name": "DRL-Pytorch",
    "remote_url": "https://github.com/XinJingHao/DRL-Pytorch.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "83486646f12d44e4e94a834e495b81a8f2710055",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "not-installable-script-collection",
      "version": null,
      "import_names": [
        "Q_learning",
        "DQN",
        "PriorDQN",
        "LPRB",
        "Categorical_DQN",
        "NoisyNetDQN",
        "PPO",
        "DDPG",
        "TD3",
        "SACD",
        "SAC",
        "Agent",
        "AtariNames",
        "tianshou_wrappers"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "1.Q-learning",
      "2.1_Duel-Double-DQN",
      "2.2_Noisy-Duel-DDQN-Atari",
      "2.3 Prioritized-Experience-Replay-DDQN-DQN/LightPriorDQN_gym0.2x",
      "2.3 Prioritized-Experience-Replay-DDQN-DQN/PriorDQN_gym0.2x",
      "2.3 Prioritized-Experience-Replay-DDQN-DQN/PriorDQN_gym0.1x",
      "2.4_Categorical-DQN_C51",
      "2.5_NoisyNet-DQN",
      "3.1 PPO-Discrete",
      "3.2 PPO-Continuous",
      "4.1 DDPG",
      "4.2 TD3",
      "5.1 SAC-Discrete",
      "5.2 SAC-Continuous",
      "6. Actor-Sharer-Learner"
    ],
    "docs": [
      "README.md",
      "1.Q-learning/README.md",
      "2.1_Duel-Double-DQN/README.md",
      "2.2_Noisy-Duel-DDQN-Atari/README.md",
      "2.3 Prioritized-Experience-Replay-DDQN-DQN/README.md",
      "2.4_Categorical-DQN_C51/README.md",
      "2.5_NoisyNet-DQN/README.md",
      "3.1 PPO-Discrete/README.md",
      "3.2 PPO-Continuous/README.md",
      "4.1 DDPG/README.md",
      "4.2 TD3/README.md",
      "5.1 SAC-Discrete/README.md",
      "5.2 SAC-Continuous/README.md",
      "6. Actor-Sharer-Learner/README.md"
    ],
    "examples": [
      "algorithm-local main.py launchers",
      "README command examples"
    ],
    "tests": [],
    "configs": [],
    "excluded_from_runtime_bundling": [
      "Old version zip archives",
      "model/*.pth binary checkpoints",
      "runs/ TensorBoard outputs",
      "image/GIF/result assets"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If the upstream repository becomes an installable package or changes its algorithm directory names, refresh this skill.
- If launcher flags, `EnvIdex` maps, checkpoint naming, or optional dependency requirements change, refresh the relevant sub-skill.
- If dirty paths include algorithm source files rather than generated skill artifacts, refresh before trusting command or API details.
