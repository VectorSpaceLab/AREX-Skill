# Sandbox Agent Workflows

Use this reference to assemble common sandbox-agent run shapes without copying networked, Docker-starting, hosted-provider, or real-repo-editing examples.

## Design Order

1. Define the fresh workspace with `Manifest` entries.
2. Define the agent with `SandboxAgent`, stable `instructions`, and capability choices.
3. Choose a client/session source in `RunConfig(sandbox=SandboxRunConfig(...))`.
4. Decide whether later runs resume a live session, serialized `session_state`, runner-managed `RunState`, or a snapshot.
5. Keep all model-facing file paths relative to the sandbox workspace unless intentionally using approved grants.

## Local Coding Agent Pattern

```python
from agents import Runner
from agents.run import RunConfig
from agents.sandbox import Manifest, SandboxAgent, SandboxRunConfig
from agents.sandbox.capabilities import Capabilities
from agents.sandbox.entries import LocalDir
from agents.sandbox.sandboxes.unix_local import UnixLocalSandboxClient

agent = SandboxAgent(
    name="Sandbox engineer",
    instructions=(
        "Read repo/task.md before editing. Use apply_patch for file changes. "
        "Run the narrowest relevant verification and summarize exact commands."
    ),
    default_manifest=Manifest(entries={"repo": LocalDir(src="repo")}),
    capabilities=Capabilities.default(),
)

result = await Runner.run(
    agent,
    "Fix the issue described in repo/task.md.",
    run_config=RunConfig(
        sandbox=SandboxRunConfig(client=UnixLocalSandboxClient()),
        workflow_name="Sandbox coding task",
    ),
)
```

This starts a Unix-local sandbox session through the runner. It is fast for local development but executes on the host under the sandbox workspace boundary; do not treat it as container isolation.

## Client Choice

| Client | Import | Install | Choose when | Trade-off |
| --- | --- | --- | --- | --- |
| `UnixLocalSandboxClient` | `agents.sandbox.sandboxes.unix_local` | base install | Fast macOS/Linux local iteration. | Weakest isolation; no manifest account provisioning. |
| `DockerSandboxClient` | `agents.sandbox.sandboxes.docker` | `openai-agents[docker]` plus Docker daemon | Container isolation or image parity. | Needs Docker SDK/daemon and image dependencies. |
| Hosted clients | provider extension modules | provider-specific extras such as `openai-agents[e2b]` | Managed execution, production-like isolation, or provider runtime features. | Provider credentials, network, API drift, and mount strategy differences. |

Switch clients by changing only `SandboxRunConfig.client` and client `options` when the agent and manifest can stay portable.

## Docker Pattern

```python
from docker import from_env as docker_from_env
from agents.run import RunConfig
from agents.sandbox import SandboxRunConfig
from agents.sandbox.sandboxes.docker import DockerSandboxClient, DockerSandboxClientOptions

run_config = RunConfig(
    sandbox=SandboxRunConfig(
        client=DockerSandboxClient(docker_from_env()),
        options=DockerSandboxClientOptions(image="python:3.14-slim"),
    )
)
```

Use an image that contains the commands your `Shell` capability, tests, or mount strategies need. For remote mounts, the image may need `rclone`, `mount-s3`, `blobfuse2`, or `mount.s3files` depending on strategy.

## Sessions, State, and Snapshots

| Mechanism | Use when | Notes |
| --- | --- | --- |
| `SandboxRunConfig(session=...)` | Reuse one live sandbox in the same process. | The caller owns the live session lifecycle, commonly with `async with sandbox:`. |
| `SandboxRunConfig(session_state=...)` | Resume from serialized sandbox state outside `RunState`. | Backend tries to reattach; if unavailable it may recreate and hydrate from snapshot. |
| `RunState` sandbox payload | Pause/resume a runner-managed workflow. | Runner carries sandbox state alongside model/run state. |
| `SandboxRunConfig(snapshot=LocalSnapshotSpec(...))` | Seed a fresh session from saved workspace contents. | Snapshot IDs become single path segments for local snapshots. |
| `RemoteSnapshotSpec` | Store snapshots behind a dependency-provided remote client. | Client must implement upload/download/exists semantics. |

`Manifest` is not the full truth once a live session, session state, or snapshot is reused. The effective workspace comes from the existing or restored sandbox state, with manifests applying to fresh sessions.

## Skill Mounting Pattern

Prefer the `Skills` capability over manual `.agents` directory mounting:

```python
from agents.sandbox.capabilities import Capabilities, LocalDirLazySkillSource, Skills
from agents.sandbox.entries import LocalDir

capabilities = Capabilities.default() + [
    Skills(lazy_from=LocalDirLazySkillSource(source=LocalDir(src="/approved/skills")))
]
```

Use lazy skills for large skill libraries so the model sees an index and loads only needed skills. If the source path is outside the SDK process working directory, add a trusted read-only `SandboxPathGrant` to the manifest.

## Shell and Apply Patch Patterns

- With `Filesystem`, use the sandbox `apply_patch` tool for edits; paths are relative to workspace root.
- With `Shell`, use `exec_command` for commands and `write_stdin` only when the backend supports PTY interaction.
- Put repo work under a stable workspace path such as `repo/`; tell the agent to run commands with `workdir` inside that path.
- If instructions mention verification, require exact commands and outputs in the final answer.
- Avoid using host absolute paths in prompts. Use `repo/`, `data/`, `output/`, and other workspace-relative paths.

## Memory Workflow

Add `Memory()` only when later sandbox-agent runs should reuse lessons from prior runs. Memory is separate from ordinary SDK conversation sessions.

- `Memory()` reads and generates memories by default.
- Reads require `Shell`; live updates require `Filesystem`.
- Memory artifacts live in the sandbox workspace, usually under `memories/` and `sessions/`.
- Preserve the same live session, session state, or snapshot to reuse memory across runs.
- For multi-agent shared sandboxes, use different memory layouts to keep domains isolated.

## Remote Mount Workflow

1. Choose a mount entry, such as `S3Mount`, `GCSMount`, `R2Mount`, `AzureBlobMount`, `BoxMount`, or `S3FilesMount`.
2. Choose a backend-compatible strategy.
3. Keep `read_only=True` unless write-back is required.
4. Set `mount_path` only when the default destination path is not enough.
5. Validate that the image or provider supports the strategy before relying on it.

Common local/container strategies:

| Strategy | Supports | Runtime need |
| --- | --- | --- |
| `InContainerMountStrategy(pattern=RcloneMountPattern(...))` | S3, GCS, R2, Azure Blob, Box | `rclone`, plus FUSE/NFS mode requirements. |
| `InContainerMountStrategy(pattern=MountpointMountPattern(...))` | S3 and GCS-style mounts | `mount-s3`. |
| `InContainerMountStrategy(pattern=FuseMountPattern(...))` | Azure Blob | `blobfuse2` and FUSE support. |
| `InContainerMountStrategy(pattern=S3FilesMountPattern(...))` | S3 Files | `mount.s3files`. |
| `DockerVolumeMountStrategy(driver="rclone" or "mountpoint")` | Docker volume-driver mounts | Docker volume driver support on host. |

## Safe Distillation of Source Examples

The repository examples demonstrate useful patterns but may edit real files, run Docker, use hosted providers, clone networks, or require credentials. For generated skills, distill these patterns into safe guidance and helpers instead of telling future agents to run source examples directly.
