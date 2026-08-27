# Workspaces and Remote Conversations

## Workspace classes

| Class | Role |
| --- | --- |
| `RemoteWorkspace` | Generic remote workspace interface for a host URL and working directory. |
| `DockerWorkspace` | Starts and manages a Docker container running the agent-server. |
| `DockerDevWorkspace` | Builds a container from a source image or dev target. |
| `ApptainerWorkspace` | Starts a prebuilt image in Apptainer / Singularity environments. |
| `APIRemoteWorkspace` | Talks to the runtime API to start or resume a sandboxed runtime. |
| `OpenHandsCloudWorkspace` | Cloud-managed workspace / sandbox interface. |

## Remote conversation flow

1. Start the agent-server.
2. Create a `Workspace(host=...)` or a workspace implementation.
3. Build `Conversation(agent=..., workspace=workspace)`.
4. Use the remote REST and WebSocket endpoints for state and events.
5. Use the workspace routes to inspect the mounted filesystem or files.

## Important operational notes

- `Workspace(host=...)` is for the remote transport boundary, not a local disk workspace.
- Docker and Apptainer workspaces need a reachable server image.
- `APIRemoteWorkspace` needs runtime API URL and API key credentials.
- `OpenHandsCloudWorkspace` is for the cloud runtime path, not direct local startup.
- Use slash-normalized paths for remote git change/diff query parameters.
