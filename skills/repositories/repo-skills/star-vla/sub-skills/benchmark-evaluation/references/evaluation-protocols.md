# StarVLA benchmark evaluation protocols

This reference describes the safe planning pattern for StarVLA simulation benchmarks. It intentionally avoids executable launcher commands because benchmark launchers can start servers, simulators, downloads, GPU jobs, or third-party bootstrap steps.

## Two-environment flow

Most simulation evaluations use two independent runtime roles:

1. **Policy-server terminal**
   - Runs from a StarVLA installation with model dependencies and the checkpoint available.
   - Starts the websocket policy server with checkpoint, port, device selection, and optional precision/config overrides.
   - Emits server metadata such as `action_chunk_size` and `available_unnorm_keys`.
   - Returns already unnormalized `actions` when the current server contract is used.

2. **Simulator-client terminal**
   - Runs from the benchmark simulator installation with benchmark assets/data available.
   - Connects to the policy server host/port.
   - Converts simulator observations into StarVLA examples (`image`, `lang`, optional `state`, optional history payloads).
   - Passes `unnorm_key` for multi-stat checkpoints.
   - Applies action chunks according to benchmark-specific control cadence.
   - Writes videos, logs, JSON/CSV summaries, or benchmark-native metrics.

Use the same host/port pair in both terminals. Confirm the server is listening before starting the simulator; otherwise client errors will look like simulator failures.

## Path and placeholder roles

Keep these placeholders distinct:

| Placeholder | Role | Common mistakes |
| --- | --- | --- |
| `CHECKPOINT_PATH` | File loaded by the policy server. Often also used by client launchers for naming result folders or finding metadata. | Pointing to a run directory instead of a checkpoint file; serving one checkpoint while the client names/results another. |
| `MODEL_OR_BASE_VLM` | Model family or released checkpoint identifier used during planning/training. | Treating a model-zoo identifier as a local checkpoint file. |
| `BENCHMARK_ROOT` | External simulator source/project location. | Assuming StarVLA contains the full simulator. |
| `DATA_ROOT` / `ASSET_ROOT` | Benchmark datasets, textures, task files, or converted demonstrations. | Using training LeRobot data where evaluation expects original simulator data. |
| `OUTPUT_DIR` | Videos, logs, metrics, per-task JSON/CSV, or benchmark-native output. | Letting parallel launchers write into checkpoint directories unintentionally. |
| `UNNORM_KEY` | Statistics key selected for server-side action unnormalization. | Leaving it unset for multi-dataset checkpoints or choosing a key from the wrong embodiment. |
| `PORT` | Policy server port used by both terminals. | Reusing a busy port or mismatching server/client ports. |
| `TASK_OR_SUITE` | Benchmark task name, task list, suite, difficulty level, or mode. | Running full benchmark when intending a single smoke task. |

## Current websocket action contract

Current StarVLA policy serving centralizes action unnormalization on the server side:

- Client request contains `examples` and should include `unnorm_key` when needed.
- Client should fetch metadata through the websocket client handshake.
- Server response data should contain `actions`, already unnormalized and ready for simulator adaptation.
- Clients should read `action_chunk_size` from server metadata. Do not infer it from old config field names.

If a client still expects `normalized_actions` or manually reads `dataset_statistics.json`, suspect stale adapter code or stale docs. Before rewriting benchmark logic, route the protocol mismatch to `../policy-deployment/SKILL.md`.

## Client-side adapter responsibilities

A `model2*_interface.py` style adapter should do only benchmark-specific conversion:

- Resize/crop images to the size used by the checkpoint recipe.
- Preserve camera count and ordering from training.
- Package language instructions under the expected key.
- Include or omit state according to the checkpoint recipe.
- Add optional history payloads only if the policy was trained to consume them.
- Forward `unnorm_key` instead of unnormalizing locally.
- Cache or ensemble returned chunks according to the benchmark control cadence.
- Convert the flat or chunked StarVLA action into simulator-specific action fields.

Silent behavior degradation is common when image order, state inclusion, action dimension, or replanning cadence differs from training even though all processes run without exceptions.

## Benchmark protocol patterns

### Single-task manual debug

Use for initial troubleshooting.

1. Prepare one checkpoint and one task/suite.
2. Start one policy server on one port.
3. Confirm the port listens and metadata contains expected keys.
4. Start one simulator client using that host/port.
5. Save logs and a small video/result artifact.
6. If observation schema or server response fails, route to policy deployment.

### Full benchmark scheduler

Use only after manual debug succeeds.

1. Expand task list (`all`, task-list file, suite list, or levels).
2. Decide per-device server/client concurrency.
3. Allocate non-overlapping ports.
4. Set a server-start timeout long enough for checkpoint loading.
5. Stream concise metric lines, but preserve full logs.
6. Clean up server and simulator subprocesses after each slot.

Schedulers for RoboTwin, DOMINO, VLA-Arena, and BEHAVIOR may start many processes. Treat them as expensive/unsafe until explicitly requested.

## `unnorm_key` handling

1. Ask the server for `available_unnorm_keys` if supported.
2. If one key exists, many clients can auto-select it, but record the selected key anyway.
3. If multiple keys exist, choose the key matching the benchmark embodiment/dataset mixture.
4. For OXE/SimplerEnv-style checkpoints, distinguish Bridge and RT-1 statistics.
5. For RoboTwin/DOMINO-style examples, confirm `new_embodiment` or the training registry key is correct.
6. For RoboCasa tabletop, pass a key such as `gr1` if the checkpoint statistics contain multiple embodiments.
7. For RoboDojo released policies, the relevant statistics key is `arx_x5`.
8. Wrong keys often produce plausible but ineffective actions, not immediate crashes.

## `action_chunk_size` and replanning

- Server metadata is authoritative for the predicted action chunk length.
- Simulator clients may execute fewer actions per request than the full predicted chunk; this is benchmark-specific.
- Examples:
  - LIBERO and VLA-Arena adapters cache chunks and index by step modulo `action_chunk_size`.
  - RoboCasa tabletop maps only `n_action_steps` from each returned chunk into named action groups.
  - RoboDojo released evaluation predicts 50 actions but replans after executing 16.
  - BEHAVIOR source code currently hardcodes a short action chunk in its experimental client; treat mismatches as adapter-level hazards.
- If control feels delayed, jerky, or repeats stale actions, check chunk/replanning before assuming model quality issues.

## Results and metrics expectations

| Benchmark | Result artifacts |
| --- | --- |
| LIBERO | success rates over task suites; per-run videos. |
| SimplerEnv | per-task logs and videos under checkpoint-derived output folders. |
| RoboCasa tabletop | task success rates and videos from simulator arguments. |
| RoboCasa 365 | per-task JSON summary beside checkpoint plus videos in a result directory. |
| RoboTwin | streamed success-rate lines plus per-task server/eval logs. |
| DOMINO | Success Rate, Manipulation Score, route completion, penalty counts, and logs. |
| BEHAVIOR | task videos and challenge/task success signals; exact reporting may change because source docs are under construction. |
| VLA-Arena | CSV summary, logs, success rate, and constraint cost for safety suites. |
| Calvin | average sequence length and chained subtask success. |
| RoboDojo | success rate and score over the released task protocol. |

## Compatibility and stale-doc hazards

- `examples/eval_protocol.md` contains an older minimal pseudo-code snippet reading `normalized_actions`. Current server docs and updated benchmark adapters use `actions` instead.
- LIBERO released Qwen3 PI checkpoint compatibility requires a runtime override for historical LayerwiseFM semantics. Do not edit checkpoint config for that case.
- Some benchmark READMEs list environment names or executable paths as examples. Treat them as placeholders; do not bake local names into reusable plans.
- BEHAVIOR is explicitly under construction and may not match the current policy-server response contract.

## Evidence notes

Distilled from source evidence in `examples/eval_protocol.md`, `deployment/model_server/README.md`, benchmark README files, representative `run_policy_server.sh` / `start_eval.sh` / `eval_*.sh` launchers, `model2*_interface.py` adapters, and the RoboCasa tabletop interface test. These are evidence notes only; this runtime skill does not link to or require the original checkout.
