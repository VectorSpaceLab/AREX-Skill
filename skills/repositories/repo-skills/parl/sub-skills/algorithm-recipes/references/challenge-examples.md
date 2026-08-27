# Challenge Examples

PARL ships several competition-oriented examples. They are valuable design references, but they are not safe default runtime scripts: they depend on old package versions, external simulators, pretrained model downloads, many CPU workers, or challenge-specific data.

## When to use this reference

Use it when a task mentions:

- NeurIPS AI for Prosthetics / Learn-to-Move examples.
- Learning-to-Run-a-Power-Network (L2RPN) examples.
- Curriculum learning with staged pretrained models.
- Challenge submission/evaluation wrappers.
- Large xparl clusters or hundreds of simulator clients.

Route to `../../../xparl-distributed/SKILL.md` for cluster mechanics and to `../../../environment-utils/SKILL.md` for wrappers/logging/data utilities.

## Challenge inventory

| Example family | Core idea | Algorithm pattern | Runtime risk |
| --- | --- | --- | --- |
| AI for Prosthetics challenge | Curriculum learning and final submission controller for OpenSim prosthetics. | Multi-head DDPG-style actor-critic plus simulator server/client workers. | Old Python/Paddle/PARL versions, OpenSim dependency, gRPC workers, pretrained model downloads, many CPU clients. |
| Learn-to-Move challenge | Staged curriculum for different difficulties and target velocities. | DDPG-style continuous control with xparl cluster and challenge-specific wrappers. | Requires downloaded warm-start models, OpenSim/osim-rl, shell launchers, and large CPU counts. |
| L2RPN power-network challenge | Action-set policy optimization for safe power-grid management. | ES-like and policy-optimization examples around Grid2Op-style tracks. | Challenge datasets/environments and track-specific wrappers; not a generic PARL smoke test. |
| ES MuJoCo example | Evolution strategies for continuous control. | Distributed ES workers with observation filters and noise tables. | MuJoCo, xparl workers, long training, many CPUs; route deeper ES/C++ build issues to `../../../evo-kit/SKILL.md` when applicable. |

## Safe extraction rules

Do extract:

- High-level algorithm pattern: curriculum stages, actor/critic split, simulator-client boundary, evaluation-vs-training separation.
- Shape contracts: observation preprocessing, action scaling, multi-head or ensemble model selection.
- Operational warnings: external simulator, old dependency stack, model checkpoint requirement, distributed worker count.

Do not extract as runnable code by default:

- Shell scripts that start long training/evaluation stages.
- Commands that require 100+ CPU workers or external challenge services.
- Pretrained model download instructions with third-party storage links.
- Challenge-specific generated protocol files as general-purpose APIs.
- Paths, ports, or model names that assume one maintainer's training setup.

## Curriculum-learning adaptation pattern

For challenge-style curriculum, document the stages as a plan before running anything:

```text
stage_0: define environment version, simulator dependency, observation scaler, action bounds
stage_1: train or load a low-difficulty / low-speed base policy
stage_2: warm-start from stage_1 and change reward target or difficulty
stage_3: warm-start from stage_2 and change target distribution
stage_4: freeze/select ensemble heads or submission-specific policy wrapper
eval: run deterministic evaluation with fixed seeds and no learner updates
```

Every stage should state:

- Required pretrained checkpoint or explicit "train from scratch" decision.
- Expected simulator and dependency version.
- Number of actors/clients and whether xparl is required.
- Stop condition and output directory.
- Evaluation metric and whether visual inspection is part of model selection.

## Safe response patterns

| User intent | Safe answer |
| --- | --- |
| "Use the Learn-to-Move example for my continuous-control task" | Extract the continuous-action DDPG/MADDPG-style pattern, action scaling, and curriculum idea. Replace OpenSim-specific wrappers with the user's environment wrapper and keep xparl optional. |
| "Run the challenge scripts" | Ask for explicit approval of simulator installation, pretrained model acquisition, old dependency versions, long runtime, and distributed process side effects. |
| "Why does a challenge example fail?" | First check simulator availability, dependency age, checkpoint/scaler files, xparl cluster state, and observation/action shape drift. Only then debug algorithm methods. |
| "Can I cite benchmark performance from a tiny run?" | No. A bounded smoke run proves wiring only. Challenge scores require the full challenge environment, training budget, seeds, and evaluation protocol. |

## Relationship to built-in algorithms

Most challenge examples use PARL abstractions rather than introducing new generic algorithm classes. When adapting:

- Identify whether the learner is DDPG/TD3/SAC/PPO/ES-like.
- Map model methods back to the algorithm catalog.
- Keep challenge-specific preprocessing in a separate wrapper module.
- Keep distributed collection optional until the local Agent/Algorithm loop passes shape checks.
