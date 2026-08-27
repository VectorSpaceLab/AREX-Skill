---
name: policy-deployment
description: "Serve StarVLA checkpoints over websocket or GR00T-compatible ZMQ
  and debug policy client contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# policy-deployment

Use this operating sub-skill after a StarVLA checkpoint exists and the task is to serve it, connect a policy client, debug request/response schemas, or bridge the policy to a robot/controller stack. The current StarVLA serving path performs **server-side action unnormalization**: clients should consume `response["data"]["actions"]`, not reimplement old `normalized_actions` handling.

## Route first

- Websocket or ZMQ server protocol, server metadata, `PolicyServerWrapper`, `PolicyNormProcessor`, `server_policy.py`, `server_policy_gr00t_zmq.py`, `ZmqGr00tPolicyServer`, `Gr00tCompatPolicy`: read [policy-server-protocols](references/policy-server-protocols.md).
- Websocket client request/response schemas, image/state shape checks, GR00T named state/action split, optional helper validation: read [client-contracts](references/client-contracts.md) and use [check_policy_server_contract.py](scripts/check_policy_server_contract.py).
- Real-robot or controller bridge design, safety gates, GR00T-WBC/Unitree G1/EgoVLA/RoboChallenge/Franka caveats: read [real-robot-bridges](references/real-robot-bridges.md).
- Failure diagnosis for checkpoint config/statistics, multiple unnormalization keys, request shape mismatch, stale normalized-action clients, codec mismatch, port/timeouts, or device/bfloat16 mistakes: read [troubleshooting](references/troubleshooting.md).

Route elsewhere when the question is not serving/client deployment:

- Simulator environment installation, benchmark-specific eval launchers, MuJoCo/Vulkan/rendering, or benchmark metrics -> `../benchmark-evaluation/SKILL.md`.
- Dataset registry, `data_mix`, `DataConfig`, modality/statistics key construction, or `dataset_statistics.json` generation -> `../data-integration/SKILL.md`.
- Training a checkpoint, YAML training overrides before a checkpoint exists, Accelerate/DeepSpeed, or resume planning -> `../training-config/SKILL.md`.

## Operating invariants

1. Start from server metadata. `action_chunk_size`, `available_unnorm_keys`, `default_unnorm_key`, `training_data_mix`, `training_obs_image_size`, and any exposed `action_keys`/`state_keys` are the authoritative handshake for a served checkpoint.
2. If metadata reports multiple `available_unnorm_keys` and no default, every inference payload must pass a top-level `unnorm_key` matching the requested embodiment/statistics key.
3. Websocket clients send a payload with `examples`; each example carries explicit image views, language, and optional state. The server never infers camera count or camera order.
4. StarVLA websocket responses return already-unnormalized `actions` shaped like `[B, T, action_dim]`. Treat docs or clients expecting `normalized_actions` as stale until migrated.
5. GR00T-compatible ZMQ clients use endpoint messages and the custom ndarray codec. Named state groups are flattened in checkpoint `state_keys` order; flat actions are split into named groups using `action_keys` and key dims.
6. `--config_override KEY=VALUE` is a repeatable OmegaConf dotlist override for the websocket server path. Do not pass a bare string into the Python API; pass a sequence of `KEY=VALUE` entries.
7. Robot bridges own observation capture, controller grouping, clipping, stale-action handling, and safety interlocks. They should not duplicate StarVLA action unnormalization.
