# Craft sandbox and skills

## What this covers

Use this when the task touches Craft build mode, sandbox provisioning, session workspaces, managed skills, user-library sync, or the OpenCode session bootstrap.

## Backend modes

### Kubernetes backend

- Canonical local-dev path for Craft.
- Requires `kind`, `kubectl`, `helm`, and `telepresence`.
- The cluster must be `kind-onyx-dev`, and Craft sandboxes require Kubernetes 1.33 or newer.
- `SANDBOX_BACKEND=kubernetes` selects the in-cluster pod backend.
- `make craft-up` is the one-shot bootstrap for cluster bring-up, sandbox image build/load, and `.env.k8s` setup.
- The local sandbox image must be built and loaded before sessions can start.
- Keep `SANDBOX_CONTAINER_IMAGE` aligned with the image you loaded locally.
- Never do destructive cluster work unless the active kubectl context is the expected kind context.

### Docker backend

- The compose/self-host path uses `SANDBOX_BACKEND=docker`.
- It needs the Docker socket, a sandbox proxy, the dedicated sandbox bridge network, and the proxy CA volume.
- `SANDBOX_PROXY_HOST` is required in this mode.
- `ONYX_SERVER_URL` must point at the full API base URL that sandboxes can reach.
- This backend is a host-level trust boundary: anything with the Docker socket can control containers on the host.

## Session and workspace lifecycle

- Craft uses one sandbox per user and one session workspace per build session.
- `setup_session_workspace` creates the session directory, `outputs/`, `venv/`, `attachments/`, `AGENTS.md`, and the `.opencode/skills` symlink.
- When a session has a web preview, the workspace also gets a `start-webapp.sh` bootstrap script.
- `regenerate_session_config` rewrites the per-session `opencode.json` and `AGENTS.md` when the provider or MCP set changes.
- `ensure_opencode_session` prewarms the runtime ID before the first prompt.
- `reload_session_skills` is the reload path for stale skills or stale MCP config. It rewrites the session config, then disposes the live OpenCode instance so the next turn rereads the new config.
- Session cleanup removes the workspace and best-effort deletes the OpenCode session.

## Managed skills, user library, and config

- `build_managed_content_payload` gathers the connectable-apps section, managed skills payload, user-library files, skills hash, and MCP fingerprint.
- `push_managed_content` pushes skills first, then the user library.
- Hashes are recorded only when the push actually lands.
- The user library is synchronized into sandboxes on session creation, session resume, and user-library changes.
- Sandboxes see stable paths through atomic swaps and managed symlinks; do not assume direct writes into the final path.
- The Craft OpenCode config layers the provider catalog and MCP servers into the per-session `opencode.json` so a model change or MCP change can hot-reload without a pod reprovision.

## Image and spinup notes

- The sandbox image is the Craft runtime image; the normal Onyx app images are not Craft-specific.
- Both backends pre-pull the sandbox image to reduce cold starts.
- Timing and cluster-spinup helpers are reference-only here because they require a live cluster and mutate shared state.
- Do not add bundled cluster-mutation scripts to this skill tree.

## Prereqs and guardrails

- For Kubernetes: kind, kubectl, helm, telepresence, Docker Desktop resources, and a populated `.env.k8s`.
- For Docker: Docker Desktop resources, the sandbox proxy, the proxy CA volume, and the sandbox bridge network.
- Keep the active backend flag, sandbox image tag, and environment file in sync.
- If a sandbox is stuck during provisioning, check whether the image was loaded, the proxy/network is correct, and the active backend matches the environment.
