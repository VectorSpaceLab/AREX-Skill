# cli-cloud troubleshooting

## Purpose

Read this when `axlearn gcp` fails because of config, credentials, cloud tools, or log-view dependencies.

## Common failures

### `No GCP project has been activated`

**Likely cause:** The CLI could not find an active entry in the GCP config namespace.

**Recovery:**

1. Run `axlearn gcp config list` to see the available entries.
2. Activate one with `axlearn gcp config activate --label=...`.
3. If needed, copy the repo default config into `.axlearn/.axlearn.config` first.

### `Please run axlearn gcp auth`

**Likely cause:** Google Cloud credentials are missing or expired.

**Recovery:** Run `axlearn gcp auth` and follow the browser / ADC prompts.

### `gke-gcloud-auth-plugin` or kube-config errors

**Likely cause:** GKE credentials were not initialized for the selected cluster.

**Recovery:** Authenticate with `gcloud`, then use the cloud CLI's config activation path again. If the error mentions `gke-gcloud-auth-plugin`, install that plugin before retrying.

### `Required to view logs: pip install google-cloud-logging`

**Likely cause:** The logs subcommand is available, but the optional Cloud Logging dependency is missing.

**Recovery:** Install the missing logging dependency or use a different path to inspect job output.

### `tensorflow_io is not installed`

**Likely cause:** A bundler or remote-storage path expects `tensorflow-io` to be present.

**Recovery:** Install the missing optional dependency only for the workflow that needs it. If the task does not use `s3://` or other tf.io-backed paths, this warning may be harmless.

### Bundle or Dataflow commands ask for Docker/GCloud support

**Likely cause:** The selected bundler type requires external cloud tooling.

**Recovery:** Make sure `gcloud` is installed, authenticated, and configured for the target project; verify Docker is installed for Docker-based bundlers.

## Recovery order

1. Check the active config first.
2. Check GCP auth second.
3. Check the command's optional dependency requirements third.
4. Only after that debug project-specific TPU/GKE/Dataflow settings.
