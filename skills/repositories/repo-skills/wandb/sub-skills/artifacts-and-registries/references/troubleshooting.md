# Artifact and Registry Troubleshooting

## Invalid artifact names

Symptoms:

- `ValueError` mentioning invalid artifact name characters.
- CLI upload fails after parsing the artifact path.

Checks and fixes:

- Artifact names may contain letters, numbers, underscores, hyphens, and dots.
- Do not include `/` inside the artifact name; use `entity/project/name:alias` only when referring to an artifact path.
- Keep the artifact name at or below 128 characters.
- Avoid embedding local filesystem paths or URL-like strings in artifact names; put that detail in metadata when safe.

## Invalid artifact types

Symptoms:

- `ValueError` for artifact type validation.
- Registry rejects a linked artifact because the type is not allowed.

Checks and fixes:

- Types must not contain `/` or `:` and must be at or below 128 characters.
- Do not use reserved types such as `job` or types starting with `wandb-`.
- If linking to a registry restricted to specific types, log the artifact with one of the allowed types.
- For model registry flows, use a type such as `model` or a type string that includes `model` when that convention is required by the workflow.

## File or directory does not exist

Symptoms:

- `Path is not a file` from `Artifact.add_file()`.
- `Path is not a directory` from `Artifact.add_dir()`.
- `Path argument must be a file or directory` from `wandb artifact put`.

Checks and fixes:

- Validate files before constructing the artifact; W&B checks paths when adding entries, not only when logging.
- Use `add_reference("file://...")` for externally mounted local references that should not be uploaded.
- For generated model checkpoints, call the framework save function and flush/close the file before `add_file()`.
- When using `policy="immutable"`, do not mutate or delete files while upload is in progress.

## Finalized artifact mutation errors

Symptoms:

- `ArtifactFinalizedError` or a message that the current artifact version cannot be changed.
- Mutation methods fail after `run.log_artifact()` or `artifact.wait()`.

Checks and fixes:

- Add all files, directories, references, metadata, aliases, and tags before logging when possible.
- To change contents after logging, create a new artifact version rather than mutating the finalized object.
- For draft updates based on an existing artifact, use the SDK's draft/versioning pattern rather than editing a committed artifact in place.

## Alias and version confusion

Symptoms:

- The wrong artifact version is downloaded.
- `latest` resolves differently than expected.
- CLI `get` without `:alias` downloads an unexpected artifact.

Checks and fixes:

- Use explicit versions such as `:v0` for immutable reproducibility.
- Use aliases such as `:latest`, `:prod`, or `:candidate` only when following a moving channel is intended.
- Remember that aliases cannot contain `/` or `:`.
- When an alias is reused in a registry collection, it refers to the linked collection version, not necessarily the original source project context.
- Expand ambiguous names to `entity/project/name:alias` before debugging type or credential issues.

## Download requires credentials or remote access

Symptoms:

- `wandb artifact get` cannot find or download a known artifact.
- `wandb.Api().artifact(...).download()` fails in automation.
- Public API calls work locally but fail in CI.

Checks and fixes:

- Authenticate with `wandb login` or `WANDB_API_KEY` before remote artifact or registry operations.
- Set `WANDB_BASE_URL` or use `wandb login --host ...` for self-hosted instances.
- Confirm the entity/project path is explicit and the account has access.
- `Artifact.download()` cannot download an artifact that has not been logged; wait for logging to finish first.
- Existing files in the download root are not overwritten; remove the root directory when exact contents are required.

## Optional storage dependency failures

Symptoms:

- S3 references mention missing `boto3` or `botocore`.
- GCS references mention missing `google-cloud-storage`.
- Azure blob references fail while loading Azure modules or credentials.

Checks and fixes:

- Install `wandb[aws]` for `s3://` reference metadata/download support.
- Install `wandb[gcp]` for `gs://` reference metadata/download support.
- Install Azure blob storage and identity packages when using Azure blob HTTPS references.
- Use `checksum=False` only when metadata inspection is too slow or unsupported and the weaker integrity behavior is acceptable.
- Cloud object-store credentials are separate from W&B credentials; validate both.

## Registry path and link errors

Symptoms:

- `Run.link_artifact()` or `Artifact.link()` fails to resolve a collection.
- Linked artifact appears under the wrong entity/project.
- Offline run raises `NotImplementedError` for linking.

Checks and fixes:

- Registry collection target paths use the registry project prefix: `wandb-registry-{registry-name}/{collection-name}`.
- Use `org-entity/wandb-registry-{registry-name}/{collection-name}` when the default entity is ambiguous.
- Source artifacts must be logged before they can be linked; call `logged.wait()` before linking in scripts that immediately chain operations.
- Registry linking requires online mode, authentication, permissions, and server support; it is not implemented for offline runs.
- Registry creation/search methods can raise runtime errors on older servers that do not support the needed registry APIs.
- `Api.create_registry(name="model", ...)` takes the registry name without `wandb-registry-`; link target paths include the prefix.

## Registry artifact type restrictions

Symptoms:

- Linking fails even though the artifact path is valid.
- Registry save fails after editing `artifact_types`.

Checks and fixes:

- If a registry was created with `artifact_types=[...]`, only those types are allowed.
- Previously saved allowed artifact types cannot be removed later.
- If `allow_all_artifact_types` is `True`, save can reject newly added restricted types until it is set to `False`.
- Validate planned artifact types before logging production model artifacts.

## CLI path mixing mistakes

Symptoms:

- `wandb artifact get` says it is unable to download.
- `wandb artifact ls` works for a project but `get` does not.
- A registry artifact path works in Python but not in shell scripts.

Checks and fixes:

- For `ls`, pass `entity/project`; for `get`, pass `entity/project/artifact:alias` or `entity/project/artifact:vN`.
- Do not pass a collection-only registry path to `get`; include the artifact collection name and alias/version.
- Quote shell paths containing `:` or glob-like characters in CI scripts.
- Confirm `--type` matches the remote artifact; remove it temporarily while isolating path vs. type failures.
