# CLI, Backend, Scanner, and GUI Troubleshooting

## Backend not running or wrong URL

Symptoms: connection refused, server unavailable, list commands fail.

Recovery: verify `--server-url`, start a local backend only when authorized, and confirm the same config/database is used by backend and client.

## Port conflict or startup timeout

Symptoms: backend does not bind, startup timeout expires, another process owns the port.

Recovery: choose another port, stop only owned local backends, increase `--startup-timeout` for slow initialization, and inspect logs for config/initializer failures.

## Invalid config file

Symptoms: YAML parse errors, missing database settings, initializer import failures, or CLI args not matching config values.

Recovery: validate the config syntax; route config semantics to `setup-memory-core`; remember that CLI flags can override config values.

## No registered target or missing credentials

Symptoms: scenario run fails because target name is unknown or target sends fail with auth errors.

Recovery: list targets/initializers; load the initializer that registers the target; route target setup and secrets to `targets-scorers`.

## Bad scenario, technique, or dataset filter

Symptoms: scenario/technique name rejected, dataset filters produce no objectives, or run completes with no attacks.

Recovery: list scenarios and datasets; check available technique names/tags; use a small `--max-dataset-size`; route semantics to `attacks-scenarios` and dataset details to `converters-datasets`.

## GUI/backend split confusion

Symptoms: GUI loads but actions fail, or backend responds but browser UI is unavailable.

Recovery: distinguish the Python API from the frontend client. Verify backend health and route/API behavior first; handle frontend deployment/browser issues separately.

## Container caveats

Symptoms: Docker cannot reach host services, volumes hide config files, credentials missing in container, or image build is slow.

Recovery: ask before container operations; pass config/secrets at runtime; map ports explicitly; avoid baking secrets into images.
