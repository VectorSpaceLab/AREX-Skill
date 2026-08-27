# AXLearn Troubleshooting

## Purpose

Read this when installation, import, config activation, or optional backend checks fail before you dive into a sub-skill.

## Common failures

### `pip check` reports a TensorFlow / NumPy mismatch

**Symptom:** `tensorflow 2.19.1 has requirement numpy<2.2.0,>=1.26.0` or a similar resolver conflict.

**Cause:** The environment pulled a newer NumPy than the TensorFlow wheel expects.

**Recovery:** Pin NumPy back to the TensorFlow-compatible range and rerun `python -m pip check`.

### `axlearn` imports, but some optional modules fail

**Symptom:** `tensorflow_io is not installed`, `tokamax` import errors, or `ModuleNotFoundError` for cloud extras.

**Cause:** AXLearn exposes many optional workflows. The base install is not enough for every sub-skill.

**Recovery:** Install the extra required by the route you want:

- `audio` for ASR workflows.
- `gcp` for cloud CLI workflows.
- Any repo-specific optional dependency named in the sub-skill reference.

If a GPT catalog fails because of `tokamax`/`qwix`, see the language-model sub-skill.

### `axlearn gcp ...` says no project has been activated

**Symptom:** Warnings such as `No GCP project has been activated; please run axlearn gcp config activate.`

**Cause:** The CLI reads project settings from `.axlearn/axlearn.default.config` and `.axlearn/.axlearn.config`.

**Recovery:** Run `axlearn gcp config list`, then `axlearn gcp config activate` after creating or copying the repo config file.

### GCP auth or kube access failures

**Symptom:** Messages asking for `axlearn gcp auth`, `gcloud auth login`, or `gke-gcloud-auth-plugin`.

**Cause:** Cloud launch commands depend on Google Cloud credentials and, for some paths, Kubernetes auth.

**Recovery:** Authenticate with `axlearn gcp auth` and follow the CLI help for the specific command.

### Fake-data workflows fail unexpectedly

**Symptom:** A tutorial or trainer config fails even though `DATA_DIR=FAKE` was set.

**Cause:** The command may still be pulling a real-dataset code path, or the config name is not a fake-data variant.

**Recovery:** Use the sub-skill-specific fake-data command or probe and confirm the named config first.

## When to stop

Stop and collect more evidence if the failure needs:

- Cloud credentials or project-specific config.
- A TPU/GPU backend that is not available on the current host.
- Large datasets, downloads, or long training runs.
- A dependency combination that cannot be imported without changing the environment.
