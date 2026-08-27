# Manifest and Capabilities

Use this reference to design the fresh workspace and capability surface for a `SandboxAgent`.

## Main Objects

| Object | Import | Purpose |
| --- | --- | --- |
| `SandboxAgent` | `from agents.sandbox import SandboxAgent` | Extends normal `Agent` with `default_manifest`, `base_instructions`, `capabilities`, and `run_as`. |
| `Manifest` | `from agents.sandbox import Manifest` | Declares fresh-session workspace root, entries, env, users/groups, path grants, and remote-mount command allowlist. |
| `SandboxRunConfig` | `from agents.sandbox import SandboxRunConfig` | Supplies per-run sandbox client/session/source/snapshot choices through `RunConfig(sandbox=...)`. |
| `SandboxPathGrant` | `from agents.sandbox import SandboxPathGrant` | Grants trusted absolute paths outside the workspace; root paths are rejected. |
| `Permissions`, `FileMode`, `User`, `Group` | `from agents.sandbox import ...` | Configure manifest metadata and sandbox user/group ownership where the backend supports it. |

## Manifest Shape

`Manifest` fields verified in source:

| Field | Default | Notes |
| --- | --- | --- |
| `version` | `1` | Current manifest schema literal. |
| `root` | `"/workspace"` | Absolute sandbox workspace root. |
| `entries` | `{}` | Mapping of workspace-relative paths to entry objects. |
| `environment` | empty `Environment` | Values can be strings or environment value wrappers. |
| `users`, `groups` | `[]` | Provisioned in backends that support accounts; Unix-local rejects provisioning. |
| `extra_path_grants` | `()` | Trusted absolute host/sandbox grants outside workspace. |
| `remote_mount_command_allowlist` | common read/list/copy commands | Commands allowed for remote-mount policy text. |

Entry keys are workspace-relative. The SDK rejects absolute entry paths, Windows absolute paths, and any key containing `..` that escapes the workspace.

## Entry Types

| Entry | Import | Use | Safety notes |
| --- | --- | --- | --- |
| `File(content=...)` | `agents.sandbox.entries` | Small synthetic file content. | Content is copied into the sandbox. |
| `Dir(children={...})` | `agents.sandbox.entries` | Synthetic directory or output directory. | Nested child keys follow the same relative-path checks. |
| `LocalFile(src=...)` | `agents.sandbox.entries` or top-level `agents.sandbox` | Copy one trusted host file. | Source is resolved from the SDK process working directory unless covered by `extra_path_grants`. |
| `LocalDir(src=...)` | `agents.sandbox.entries` | Copy a trusted host directory. | Recursive copy rejects unsupported symlink paths and honors the same base-dir/grant boundary. |
| `GitRepo(repo=..., ref=..., subpath=...)` | `agents.sandbox.entries` | Clone or copy a repository into the workspace. | Pin `ref` for reproducibility; use `subpath` only for trusted repo layout. |
| `S3Mount`, `GCSMount`, `R2Mount`, `AzureBlobMount`, `BoxMount`, `S3FilesMount` | `agents.sandbox.entries` | Attach remote storage. | Mount entries are ephemeral and skipped/detached by snapshot persistence flows. |

Use `Dir` for synthetic folders. Use `LocalDir` only when an existing host directory must be materialized. Do not tell future agents to read original repo paths at runtime; copy needed helpers or references into the skill tree or sandbox manifest.

## Permissions and Users

- Default entry permissions are owner read/write/execute and group/other read/execute.
- `Dir`, `LocalDir`, and mounts mark permissions as directories.
- `Permissions.from_str("drwxr-x---")` can parse POSIX-style permission strings.
- `UnixLocalSandboxSession` rejects manifest `users` or `groups` because provisioning would mutate the host.
- Mount-level permissions are not reliable; configure remote access at the cloud provider and use read-only mounts by default.

## Path Grants and Boundaries

`SandboxPathGrant(path=..., read_only=False, description=None)` is for trusted configuration only.

Good uses:

- Grant a generated skills directory so `Skills(lazy_from=LocalDirLazySkillSource(source=LocalDir(src=...)))` can materialize local skills.
- Grant a read-only toolchain path outside the workspace.
- Grant a temporary output directory under a bounded path.

Avoid:

- Loading grants from model output, user-uploaded manifests, or unreviewed JSON.
- Granting `/`, drive roots, home directories, SSH/config directories, cloud credential directories, or broad project parents.
- Using a writable grant when read-only is enough.

The SDK rejects filesystem-root grants and relative grants. Local source materialization (`LocalFile`, `LocalDir`, lazy skill sources) stays under the SDK working directory unless an explicit grant covers the source.

## Capabilities

`SandboxAgent.capabilities` defaults to `Capabilities.default()`, which returns `Filesystem()`, `Shell()`, and `Compaction()`.

| Capability | Import | Adds | Notes |
| --- | --- | --- | --- |
| `Filesystem` | `agents.sandbox.capabilities` | `apply_patch`, `view_image` | Patch paths are workspace-root-relative, not shell `cwd`-relative. |
| `Shell` | `agents.sandbox.capabilities` | `exec_command`; `write_stdin` when PTY is supported | Uses sandbox session command execution and optional PTY interaction. |
| `Skills` | `agents.sandbox.capabilities` | Skill index and `load_skill` behavior | Prefer over manually mounting `.agents/skills`; supports eager and lazy local/git sources. |
| `Memory` | `agents.sandbox.capabilities` | Memory read/generation workflow | Requires `Shell` for reads; live updates also need `Filesystem`. |
| `Compaction` | `agents.sandbox.capabilities` | Input/model handling for long runs | Included in defaults. |

If you pass `capabilities=[...]`, that replaces the default list. Include any default capabilities you still need.

## Safe Manifest Pattern

```python
from agents.sandbox import Manifest, SandboxAgent, SandboxPathGrant
from agents.sandbox.capabilities import Capabilities, LocalDirLazySkillSource, Skills
from agents.sandbox.entries import LocalDir

agent = SandboxAgent(
    name="Sandbox engineer",
    instructions="Read repo/task.md, edit only workspace files, and report verification.",
    default_manifest=Manifest(
        entries={"repo": LocalDir(src="repo")},
        extra_path_grants=(SandboxPathGrant(path="/trusted/skills", read_only=True),),
    ),
    capabilities=Capabilities.default()
    + [Skills(lazy_from=LocalDirLazySkillSource(source=LocalDir(src="/trusted/skills")))],
)
```

Keep the task spec inside workspace files such as `repo/task.md` when it is long. Keep `instructions` short and stable.

## Remote Mount Policy

- Mount entries describe storage; mount strategies describe how a backend attaches it.
- `mount_path` may be relative to the manifest root or absolute inside the sandbox backend.
- `read_only=True` by default; set `False` only when write-back is required and approved.
- In-container strategies need matching runtime binaries in the image, such as `rclone`, `mount-s3`, `blobfuse2`, or `mount.s3files`.
- Docker volume strategies attach before container startup and are Docker-specific.
- Hosted clients expose provider-specific strategies through extension modules or provider extras.
