# Backend Matrix

## Purpose

Read this before choosing a workspace backend or diagnosing why one backend works and another does not.

## Verified workspace backends

| Workspace | Best for | Key prerequisite |
| --- | --- | --- |
| `LocalWorkspace` | Local development, smoke tests, and file-backed skill seeding | No external runtime; uses the host filesystem |
| `DockerWorkspace` | Container-isolated execution | Docker daemon / container runtime |
| `BubblewrapWorkspace` | Lightweight Linux isolation | `bwrap` support on the host |
| `AppleContainerWorkspace` | macOS container isolation | Apple Container support on macOS |
| `E2BWorkspace` | Cloud sandbox execution | E2B account / API key |
| `DaytonaWorkspace` | Remote dev workspace execution | Daytona account / API key |
| `K8sWorkspace` | Kubernetes-backed workspaces | Reachable cluster and kubeconfig |
| `OpenSandboxWorkspace` | Remote sandbox execution | OpenSandbox account / endpoint |

## Common pattern

All workspace implementations share the same high-level contract:

- `initialize()` provisions the workspace and seeds skills / MCPs.
- `list_tools()` exposes the built-in file and shell tools for that backend.
- `list_skills()` and `list_mcps()` enumerate the active workspace resources.
- `add_skill()` / `remove_skill()` and `add_mcp()` / `remove_mcp()` mutate the workspace state.
- `close()` ends backend sessions without deleting the workspace root.

## Practical selection guide

| Need | Best choice |
| --- | --- |
| Verify the skill tree locally | `LocalWorkspace` |
| Test container boundaries | `DockerWorkspace` or `BubblewrapWorkspace` |
| Test a macOS-specific workspace path | `AppleContainerWorkspace` |
| Run on a hosted remote sandbox | `E2BWorkspace`, `DaytonaWorkspace`, or `OpenSandboxWorkspace` |
| Match an existing Kubernetes deployment | `K8sWorkspace` |

## Notes

- `LocalWorkspace` is the easiest way to verify skill seeding and path-safe file tools.
- Remote or container backends may need an initialized backend before `get_backend()` becomes available.
- If a backend-specific failure disappears when you fall back to `LocalWorkspace`, the issue is probably the backend/runtime rather than the skill content.
