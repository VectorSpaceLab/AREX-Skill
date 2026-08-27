# Simulation benchmark readiness

This reference helps choose and prepare a StarVLA simulation benchmark evaluation without running unsafe downloads or simulators. Treat all source benchmark launch scripts as reference-only until the user confirms execution, resources, and external simulator setup.

## Universal readiness checklist

Before planning an actual evaluation, collect:

- Benchmark family, task suite/mode, episode count, seed policy, and desired metric.
- Checkpoint file to serve; model family and whether it needs a compatibility override.
- Policy-server host/port and device allocation.
- `unnorm_key` selected from checkpoint statistics or server metadata. For multi-dataset checkpoints this is required.
- `action_chunk_size` from server metadata and the simulator-side replanning interval or `n_action_steps`.
- Benchmark simulator installation, dataset/assets, and any third-party checkout or project root.
- Result directory expectations: videos, JSON summaries, CSV summaries, per-task logs, or benchmark-native metrics.
- Safety class: planning-only, help-only, mock-only, simulator-required, network/download-required, GPU-required, or third-party patch-required.

Use one StarVLA policy-serving environment and one benchmark simulator environment for actual simulator runs. A single environment is acceptable only for reading configs, running this skill's safe checklist script, or running a local mock/unit test that does not import a simulator.

## Benchmark map

| Benchmark | Simulator-side requirement | Common policy/client knobs | Results/metrics to expect | Caveats |
| --- | --- | --- | --- | --- |
| LIBERO | LIBERO simulator plus MuJoCo dependencies and task suites | checkpoint, host/port, task suite, `unnorm_key`, server metadata `action_chunk_size` | per-suite success over tasks; videos saved under a checkpoint-derived results directory | Some source docs mention client-side stats; current server-side unnormalization should return `actions`. Released Qwen3 PI LIBERO checkpoint needs a LayerwiseFM compatibility override with `USE_CANONICAL_FORWARD=false`. |
| SimplerEnv | SimplerEnv/ManiSkill stack, overlay assets, and rendering backend | checkpoint, host/port, WidowX policy setup, `unnorm_key` such as bridge or RT-1 statistics, task env names | task logs and videos under checkpoint-derived output directories | Vulkan/MuJoCo rendering failures are common; missing `libvulkan.so.1` is a simulator-side issue, not a policy-server issue. |
| RoboCasa tabletop | RoboCasa GR1 tabletop simulator | checkpoint, port, `n_action_steps`, `unnorm_key`, optional state toggle | success rates over tabletop tasks; video output path supplied to client | QwenOFT tabletop checkpoint should omit state; GR00T expects state. If multiple statistics keys exist, pass the correct embodiment key. |
| RoboCasa 365 | Upstream RoboCasa 365 simulator and assets | checkpoint, environment name such as a RoboCasa task id, `n_action_steps`, port | JSON result beside checkpoint and videos in a configured results directory | Training example is a short walk-through; official protocol uses more rollouts and longer horizons. |
| RoboTwin | RoboTwin 2.0 simulator plus a third-party patch so the benchmark can forward checkpoint paths | mode (`demo_clean` or `demo_randomized`), policy/run name, checkpoint, task list, base port, jobs per device, deploy policy fields | streamed per-episode success and per-task server/eval logs under checkpoint-derived log root | Full runs launch many policy-server/client pairs. Patch the external RoboTwin checkout only when user authorizes modifying third-party code. |
| DOMINO | DOMINO dynamic manipulation simulator | dynamic mode, run name, checkpoint, task list, port allocation, optional history settings | Success Rate, Manipulation Score, route completion, penalty counts, per-task logs | History payloads are bridge-level optional; current source notes that some models may ignore `history_images`. |
| BEHAVIOR | BEHAVIOR-1K / OmniGibson assets and renderer | task descriptions, asset path, port, `unnorm_key` commonly for R1Pro-style stats, 23D action contract | per-task videos and challenge-style success signals | Source README is under construction. Avoid GPUs without ray-tracing support for simulator rendering; Vulkan/libGL failures are simulator-side. Some source client code still shows client-side unnormalization and `normalized_actions`; treat that as stale until reconciled with policy deployment. |
| VLA-Arena | VLA-Arena project managed by its own environment tooling | checkpoint, VLA-Arena project path, suite list, levels, output directory, port | CSV summary, logs, success rate, and constraint cost for safety suites | Parallel launcher chooses free devices and starts several servers; dry-run or single-suite planning is safer for debugging. |
| Calvin | Calvin simulator/evaluation dataset in original Calvin format | checkpoint, Calvin dataset validation path, config path, sequences JSON, `unnorm_key` such as Franka statistics | average sequence length and task-chain success metrics | Training uses LeRobot-format Calvin data, but evaluation uses original Calvin format. Do not mix the two path roles. |
| RoboDojo | RoboDojo plus XPolicyLab StarVLA adapter | released policy variant, task, seed, policy/sim devices, environment roots, episode count | success rate and score over released task protocol | StarVLA delegates checkpoint download, verification, serving, simulator startup, and result collection to the companion adapter. Treat this as a third-party integration, not a generic websocket benchmark. |

## Benchmark-specific notes

### LIBERO

- Two terminal roles: StarVLA policy server first, LIBERO evaluation client second.
- Read server metadata for `action_chunk_size`; the LIBERO adapter caches unnormalized chunks and emits 7D Franka-style actions (`world_vector`, `rotation_delta`, `open_gripper`).
- Use MuJoCo/OpenGL rendering variables appropriate for the simulator machine. `egl` is common for headless GPU rendering, but the correct value is simulator-specific.
- For the released Qwen3 PI LIBERO checkpoint trained with historical LayerwiseFM semantics, apply the compatibility override through the launcher environment/CLI rather than editing checkpoint config.
- Network/download scripts for LIBERO datasets are reference-only unless the user asks for data preparation.

### SimplerEnv

- Two terminal roles: StarVLA policy server and SimplerEnv client. The simulator client needs SimplerEnv/ManiSkill assets such as real-to-sim overlays.
- Default client logic chooses an `unnorm_key` from policy setup when one is not provided; confirm this against `available_unnorm_keys` for multi-stat checkpoints.
- Rendering errors such as missing Vulkan library or bad MuJoCo/OpenGL backend should be triaged on the simulator side before touching StarVLA model code.
- Full task lists and output directories are source-launcher details; do not assume they are safe to run automatically.

### RoboCasa tabletop and RoboCasa 365

- Tabletop client batches observations, resizes images to 224x224, can omit state, forwards `unnorm_key`, and maps the returned action chunk into named robot action groups.
- `send_state` matters: source tests prove the tabletop client omits the `state` key when requested and includes a sin/cos state by default.
- Tabletop `n_action_steps` determines how many actions are consumed per server chunk. A mismatch with the checkpoint's action horizon can silently degrade behavior.
- RoboCasa 365 uses upstream RoboCasa task names and writes a small JSON summary per task near the checkpoint plus videos to a result directory.

### RoboTwin and DOMINO

- Both families use scheduler launchers that can start one policy server plus one simulator eval per device slot. They should be treated as full benchmark jobs, not smoke tests.
- Manual mode is safer for debugging: start a single policy server, wait for the port to listen, then run one task in the simulator client.
- The deploy policy config supplies `unnorm_key`, normalization mode, and action mode. Confirm `q99` versus min/max normalization against the checkpoint/training recipe.
- RoboTwin requires external benchmark code to accept a checkpoint path. If the patch is missing, the simulator cannot forward the checkpoint to the StarVLA adapter.
- DOMINO reports both Success Rate and Manipulation Score, including dynamic penalties. Optional temporal history can be encoded as flow or raw frames, but a current policy may ignore extra history payloads.

### BEHAVIOR

- Treat BEHAVIOR as experimental/under-construction. The simulator has strict rendering and asset requirements.
- Source notes warn against GPUs without RT cores for BEHAVIOR evaluation because simulator rendering may segfault or run at low resolution.
- BEHAVIOR action is 23D split into base, torso, left arm/gripper, and right arm/gripper groups.
- If the client expects `normalized_actions`, check whether that adapter is stale relative to the current server-side unnormalization contract before debugging checkpoint quality.

### VLA-Arena

- VLA-Arena evaluation covers multiple suites and levels. Safety suites include constraint cost in addition to success rate.
- The parallel launcher chooses devices, starts several policy servers, then runs suite groups through the external VLA-Arena project. Prefer a single-suite plan before full parallel execution.
- Result summaries are written under the selected output directory; include suite names and levels in the run record.

### Calvin

- Training and evaluation data formats differ. Training recipes use LeRobot-formatted Calvin data; evaluation expects original Calvin format with validation sequences.
- The evaluator needs checkpoint, dataset path, Calvin model config path, and evaluation sequence JSON. Keep these as separate placeholders.
- `unnorm_key` must match the Franka statistics for the checkpoint.

### RoboDojo

- Evaluation is delegated to RoboDojo/XPolicyLab rather than the generic StarVLA websocket wrappers.
- Released policies use three RGB streams, 14D absolute joint state/action, q99 statistics under `arx_x5`, a 50-action horizon, and a 16-action replanning interval.
- The public protocol reports success rate and score across held-out/open tasks; full evaluation includes many episodes and should not be launched as a smoke test.

## Source-script decisions

- Benchmark `run_policy_server.sh`, `start_eval.sh`, `eval_*.sh`, and simulator `simulation_env.py` files are reference-only in this skill because they can load checkpoints, allocate GPUs, start servers, start simulators, patch external repos, or run long evaluations.
- Dataset preparation and download helpers are reference-only because they can trigger network and large-storage side effects.
- `model2*_interface.py` files are distilled into protocol guidance rather than copied because they depend on benchmark imports and simulator observation objects.
- Safe helper retained: `scripts/plan_benchmark_eval.py`, which only prints a checklist.

Evidence notes: facts were distilled from `examples/eval_protocol.md`, benchmark README files under `examples/simBenchmarks/`, representative benchmark launchers/adapters, `deployment/model_server/README.md`, `docs/model_zoo.md`, and `tests/test_robocasa_tabletop_interface.py`. These source paths are evidence notes only, not runtime dependencies.
