# Async inference and transport services

## Required extras and process model

Async inference is exposed by `lerobot.async_inference.policy_server` and `lerobot.async_inference.robot_client`. Install the `async` extra, which includes the gRPC and matplotlib dependency groups. The service uses Python gRPC and the generated `lerobot.transport.services_pb2` / `services_pb2_grpc` modules. The transport package also supports learner RPC messages, but this reference focuses on async inference.

The server is empty until a client handshake supplies a remote policy description. The client constructs and connects the robot locally; the server loads the policy checkpoint and runs preprocessing, inference, and postprocessing. A real client therefore crosses both a robot/hardware gate and a network/model/credential gate. A config diagnostic crosses neither.

## Wire contract

The `AsyncInference` service declares:

- `Ready(Empty) -> Empty`: handshake/reset. A new client resets the server's one-item observation queue and predicted timestep set.
- `SendPolicyInstructions(PolicySetup) -> Empty`: client sends serialized `RemotePolicyConfig` containing `policy_type`, `pretrained_name_or_path`, mapped LeRobot features, `actions_per_chunk`, `device`, and optional `rename_map`.
- `SendObservations(stream Observation) -> Empty`: client sends serialized `TimedObservation` values as transfer-state chunks.
- `GetActions(Empty) -> Actions`: client requests one serialized action chunk, or receives an empty response when the observation queue times out.

`TimedObservation` carries a wall-clock `timestamp`, integer `timestep`, raw observation mapping, and `must_go`. `TimedAction` carries timestamp, timestep, and a tensor action. The server converts raw robot keys to `observation.state` / image features, applies the policy preprocessor, predicts an action chunk, applies the postprocessor action-by-action, and returns CPU tensors. The client may move actions to `client_device` before queue aggregation and local robot execution.

`services.proto` also declares `LearnerService` (`StreamParameters`, `SendTransitions`, `SendInteractions`, `Ready`) and message types `Transition`, `Parameters`, and `InteractionMessage`. Those are not interchangeable with `Observation` or `Actions`; match the generated stub method and message class exactly.

## Endpoint and timing contract

`PolicyServerConfig` fields are `host` (default `localhost`), `port` (default `8080`), `fps` (default constant), `inference_latency`, and `obs_queue_timeout`. Port must be 1–65535; latency and queue timeout are non-negative; the effective environment step is `1 / fps`. `RobotClientConfig` requires `policy_type`, `pretrained_name_or_path`, a concrete `robot`, and positive `actions_per_chunk`; it defaults to `server_address=localhost:8080`, CPU policy/client devices, weighted-average aggregation, FPS, and a 0–1 `chunk_size_threshold`.

The client sends a new observation when its action queue is at or below the threshold relative to the last received chunk, and marks an empty queue as `must_go`. `actions_per_chunk` must not exceed the model's usable prediction horizon. The registered aggregate names are `weighted_average` (0.3 old + 0.7 new), `latest_only` (new), `average` (0.5/0.5), and `conservative` (0.7 old + 0.3 new). Unknown names raise `ValueError` locally.

Tune `fps`, `actions_per_chunk`, and `chunk_size_threshold` together. A queue that repeatedly empties indicates latency or bandwidth pressure; lowering FPS or increasing the chunk can help, while increasing the threshold sends more overlapping requests and raises inference/bandwidth load. These are performance hypotheses, not safety guarantees.

## Serialization and chunking

`send_bytes_in_chunks()` uses 2 MiB chunks and marks `TRANSFER_BEGIN`, `TRANSFER_MIDDLE`, and `TRANSFER_END`. The generated messages carry `transfer_state` and `data`. `receive_bytes_in_chunks()` reconstructs the buffer, rejects unknown transfer states, and can stop on a shutdown event. gRPC channel options default to 4 MiB send/receive message limits, retries enabled, five attempts, exponential backoff, and retryable `UNAVAILABLE` / `DEADLINE_EXCEEDED` codes. Chunking is necessary for observations larger than one message limit; it does not provide authentication or encryption.

`state_to_bytes()` / `bytes_to_state_dict()` use `torch.save` and `weights_only=True` on load. `transitions_to_bytes()` / `bytes_to_transitions()` use the same tensor-safe load mode. `python_object_to_bytes()` and `bytes_to_python_object()` use pickle and are only suitable for mutually trusted, version-matched peers. Do not feed untrusted network or downloaded content to these helpers.

## Safe mismatch diagnosis

Before launch, compare these values on paper or with the local checker:

1. server bind host and port versus client `host:port` syntax;
2. server and client `fps` / environment step assumptions;
3. policy `type` and checkpoint visibility on the **server**, not just the client;
4. policy input image/state feature keys against the robot's mapped feature keys;
5. `actions_per_chunk`, aggregate name, and device strings;
6. installed `grpcio`/protobuf extra and optional policy dependencies.

A refused connection is endpoint/network state, not a bad pickle. A successful `Ready` followed by setup failure usually indicates policy registration, checkpoint access, optional dependency, device, or serialized feature mismatch. A successful setup followed by empty actions points to queue timeout, observation filtering, shape/preprocessor errors, or server-side inference logs. Never start a daemon solely to distinguish these cases; first use a local config check and the focused service logs if a run already exists.

## Security and launch gate

The reference server binds an insecure gRPC port. It has no credential handshake, TLS, authorization, or payload schema authentication in this layer. Keep it on a trusted/private network, firewall the port, and treat the checkpoint and robot endpoint as sensitive. A port-open test is an actual network operation and requires explicit user approval; it is not performed by the bundled diagnostics. Do not launch the client until the robot is secured, an emergency stop is ready, policy actions are validated offline, and the user explicitly requests actuation.
