# Storage, secrets, ingress, and access-control troubleshooting

Use this reference when a Lepton storage, secret, ingress, mount/env/secret, or endpoint access-control plan fails validation or could mutate workspace state unexpectedly.

## `set-endpoints` would remove endpoints

**Symptom:** a plan uses `lep ingress set-endpoints -n INGRESS -e ...` and the proposed list omits an endpoint that currently exists.

**Likely cause:** `set-endpoints` replaces the complete ingress endpoint list. It is not an incremental weight update.

**Recovery:**

1. Read the current state with an authorized `lep ingress get -n INGRESS`.
2. Include every endpoint that should remain in the repeated `-e ENDPOINT:WEIGHT` list.
3. Prefer `add-endpoint`, `update-endpoint`, or `remove-endpoint` for incremental changes.
4. Run the bundled local checker before presenting the command:

   ```bash
   python scripts/validate_mounts_env.py \
     --existing-endpoint stable:100 \
     --existing-endpoint canary:10 \
     --set-endpoint stable:90 \
     --set-endpoint canary:10
   ```

5. Ask the user to explicitly confirm any omitted endpoint removal before using `--ack-complete-set` in the checker or running the real command.

## Invalid mount string or missing storage name

**Symptoms:** errors such as `expected FROM_PATH:MOUNT_PATH:VOLUME`, `missing storage_name in VOLUME node-nfs`, or `VOLUME must contain exactly one colon after node-<type>`.

**Likely cause:** Lepton mount strings are split on the first two colons and the third part must be a valid volume selector.

**Recovery:**

- Use `FROM_PATH:MOUNT_PATH:node-local` for node-local storage.
- Use `FROM_PATH:MOUNT_PATH:node-nfs:STORAGE_NAME` for a named node NFS volume.
- Validate locally before asking to create/update a workload:

  ```bash
  python scripts/validate_mounts_env.py --mount storage-cache:/cache:node-nfs:my-nfs
  ```

The checker only proves syntax; it does not prove that a storage path or named volume exists.

## `--public` and `--ip-whitelist` conflict

**Symptom:** endpoint access-control planning includes both `--public` and one or more `--ip-whitelist` values.

**Likely cause:** public network access and IP allowlisting are mutually exclusive. Token authentication is independent of IP access.

**Recovery:** choose one network-access mode:

- Public network reachability: `--public`, optionally with `--tokens` when application-level tokens are still required.
- Restricted IP/CIDR reachability: repeated or comma-separated `--ip-whitelist` values, optionally with `--tokens`.
- Private/no explicit public mode: omit both and verify the installed CLI's current default with `lep endpoint create --help` before relying on it.

Do not paste real token values into a plan; use placeholders and count token arguments only.

## Storage upload/download path surprise

**Symptoms:** uploaded file appears under an unexpected remote name, download would overwrite a local path, or `rm`/`rmdir` rejects the target type.

**Likely cause:** storage paths are remote POSIX-like paths, upload treats a remote path ending in `/` as a directory, and `rm` is file-only while `rmdir` is directory-only.

**Recovery:**

1. Read first: `lep storage ls REMOTE_DIR` or `lep storage ls-file-system` when authorized.
2. Confirm whether local and remote paths are safe to display in chat/logs.
3. For uploads, specify the complete remote filename when needed.
4. For downloads, confirm the local destination exists and whether overwrite is acceptable.
5. Do not rely on wildcards for delete; enumerate exact remote paths.

## Secret values or tokens appear in a command plan

**Symptom:** the command or transcript includes a literal secret value, access token, or `workspace_id:token` string.

**Likely cause:** the plan used literal `--env`, `--tokens`, or `lep login -c` values rather than placeholders or user-side entry.

**Recovery:**

- Replace token/secret values with placeholders such as `<redacted-token>` before sharing.
- Prefer `--secret ENV_NAME=SECRET_NAME` over literal secret values in `--env`.
- Use `lep secret list` to find names only after the user authorizes a workspace read.
- If the task is to create or rotate a secret, ask the user to provide the secret through a secure channel or paste it into the CLI locally; do not preserve the value in generated notes.

## Ingress or storage read fails with auth/network error

**Symptoms:** `WorkspaceConfigurationError`, 401/403/404, DNS/socket failures, or timeout on a read-only command.

**Likely cause:** no current workspace, expired or mismatched token, wrong workspace URL, sandboxed network, or transient service issue.

**Recovery:** route to `workspace-and-auth` before retrying resource operations. Keep the resource plan pending until read-only workspace status succeeds. For network sandbox errors, surface the error and ask before retrying with broader network access.

## Delete/remove/rmdir command is requested in auto mode

**Symptom:** user asks for broad deletion such as removing a secret, deleting ingress, `storage rm`, `rmdir -r`, or removing an endpoint route.

**Likely cause:** these are destructive workspace mutations even if the user is in an automated session.

**Recovery:** read current state first, show the exact single command and target, describe what will be removed, then ask for explicit confirmation for that target only. Authorization does not carry to later resources.
