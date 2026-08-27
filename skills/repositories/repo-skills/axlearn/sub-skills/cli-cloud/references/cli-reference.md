# cli-cloud reference

## Purpose

Read this when you need AXLearn's GCP command tree, config-file layout, or bundler/launcher flag patterns.

## Verified command-tree facts

The installed package exposes these GCP subcommands under `axlearn gcp`:

- `config`
- `sshvm`
- `sshtpu`
- `bundle`
- `launch`
- `vm`
- `bastion`
- `dataflow`
- `logs`
- `auth`

The root CLI only registers the GCP branch when the optional GCP extras are installed.

## Config-file behavior

The GCP config namespace uses:

- `.axlearn/axlearn.default.config` for the repo default config.
- `.axlearn/.axlearn.config` for the user-local override.
- `~/.axlearn.config` as the home-directory fallback.

Useful functions inspected from the installed package:

- `axlearn.cloud.common.config.load_configs(namespace, required=False)`
- `axlearn.cloud.gcp.config.gcp_settings(key, fv=..., default=None, required=True)`
- `axlearn.cloud.gcp.config.default_project()`
- `axlearn.cloud.gcp.config.default_zone()`
- `axlearn.cloud.gcp.config.default_env_id()`

## Bundling and launch types

Bundler types exposed by the installed package:

- `gcs`
- `artifactregistry`
- `cloudbuild`

Important runtime facts:

- `bundle` can package the local checkout and optional external paths.
- `launch` can submit jobs locally or via bastion, depending on the selected runner.
- `vm` creates a VM and runs a command on it.
- `bastion` manages Bastion job history and quota-backed orchestration.
- `dataflow` wraps local or remote Dataflow execution.
- `logs` reads Cloud Logging entries.
- `auth` performs the GCP login / application-default-login flow.

## Useful command patterns

### List and activate configs

```bash
axlearn gcp config list
axlearn gcp config activate --label=my-label
```

### Bundle the checkout

```bash
axlearn gcp bundle --bundler_type=artifactregistry --name=my-tag \
  --bundler_spec=image=my-image --bundler_spec=repo=my-repo \
  --bundler_spec=dockerfile=Dockerfile
```

### Launch a command

```bash
axlearn gcp launch --instance_type=tpu-v4-8 -- python3 -c "print('hello')"
```

## When to read more

- For command-specific failure modes, see `references/troubleshooting.md`.
- For trainer/model specifics, route to the owning domain sub-skill instead of expanding this reference.
