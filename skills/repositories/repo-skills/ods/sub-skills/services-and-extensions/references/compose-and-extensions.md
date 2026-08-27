# Compose Layering And Extension Contracts

This reference distills the service manifest, compose, registry, and lifecycle
behavior used by ODS extensions. It is the operational contract for adding,
reviewing, enabling, disabling, installing, updating, or rolling back a service
extension.

## 1) Manifest contract

ODS uses the `ods.services.v1` manifest contract. The schema allows extra
fields, but the registry, resolver, and audit logic rely on the fields below.
Keep new manifests explicit instead of depending on hidden defaults.

### Root fields

| Field | Required | Meaning |
|---|---:|---|
| `schema_version` | yes | Must be `ods.services.v1`. |
| `compatibility.ods_min` | no | Minimum ODS version supported by the extension. |
| `compatibility.ods_max` | no | Highest ODS version tested by the extension. |

### Service fields

| Field | Required | Meaning |
|---|---:|---|
| `service.id` | yes | Unique kebab-case service id. Also used for registry lookups. |
| `service.name` | yes | Human-readable label. |
| `service.type` | yes | `docker` or `host-systemd`. |
| `service.category` | yes | `core`, `recommended`, or `optional`. |
| `service.port` | yes unless `host_network: true` | Internal container port or host service port. |
| `service.health` | yes unless `host_network: true` | HTTP health path. Use `""` only for non-HTTP or one-shot services. |
| `service.host_network` | no | Marks a Docker host-network service that has no Docker-published port. |
| `service.compose_file` | no for core, yes for non-core docker services | Relative compose fragment path. The enabled file is `compose.yaml`; the disabled marker is `compose.yaml.disabled`. |
| `service.aliases` | no | Short names that resolve to the same service id. |
| `service.container_name` | no | Container name used by compose and the registry. |
| `service.default_host` | no | Default host name used inside the stack. |
| `service.host_env` | no | Environment variable that controls host overrides. |
| `service.external_port_env` | no | Env var that controls the user-facing port. |
| `service.external_port_default` | no | Default user-facing port. `0` means internal-only / no published port. |
| `service.gpu_backends` | no | Backend compatibility filter used for overlay selection. Set this explicitly. |
| `service.depends_on` | no | Service ids that must be present and enabled before activation. |
| `service.env_vars` | no | Documented environment variables used by the service. |
| `service.llm` | no | Swap-safety contract for services that consume a model endpoint. |
| `service.startup_check` | no | Set `false` for one-shot services whose clean exit counts as success. |
| `service.startup_timeout` | no | Startup wait budget in seconds for slow services. |
| `service.container_uid` | no | Host-side UID hint for bind-mounted data directories. |
| `service.ui_path` | no | Path to the user-facing UI. |
| `service.hooks` | no | Lifecycle hooks such as `pre_install` and `post_install`. |
| `service.setup_hook` | no | Legacy single setup hook; prefer `hooks.post_install`. |

### Feature fields

| Field | Required | Meaning |
|---|---:|---|
| `features[].id` | yes | Unique feature id. |
| `features[].name` | yes | UI label. |
| `features[].description` | yes | Human-readable feature text. |
| `features[].icon` | yes | Icon name for the dashboard catalog. |
| `features[].category` | yes | Feature grouping. |
| `features[].requirements` | yes | Service, VRAM, and disk requirements. |
| `features[].priority` | yes | Sort order; lower numbers usually surface earlier. |
| `features[].launch` | no | Launch target used by feature tiles. |
| `features[].gpu_backends` | no | Backend filter for the feature tile. |

### LLM consumer contract

When a service sends prompts or completions to an LLM, the manifest should
state that explicitly.

| Field | Required when `consumes: true` | Meaning |
|---|---:|---|
| `service.llm.consumes` | yes | `true` when the service talks to an LLM endpoint. |
| `service.llm.route` | yes | Prefer `gateway`; use `direct` only when a gateway path is not workable. |
| `service.llm.pinning` | yes | `none` or `dynamic`. Use `none` unless the app truly tracks a live model state. |
| `service.llm.probe` | yes | Deterministic probe used after model swaps. |
| `service.llm.min_context` | no | Minimum context floor the app needs. |

Guidance:

- Prefer `route: gateway` and `pinning: none`.
- Do not persist concrete model names unless the app has a documented dynamic
  refresh path.
- Include a probe path that actually proves the app can talk to the active
  model backend.

## 2) Compose layering

ODS resolves compose files as a layered stack. The exact files that appear in the
final stack depend on backend, mode, extension enablement, and security checks.

### High-level order

1. Base compose stack (`docker-compose.base.yml` and the selected backend/tier overlay).
2. Enabled bundled extension compose files.
3. Bundled extension GPU overlay for the active backend, when present.
4. Bundled local-mode overlay when local/hybrid mode allows it.
5. Bundled multi-GPU overlay when more than one GPU is detected.
6. Enabled user-installed extension compose files.
7. User-installed extension GPU/local/multi-GPU overlays, after security scanning.
8. External LLM overlay when the host is using an external model runtime.
9. `docker-compose.override.yml`, after security scanning.
10. Apple cloud auth overlay last, when Apple cloud mode is active.

### Overlay patterns

| Pattern | Base file | Overlay file | Use case |
|---|---|---|---|
| CPU base + GPU swap | Full service definition | `compose.nvidia.yaml` / `compose.amd.yaml` / `compose.apple.yaml` | Same service shape, different image tag or device settings. |
| GPU-only service | `services: {}` stub | Backend-specific overlay with the full definition | No CPU fallback. |
| Local-mode variant | Normal base compose | `compose.local.yaml` | Same service, but with local-only dependencies or startup gates. |
| Multi-GPU variant | Normal base compose | `compose.multigpu-<backend>.yaml` or `compose.multigpu.yaml` | Special handling when more than one GPU is present. |

### Enable / disable marker

- `compose.yaml` means the service is enabled.
- `compose.yaml.disabled` means the service is visible but disabled.
- Core services are usually defined in the base stack and therefore do not need
  a per-service compose file.
- Non-core docker services must provide a compose file for activation.
- `host-systemd` services usually do not ship a compose file.

### Path safety

`service.compose_file` must stay inside the extension directory. Absolute paths
and traversal paths are rejected. This keeps extension compose files from
escaping into unrelated host files.

## 3) Service registry behavior

The service registry is a manifest-driven view of services and enabled compose
fragments.

- Service ids and aliases resolve to the canonical service id.
- A leading `ods-` prefix is stripped before alias resolution when needed.
- `SERVICE_PORTS` starts from the manifest and then resolves environment-backed
  port overrides when those env vars are present.
- `host_network: true` services skip Docker-published port and HTTP-health
  assumptions.
- `sr_list_enabled` only returns services whose enabled compose file is present.
- `sr_compose_flags` builds the active `docker compose -f ...` list from enabled
  extension files and caches the result for the session.
- Malformed manifests are skipped with visible warnings instead of hidden
  fallback behavior.

## 4) Install / update / rollback semantics

The extension library and the installed extension tree follow a definition-only
update model: data stays put unless the extension itself is reinstalled or
uninstalled.

| State | Meaning | Typical action |
|---|---|---|
| `current` | Installed files match the stored receipt and the library definition. | No action needed. |
| `available` | The bundled library has a newer definition. | Review and update if desired. |
| `modified` | Local installed files diverged from the stored receipt. | Confirm before overwriting. |
| `untracked` | Legacy install without a receipt. | Treat as manual/old state and review carefully. |

Lifecycle rules:

- Install copies the library definition into the installed extension area, scans
  the compose content, and only then activates it.
- Enable/disable is a rename operation on the compose marker plus a start/stop
  action.
- Disable stops the service before renaming the compose file out of the way.
- Update stages the new definition, security-scans it, and replaces the installed
  definition atomically on the same filesystem.
- Rollback restores the previous definition only; it does not delete data,
  volumes, secrets, or existing config files.
- Enabled services are reconciled after update. Disabled and one-shot services
  stay disabled.
- Dependency checks happen before enable. If a disabled service still has
  dependents, warn rather than silently breaking the stack.

## 5) Compose security failure modes

User-installed extension compose files and `docker-compose.override.yml` are
scanned as untrusted input. The resolver rejects or skips content with the
following patterns:

- `privileged: true`
- `build:` instead of a pre-built image
- `user: root` or `user: 0`
- `network_mode: host`
- `pid: host`, `ipc: host`, or `userns_mode: host`
- dangerous capabilities such as `SYS_ADMIN`, `NET_ADMIN`, `SYS_PTRACE`,
  `NET_RAW`, `DAC_OVERRIDE`, `SETUID`, `SETGID`, `SYS_MODULE`, `SYS_RAWIO`, or
  `ALL`
- dangerous `security_opt` values such as `seccomp:unconfined`,
  `apparmor:unconfined`, or `label:disable`
- `devices:` or GPU passthrough via `deploy.resources.reservations.devices`
- Docker socket mounts
- absolute host bind mounts, including bind-style top-level volume options
- `extra_hosts` or `sysctls`
- reserved Docker Compose labels that start with `com.docker.compose.`
- published ports that do not stay on loopback (`127.0.0.1` or
  `${VAR:-127.0.0.1}`)
- `service.compose_file` values that escape the extension directory
- user content that reuses a built-in core service id or alias

Practical fixes:

- Replace host binds with relative data paths inside the extension directory.
- Use loopback-only published ports.
- Replace root, host namespace, or privileged directives with a vetted image and
  a narrower compose shape.
- Keep user extensions out of built-in core ids and aliases.
- Add the matching backend overlay when the manifest declares a backend that
  needs one.

## 6) New-extension checklist

1. Pick a unique service id and a stable human-readable name.
2. Decide whether the service is `core`, `recommended`, or `optional`.
3. Add a manifest with explicit `schema_version`, `service`, and any `features`
   or `llm` metadata you need.
4. Add the compose file and any backend overlays that the manifest requires.
5. Keep published ports loopback-only.
6. Run the bundled summary helper on the catalog root and fix any missing fields,
   collisions, or overlay gaps.
7. Revisit the security failure list above before treating the service as ready.

