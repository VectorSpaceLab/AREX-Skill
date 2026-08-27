# WebUI Server and REST API

Use this reference to operate the unified SimpleTuner server and script training through the HTTP API. Confirm with the user before launching, stopping, or autostarting training.

## Server launch patterns

- Start the unified WebUI/API server with `simpletuner server --host <host> --port <port>`.
- Default API/Web routes are served from the same process. The server prints API and Web URLs at startup.
- Use `--ssl` for TLS. If no key/cert pair is supplied, SimpleTuner can generate a self-signed certificate; browsers will warn on self-signed certificates.
- Use explicit `--ssl-key <key-file>` and `--ssl-cert <cert-file>` when a production certificate already exists.
- Use `--ssl-no-verify` only for development/testing with self-signed upstreams.
- `--env <config-name>` validates the named environment at startup and autostarts training after the server is ready. Treat this as an actual training launch.
- Server modes are `unified`, `trainer`, and `callback`. Use `unified` for ordinary WebUI/API operation unless an architecture explicitly separates trainer and callback roles.
- Bind to a loopback address behind a reverse proxy when exposing the service publicly; otherwise restrict firewall access carefully.

## WebUI operating flow

1. Open the WebUI URL served by the server.
2. On first launch, create the first admin account before any shared use.
3. Complete onboarding by selecting configuration and dataset roots, then choose GPU settings.
4. Create or discover training environments. Existing CLI-style config environments can be discovered when their parent config directory is selected.
5. Use the wizard for a first model-family setup. It pre-enables required options for model variants and can configure LoRA/quantization, full-rank memory options, checkpoint cadence, validation prompts, publishing, logging, and dataset wizard basics.
6. For multi-GPU training, check that the dataset can cover `train_batch_size * num_gpus * gradient_accumulation_steps`. If not, reduce batch size, increase repeats, or explicitly enable dataset oversubscription where appropriate.
7. Browser dataset upload is available for local backends. Use it for files or ZIPs that belong on the server machine; confirm size limits and reverse-proxy body-size limits first.

## REST API discovery

- `GET /docs` opens Swagger UI.
- `GET /redoc` opens ReDoc.
- `GET /openapi.json` downloads the OpenAPI schema.
- Use the schema to confirm exact request/response shapes when writing automation.

## Common API training workflow

1. `POST /api/configs/environments` to create an environment.
2. Populate the generated dataloader file or upload one through the UI/API.
3. `PUT /api/configs/{name}` to update hyperparameters.
4. `POST /api/configs/{name}/activate` to set the active environment.
5. `POST /api/training/validate` with form data before launch.
6. `POST /api/training/start` with equivalent form data to launch.
7. Monitor through `GET /api/training/status`, `GET /api/training/events?since_index=N`, or the events stream.
8. Stop/cancel only with explicit user approval: `POST /api/training/stop` or `POST /api/training/cancel` with the active job identifier.

Training validation/start endpoints consume form-encoded fields such as `__active_tab__=model` and CLI-style option names. A saved active environment can be launched with a small form payload; one-off runs can submit a full CLI-style payload.

## Monitoring and runtime triggers

- `GET /api/training/status` reports coarse state, active job ID, and startup stage information.
- `GET /api/training/events?since_index=N` fetches incremental event/log records.
- `/api/training/events/stream` provides a real-time stream for dashboards.
- `POST /api/training/validation/run` asks the active trainer to run validation at the next safe synchronization point; it fails if no job is active.
- `POST /api/training/checkpoint/run` asks the active trainer to save a checkpoint at the next safe synchronization point; it fails if no job is active.
- `POST /api/training/checkpoints` lists checkpoints for the active job output directory.
- `GET /api/system/status?include_allocation=true` includes metrics and GPU allocation state.

## Webhooks and external hooks

- Training form fields may include a JSON-serialized `webhook_config` and `webhook_reporting_interval` to push lifecycle and log events to a callback URL.
- Raw webhook receivers can consume lifecycle, status, notification, error, checkpoint, validation image, and validation video events.
- For reverse-proxy deployments, webhook callback URLs and event streams must use the externally reachable public endpoint, not an internal-only server address.
- External validation, post-checkpoint, and post-upload scripts are training configuration options. They receive placeholders such as checkpoint path, global step, tracker names, model family, and publishing destination. They are not executed by this sub-skill unless the user explicitly asks to run training.

## Reverse proxy notes

- For Server-Sent Events, disable response buffering and allow long read timeouts on the stream route.
- For browser dataset uploads, raise request body limits high enough for intended datasets.
- Terminate TLS at the proxy or pass TLS through to the server; do not expose unauthenticated HTTP on an untrusted network.

## Safe planning helper

Use `scripts/build_api_training_plan.py` from this sub-skill to print reviewable curl skeletons for the API sequence. The helper never opens sockets and is suitable for planning before a user approves the actual API calls.
