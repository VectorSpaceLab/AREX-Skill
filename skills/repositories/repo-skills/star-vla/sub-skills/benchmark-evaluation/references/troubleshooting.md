# Benchmark evaluation troubleshooting

Use this page to triage simulation benchmark planning and evaluation failures without conflating policy serving, simulator installation, and checkpoint/data issues.

## Quick triage order

1. **Scope:** Is the user asking for planning, a safe dry run, or an actual simulator run?
2. **Process split:** Is the policy server running separately from the simulator client?
3. **Port:** Do server and client use the same host/port, and is the port listening?
4. **Checkpoint:** Does the server receive an actual checkpoint file, and does it finish loading?
5. **Metadata:** Does the client receive `action_chunk_size` and, when relevant, `available_unnorm_keys`?
6. **Response contract:** Does the client consume `response["data"]["actions"]`? If it expects `normalized_actions`, route to policy deployment.
7. **Unnormalization key:** Does `unnorm_key` match the checkpoint's benchmark/embodiment statistics?
8. **Observation/action cadence:** Do image order, state inclusion, action dimension, chunk size, and replanning interval match the training recipe?
9. **Simulator assets/rendering:** Are benchmark assets, datasets, MuJoCo/OpenGL/Vulkan, and third-party patches prepared?
10. **Metric artifacts:** Did outputs land in the expected result/log/video directory?

## Missing simulator environment

Symptoms:

- Client import errors for benchmark packages.
- Scripts ask for a simulator project root or asset/data root.
- Policy server starts, but evaluation never begins.

Actions:

- Do not install or clone large simulators unless explicitly asked.
- Record the missing simulator family and required external assets.
- Plan a single-task manual debug before full benchmark scheduling.
- If only the policy server fails, route to `../policy-deployment/SKILL.md`; if only the simulator imports fail, keep triage here.

## Vulkan, MuJoCo, OpenGL, and renderer errors

Symptoms:

- `libvulkan.so.1` missing.
- MuJoCo cannot create a GL context.
- `libGL.so.1` import errors.
- BEHAVIOR segmentation faults or low-resolution rendering on unsuitable devices.

Actions:

- Treat these as simulator-side issues unless the policy server also fails.
- For MuJoCo-style headless runs, confirm the intended OpenGL backend before launching.
- For SimplerEnv/ManiSkill and BEHAVIOR/OmniGibson, verify Vulkan and graphics driver installation in the simulator environment.
- For BEHAVIOR, avoid planning evaluation on devices lacking simulator-required ray-tracing support.
- Do not modify model code to fix renderer import errors.

## Server not listening or client connection refused

Symptoms:

- Client times out before first action.
- Scheduler waits until server timeout.
- Connection refused on localhost/port.

Actions:

- Confirm the server process was started first and has finished checkpoint loading.
- Check port collision and whether the client is connecting to the same host/port.
- Increase server-start timeout only when checkpoint loading is legitimately slow.
- If the server process exits, inspect server logs for checkpoint/config/model errors and route protocol/server internals to `../policy-deployment/SKILL.md`.

## Wrong checkpoint path

Symptoms:

- Server cannot find checkpoint or loads a different model than expected.
- Client output directory uses a different checkpoint name than the served model.
- Result folders are created but no valid actions are produced.

Actions:

- Keep checkpoint path, run directory, base model id, and result directory separate.
- Use the same checkpoint placeholder in server and client plan unless the client only needs it for naming.
- For released checkpoints, confirm whether the path points to the model file expected by the server rather than a repository root.
- If a benchmark launcher hardcodes a checkpoint path, replace it with an explicit placeholder before any run.

## Stale client-side unnormalization docs or code

Symptoms:

- Client looks for `normalized_actions`.
- Client reads `dataset_statistics.json` and performs its own unnormalization.
- Source docs show `result["normalized_actions"]`.

Actions:

- Current StarVLA server-side contract returns unnormalized `actions`.
- Clients should pass `unnorm_key` and read `action_chunk_size` from server metadata.
- Updated LIBERO, SimplerEnv, VLA-Arena, RoboCasa, RoboTwin, and DOMINO adapters follow this pattern.
- BEHAVIOR source code may still contain stale client-side unnormalization logic; treat it as experimental until reconciled.
- Route response-schema or server metadata failures to `../policy-deployment/SKILL.md`.

## Wrong `unnorm_key`

Symptoms:

- Actions are finite but task behavior is nonsensical.
- Multi-dataset checkpoint works for one benchmark but fails another.
- Server complains about missing statistics key.

Actions:

- Query or record `available_unnorm_keys` from server metadata.
- Match key to benchmark embodiment/dataset mixture, not just model family.
- Common key families seen in source examples include Bridge/RT-1 OXE variants, RoboCasa GR1, RoboTwin/DOMINO new embodiment, Franka/Calvin, BEHAVIOR R1Pro, and RoboDojo ARX X5.
- If only one key exists, still write it into the run plan for reproducibility.

## Action chunk mismatch

Symptoms:

- Policy repeats actions too long or replans too often.
- Simulator executes a small prefix while server predicts a longer chunk.
- Actions look delayed, jerky, or stale without crashing.

Actions:

- Treat server metadata `action_chunk_size` as authoritative for predicted chunk length.
- Separately record simulator `n_action_steps`, control frequency, and replanning interval.
- For RoboDojo released evaluation, distinguish 50 predicted actions from 16 executed actions before replanning.
- For RoboCasa tabletop, verify `n_action_steps` and named action-group slicing.
- For LIBERO/VLA-Arena/RoboTwin/DOMINO, check whether the adapter caches chunks by step modulo `action_chunk_size`.

## State, image, and camera mismatches

Symptoms:

- Evaluation runs but success is unexpectedly poor.
- No explicit exception despite wrong behavior.
- Model family expects state but client omits it, or vice versa.

Actions:

- Confirm camera count, image order, resize/crop, language key, state dimension/order, and action dimension against the checkpoint training recipe.
- RoboCasa tabletop: use the state toggle intentionally. QwenOFT tabletop checkpoint should omit state; GR00T uses state.
- DOMINO: optional history payloads are not automatically useful unless the policy was trained to consume them.
- BEHAVIOR: verify 23D action grouping if adapting the client.

## External downloads and assets

Symptoms:

- Data-preparation script wants to download datasets/checkpoints/assets.
- Simulator complains about missing kitchens, textures, task JSONL, overlays, or validation data.

Actions:

- Do not trigger downloads by default.
- Identify which artifact is missing: checkpoint, training data, evaluation dataset, simulator assets, task list, or overlay image.
- For LIBERO, VLA-Arena, RoboCasa, Calvin, and RoboDojo, data assets have distinct training/evaluation roles. Keep them separate in the plan.
- If the task is only evaluation planning, provide placeholders and skip acquisition.

## Benchmark-specific high-risk issues

- **LIBERO:** released Qwen3 PI checkpoint with historical LayerwiseFM semantics requires a runtime compatibility override; do not edit checkpoint config.
- **SimplerEnv:** Vulkan/MuJoCo failures are usually simulator rendering issues. Verify a minimal simulator environment before model debugging.
- **RoboCasa tabletop:** `send_state` and `unnorm_key` are common silent-failure knobs.
- **RoboCasa 365:** official protocol and short walk-through settings differ; do not overclaim benchmark reproduction from a smoke run.
- **RoboTwin:** external benchmark code may need a patch to accept and forward checkpoint paths.
- **DOMINO:** dynamic metrics include penalties and manipulation score; success rate alone is incomplete.
- **BEHAVIOR:** source docs are under construction and simulator hardware constraints are strict.
- **VLA-Arena:** parallel launcher starts multiple servers and eval clients; use single-suite debugging first.
- **Calvin:** training data format and evaluation data format differ.
- **RoboDojo:** evaluation is delegated to the companion adapter stack; do not treat it as the generic websocket flow.

## When to stop and route elsewhere

Stop benchmark triage and route to the appropriate sub-skill when:

- The problem is a websocket/ZMQ schema, server metadata, server normalization, or policy-server CLI issue: `../policy-deployment/SKILL.md`.
- The problem is checkpoint creation, training YAML, config overrides, or distributed launch: `../training-config/SKILL.md`.
- The problem is LeRobot modality, data registry, data mixture, statistics, or custom benchmark dataset integration: `../data-integration/SKILL.md`.
