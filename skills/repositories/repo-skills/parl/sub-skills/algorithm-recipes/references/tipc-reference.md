# TIPC Reference

PARL includes a Training and Inference Pipeline Criterion (TIPC) workflow for checking train/infer coverage across example algorithms. Treat it as reference-only in this skill: the original shell launchers perform installation, downloads, package uninstalls, MuJoCo setup, and xparl process control. Do not run them as a routine validation step.

## What TIPC covers

TIPC classifies basic train/predict support for these PARL example families:

- A2C
- CQL
- DDPG
- DQN
- DQN variants
- ES
- MADDPG
- OAC
- PPO
- QuickStart / PolicyGradient
- SAC
- TD3

The TIPC table is useful when a task asks whether a model has an intended train/inference pathway. It is not proof that the pathway is safe to execute in the current environment.

## Configuration shape

A TIPC test is selected by a model-specific config file and a mode string. Conceptually it contains:

- Python command to use.
- Training script and training arguments.
- Optional evaluation script and pretrained model arguments.
- Export/inference script and inference arguments.
- Hardware switches such as CPU/GPU flags.
- Log/output locations.

The commonly documented invocation pattern is:

```bash
bash prepare.sh <model-config> <mode>
bash test_train_inference_python.sh <model-config> <mode>
```

In this skill, interpret that pattern only as a map from algorithm to pipeline stages. Do not execute it directly.

## Safety classification

| TIPC component | Classification | Why |
| --- | --- | --- |
| Config text files | Reference-safe | They describe train/eval/inference commands and modes. Reading them is safe. |
| Preparation launcher | Skip unsafe / network / system-mutating | It may run package-manager commands, download MuJoCo assets or keys, install Python packages, editable-install the package, and start/stop xparl clusters. |
| Train/inference launcher | Skip unsafe / environment-mutating / long-running | It may train models, run inference/export, create logs, uninstall packages, launch distributed commands, and assume GPU or MuJoCo paths. |
| Common shell helpers | Reference-only | Useful for understanding status logging and command assembly, but not a stable public runtime API. |

## How to use TIPC evidence safely

Use TIPC to answer these questions:

1. Which algorithms have intended basic training/inference coverage?
2. Is the pipeline single-process, distributed, or hardware-dependent?
3. Does the mode imply a tiny smoke run or a real train/eval/export pipeline?
4. Which optional dependencies must be verified before execution?

Do not use TIPC to answer these questions without further verification:

- "Will this converge to the benchmark score?"
- "Is it safe to run in a shared environment?"
- "Are all package versions compatible with the user's current Python environment?"
- "Can I start/stop xparl processes or install system packages without permission?"

## Safe replacement pattern

When a task asks for TIPC-like confidence, replace the original launcher with bounded checks:

```text
1. Read the selected config and extract the algorithm, backend, scripts, mode, and declared dependencies.
2. Run the bundled catalog inspector for the target backend.
3. Import the selected algorithm class and inspect its signature.
4. Build a tiny synthetic model-method assertion for the algorithm family.
5. If the user approves real execution, create an isolated environment plan and run a single tiny command such as --help or --max-episodes 1.
6. Report that the check proves wiring/import/config parsing only, not benchmark accuracy.
```

## Decision guide

| User asks | Response |
| --- | --- |
| "Can I use TIPC for DQN?" | Explain the DQN TIPC coverage and propose config reading plus a safe DQN import/signature check. |
| "Run all TIPC tests" | Ask for explicit approval, isolated environment, hardware, network, runtime budget, and side-effect tolerance; otherwise refuse to run the original launchers. |
| "Why is TIPC failing after prepare?" | Check dependency/version/backend assumptions, MuJoCo/D4RL/Atari requirements, package mutations, and xparl process state before inspecting algorithm code. |
| "Can I adapt TIPC into CI?" | Use help-only/import-only checks by default; gate full train/infer modes behind optional, isolated, long-running jobs. |

## Known high-risk side effects

The original TIPC shell logic can:

- Install system packages through OS package managers.
- Download MuJoCo archives or keys and write under a user's home directory.
- Install, upgrade, or uninstall Python packages.
- Editable-install PARL into the active environment.
- Stop or start xparl processes and bind local ports.
- Run model training and inference/export with log writes.

Because of these side effects, TIPC remains a reference and classification source for this repo skill, not a bundled executable workflow.
