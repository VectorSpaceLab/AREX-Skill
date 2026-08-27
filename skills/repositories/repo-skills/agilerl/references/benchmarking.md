# Benchmarking And Performance Scripts

AgileRL includes benchmark launchers for classical RL, multi-agent RL, offline RL, recurrent networks, SimBa/ResNet variants, bandits, and LLM tasks. Those launchers were used as evidence for expected workflows, but they are not bundled as runnable helpers because benchmark runs can be long, hardware-sensitive, and sometimes require external services, datasets, or logging configuration.

## How To Use Benchmark Evidence Safely

- Treat benchmark scripts as templates for algorithm/config choices, not as default validation commands.
- Recreate a tiny smoke version with the relevant public APIs before launching a benchmark-scale run.
- Use the distilled training and benchmarking configuration patterns in this skill rather than depending on original benchmark files.
- Disable or configure W&B/logging before unattended benchmark runs.
- Confirm GPU/CPU backend, environment packages, random seeds, max steps, evaluation frequency, and checkpoint paths.

## Benchmark Families

| Family | Evidence pattern | Safer skill route |
| --- | --- | --- |
| On/off-policy classical RL | PPO, DQN, TD3, Rainbow, recurrent, distributed launchers | `../sub-skills/training-workflows/SKILL.md` |
| HPO/evolvable architecture | SimBa, ResNet, make-evolvable benchmarks | `../sub-skills/evolvable-modules/SKILL.md` and `../sub-skills/hpo-and-mutation/SKILL.md` |
| Multi-agent RL | Multi-agent on/off-policy launchers | `../sub-skills/multi-agent-and-wrappers/SKILL.md` |
| Offline/bandits | Offline and bandit launchers | `../sub-skills/offline-bandits-data/SKILL.md` |
| LLM workflows | Preference, reasoning, multiturn, SFT benchmarks | `../sub-skills/llm-fine-tuning/SKILL.md` |

Do not present a full benchmark as a quick correctness test. Prefer constructor, parser, config, and tiny-fixture checks for agent workflows.
