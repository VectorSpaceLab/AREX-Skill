# Backend Verification and Optional Runtime Boundaries

## Purpose

Read this when deciding whether a PARL task can be completed with the currently installed dependencies or whether a backend-specific recheck is needed. This reference distinguishes verified package facts from source-backed optional workflows.

## Verified in this skill production run

| Surface | Verification status | What the check proves | What it does not prove |
| --- | --- | --- | --- |
| Base PARL package metadata | Verified | `parl` distribution version `2.2.1` exists in an isolated inspection environment. | It does not prove every optional framework is installed. |
| Torch backend aliases | Verified on CPU Torch | With `PARL_BACKEND=torch`, `parl.Model`, `parl.Algorithm`, and `parl.Agent` resolve to Torch backend classes. A tiny `parl.Model` can sync/get/set weights. | It does not prove convergence of any RL algorithm or CUDA execution. |
| xparl CLI help | Verified help-only | `xparl --help`, `xparl start --help`, `connect`, `status`, and `stop` help are available without starting a cluster. | It does not prove live worker scheduling, monitor/log-server availability, or network reachability. |
| Environment utilities | Verified with tiny CPU data | Schedulers, replay memory, CSVLogger, and wrapper class imports work in a tiny diagnostic. | It does not prove Atari, MuJoCo, PettingZoo, VisualDL, or TensorBoard optional environments. |

## Source-backed but not runtime-verified here

| Surface | Required dependencies | Skill behavior |
| --- | --- | --- |
| Paddle 2.x backend | `paddlepaddle` or `paddlepaddle-gpu`, compatible Python/NumPy. | The skill provides source/docs-backed guidance and tells users to rerun checks with `PARL_BACKEND=paddle` after installing Paddle. |
| Legacy Fluid backend | Old Paddle Fluid stack (`paddle<2`) on a compatible Python. | The skill treats Fluid as legacy/source-backed and avoids claiming current runtime support. |
| CUDA execution for ordinary PARL algorithms | Backend framework CUDA wheel, driver/toolkit compatibility, and algorithm-specific environment dependencies. | The skill separates CPU API checks from GPU runtime evidence; users must run a backend smoke on their target stack. |
| Waymax-RL | JAX CUDA12, Waymax checkout at documented commit, Waymo-format TFRecord data, Hydra/rl-games stack, suitable GPU. | `waymax-rl` gives a configuration and setup checklist plus a static config validator; it does not claim a CPU substitute or completed training. |
| EvoKit | Native C++ toolchain, `protoc`/protobuf2, OpenMP, glog/gflags, PaddleLite or libtorch assets. | `evo-kit` gives build planning and a read-only prerequisite checker; it does not run build scripts or downloads. |
| TIPC scripts and challenge launchers | Model-specific requirements, possible apt/wget/MuJoCo/OpenSim/SMAC/D4RL/xparl side effects. | `algorithm-recipes` classifies these as reference-only unless a user explicitly authorizes system/network/long-running side effects. |

## Safe checker sequence

From the root of this generated skill, use these non-mutating checks before deeper work:

```bash
python scripts/check_parl_install.py --backend torch --xparl-help
python sub-skills/core-framework/scripts/check_parl_core.py --backend torch --torch-smoke auto
python sub-skills/algorithm-recipes/scripts/inspect_algorithm_catalog.py --backend torch
python sub-skills/environment-utils/scripts/check_env_utils.py --backend torch
python sub-skills/xparl-distributed/scripts/check_xparl_cli.py
```

Optional surfaces have their own read-only checkers:

```bash
python sub-skills/waymax-rl/scripts/validate_waymax_config.py <path-to-hydra-yaml>
python sub-skills/evo-kit/scripts/check_evokit_prereqs.py --project-root <evokit-root> --backend auto
```

## Interpreting failures

- If `import parl` reports no deep learning framework, install exactly one intended backend first or use xparl-only guidance.
- If `PARL_BACKEND` is wrong, set it before the Python process imports PARL; changing it after `import parl` does not rebuild aliases.
- If Torch warns about NumPy 2.x compatibility, use a Torch build that supports the installed NumPy or pin NumPy to a 1.x version compatible with the framework.
- If Paddle or Fluid imports fail, do not borrow the verified Torch result as proof; rerun with the target backend.
- If Waymax-RL or EvoKit prerequisites are missing, keep the workflow in planning/config-validation mode until the hard GPU/native dependencies are available.
