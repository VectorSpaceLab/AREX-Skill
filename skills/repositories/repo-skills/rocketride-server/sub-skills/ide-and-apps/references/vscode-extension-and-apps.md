# VS Code Extension and Apps

## Purpose

This reference covers RocketRide's public IDE/app surface: VS Code extension
contributions, visual editors, connection settings, App Builder markers, Module
Federation shell/app loading, app descriptors, and documentation update surfaces.
It intentionally avoids broad React internals.

## VS Code extension public surface

### Activation and visible surfaces

- The extension activates on `onStartupFinished`.
- The activity bar contributes a RocketRide container with a main webview view.
- The extension initializes configuration, cloud auth, one-time migrations,
  connection/deployment managers, engine registry, sidebar, settings, monitor,
  status, welcome/account/environment providers, App Builder, and the pipeline
  project editor.
- The Deploy page command redirects to the Settings page's deployment tab; Docker
  and Service operations are surfaced from Settings panels rather than a separate
  deploy tree provider.

### Custom editors and file associations

| File pattern | VS Code language association | Custom editor viewType | Display name | Notes |
|---|---:|---|---|---|
| `*.pipe` | `json` | `rocketride.PageProject` | Pipeline Grid Editor | Visual pipeline editor. |
| `*.pipe.json` | JSON by extension | `rocketride.PageProject` | Pipeline Grid Editor | Same visual editor path as `.pipe`. |
| `*.rrapp` | `json` | `rocketride.appBuilder` | RocketRide App Builder | Marker document for one app builder screen. |

Important editor behavior:

- `rocketride.PageProject` is registered with `retainContextWhenHidden: true` and
  `supportsMultipleEditorsPerDocument: false`.
- `rocketride.appBuilder` is also retained when hidden and allows only one editor
  per marker document.
- Creating a new pipeline opens a nameless untitled JSON document seeded with
  `{ "components": [] }`, then opens it with `rocketride.PageProject`.
- `Ctrl+S` / `Cmd+S` inside `rocketride.PageProject` runs the RocketRide save
  command so untitled pipelines get the custom save path and titled files save in
  place.
- File associations only make the backing files JSON-readable; the visual editor
  still depends on the custom editor contribution and registration.

### Commands and menus to keep aligned

User-facing commands include:

- Connection: `rocketride.sidebar.connection.connect`, `.disconnect`, `.reconnect`.
- Settings/deploy: `rocketride.page.settings.open`, `rocketride.page.deploy.open`.
- Monitor/status: `rocketride.page.monitor.open`, `rocketride.page.status.open`.
- Pipelines: `rocketride.pipeline.new`, `rocketride.pipeline.save`, sidebar file
  refresh/create/run/stop/status commands.
- Agent docs integration: `rocketride.agents.install`, `rocketride.agents.uninstall`.
- Apps: `rocketride.app.create`, `rocketride.app.open`, `rocketride.app.debug`.

Some older sidebar pipeline commands are stub-registered because webview messages
now handle run/stop/open behavior; keep the manifest and command registrations in
sync so VS Code does not report missing commands.

## Connection and deployment configuration

RocketRide uses two symmetric settings groups:

- `rocketride.development.*` for the active development connection.
- `rocketride.deployment.*` for deployment target settings. Its
  `connectionMode` may be `null`, meaning "same as development".

Supported connection modes are:

| Mode | Meaning | Required user-facing fields | Notes |
|---|---|---|---|
| `cloud` | RocketRide Cloud account flow. | Cloud URL must be valid; API key/session credential lives outside plain settings. | The config manager ignores stale host URL values in cloud mode and uses the build-time cloud URI fallback, defaulting to `https://api.rocketride.ai` when unset. |
| `docker` | Local Docker-backed engine target. | No host URL validation in the config manager. | Requires Docker at runtime; route Docker operations to runtime/deployment guidance. |
| `service` | Local RocketRide service target. | No host URL validation in the config manager. | Usually talks to a local service managed outside the visual editor. |
| `onprem` | Direct server with host URL and API key. | Host URL is required and must normalize to a valid URL. | API key is stored in VS Code secure storage per group. |
| `local` | Local machine engine managed by the extension. | Engine version setting. | Engine version can be `latest`, `prerelease`, or an explicit server tag. |

Configuration details future agents often need:

- Development defaults to `local`; deployment defaults to `null` so it follows
  development unless explicitly set.
- API keys are stored in VS Code secret storage as per-group secrets, not as
  plain `settings.json` values.
- The config manager refreshes on `rocketride.*` configuration changes, secret
  changes, and workspace-folder changes.
- Settings UI saves are applied atomically: intermediate change listeners are
  suppressed, all settings/secrets are written, then the cache refreshes once.
- Per-group config checksums include mode, URL, API key, and local version; when a
  checksum changes, engine/connection reconciliation can restart the affected
  backend.
- Deprecated flat settings migrate to grouped keys: old `connectionMode`,
  `hostUrl`, `local.engineVersion`, `deployTargetMode`, `deployHostUrl`, and
  `deploy.local.engineVersion` map into development/deployment groups.
- Retired team-id settings should not be resurrected; teams are assigned by the
  server profile/deployment scope.

## Pipeline editor defaults

| Setting | Default | Values | IDE-facing meaning |
|---|---:|---|---|
| `rocketride.defaultPipelinePath` | `${workspaceFolder}/pipelines` in the extension contribution; `pipelines` as internal fallback when unset | Any workspace-relative directory-like string | Default directory for new saved pipeline files. |
| `rocketride.pipelineRestartBehavior` | `prompt` | `auto`, `manual`, `prompt` | What to do when a `.pipe` file changes while a pipeline is running. |
| `rocketride.pipelineTTL` | `900` | `900`, `1800`, `3600`, `14400`, `28800`, `0` | Idle timeout in seconds; `0` means run until stopped. |
| `rocketride.pipelineTraceLevel` | `full` | `none`, `metadata`, `summary`, `full` | Default trace verbosity. |
| `rocketride.taskArguments` | empty string | Shell-parsed argument string | Passed as a single string to each pipeline task. Do not split naively on whitespace. |
| `rocketride.pipelineDebugOutput` | `false` | boolean | Adds `--trace=debugOut` unless `taskArguments` already supplies a `--trace=` option. |

App-specific pipeline-builder manifests may also expose similarly named settings
under app-qualified keys such as `rocketride.pipeBuilder.pipelineRestartBehavior`.
When diagnosing user settings, distinguish global extension keys from app manifest
configuration keys.

## App Builder and `.rrapp` markers

App Builder treats apps as real VS Code documents, similar to pipelines:

- The marker file is `<app-folder>/<short-name>.rrapp` and contains JSON like:

  ```json
  {
    "id": "rocketride.pipeBuilder"
  }
  ```

- Opening the marker uses the `rocketride.appBuilder` custom editor.
- If the marker is missing for an older app, the extension creates it on first
  open.
- If the marker JSON is malformed or missing `id`, the provider falls back to the
  containing folder's `package.json` `appManifest.id` binding.
- Workspace app scanning looks for folders with `package.json` containing
  `appManifest.id` at the workspace root, one directory below each root, and
  under the monorepo-style `apps/<name>/` convention.
- The Module Federation `moduleId` is derived from the app id by replacing dots
  and hyphens with underscores.

App Builder preview behavior:

- The preview URL uses the connected development server's HTTP URL by default,
  or `rocketride.appdev.shellUrl` when that override is configured.
- Preview URLs include the app id lock and dev hook flag: `appid=<appId>` and
  `rrdev=1`.
- `rocketride.appdev.autoWatch` controls whether opening an App Builder screen
  starts the watch/rebuild session automatically.
- Closing the App Builder panel stops its watch session and unregisters the dev
  overlay so the shell returns to the published app bundle.
- The App Builder provider forwards connection/server events, watch status,
  dev-server remote entry URLs, console rows, and auth handoff messages into the
  webview.

Do not start the App Builder watch loop as a default verification step. It may
run workspace package installation and `rsbuild dev` for the app. Use static
inspection unless the user explicitly asks for live app development and the Node
workspace is prepared.

## App manifest and descriptor concepts

RocketRide has two distinct app records.

### Lightweight app manifest entry

The lightweight manifest is JSON-compatible and available before an app bundle is
loaded. It is generated from an app package's `appManifest` block and enriched at
runtime with a lazy `load()` function.

Common fields:

| Field | Meaning |
|---|---|
| `id` | Stable app id; must match the full `AppDescriptor.id`. |
| `moduleId` | Module Federation container name, derived from `id`. |
| `name`, `description`, `publisher`, `icon`, `readme`, `categories` | Display and catalog metadata. |
| `configuration` | VS Code-style settings contribution that the shell settings registry can flatten. |
| `authenticated` | `false` means the app can render unauthenticated; default is authenticated. |
| `appStatus`, `onDesktop` | Runtime entitlement/desktop placement facts. |
| `shellApiVersion` | Shell API contract version stamped during app registration/build. |
| `load` | Runtime-only async loader that imports the full `AppDescriptor`. |

### Full `AppDescriptor`

Each remote app exposes `./AppDescriptor`, which default-exports an object with:

| Field | Meaning |
|---|---|
| `id` | Stable app id; also used as workspace state key. |
| `name` | App switcher display name. |
| `icon` | Optional React node for app switcher display. |
| `branding` | Shell-rendered app branding such as `appName`, logos, theme-aware icons, welcome title, and subtitle. |
| `app` | The app's single React mount point; it composes its own layout under the shell. |
| `components` | Optional cross-app component catalog; the shell does not mount these directly. |

Examples of built-in descriptor ids include `rocketride.pipeBuilder`,
`rocketride.hello`, `rocketride.monitor`, `rocketride.explorer`,
`rocketride.aparavi`, `rocketride.events`, `rocketride.profiler`, and
`rocketride.sql`.

When changing app identity or public metadata, keep these synchronized:

1. Package `appManifest.id` and package catalog metadata.
2. Exported `AppDescriptor.id`, `name`, and `branding`.
3. `.rrapp` marker `id` for App Builder documents.
4. Server/manifest registration and any generated app manifest output.
5. User-facing docs/readmes for the app.

## Module Federation shell and remotes

### Shell host

The `shell` package is the Module Federation host with dynamic app loading. Its
package scripts are `start`, `build`, and `build:prod`; the package expects Node
`>=20.11.0`. Do not run these as routine skill validation because they require a
prepared Node workspace.

Important shell-host boundaries:

- The host federation name is `rocketride_shell`.
- The host declares no static remotes; remote entries are registered dynamically
  from the server-provided app manifest.
- The shell provides singleton shared modules for React, React DOM, the `shell`
  public surface, and the TypeScript `rocketride` SDK surface.
- The public `shell` package entrypoint is intentionally thin: it re-exports the
  curated API surface and exposes the live shell API version. Add public exports
  through the curated API surface, not ad hoc entrypoint exports.
- The shell injects selected `RR_*`/`ROCKETRIDE_*` runtime configuration into the
  browser bundle and passes it through `ShellConfig`; remote apps should read
  shell API config rather than `process.env` directly.
- The shell settings registry is built from manifest `configuration` entries and
  can update when a connection/account event delivers a new app manifest.

### Remote UI apps

Remote apps are built separately from the shell:

- Each app package declares `appManifest` metadata.
- The remote's Module Federation name is derived from `appManifest.id`.
- The remote exposes `./AppDescriptor` from its `src/AppDescriptor` module.
- Remote entries are emitted as `remoteEntry.js`; the app is not a standalone
  shell page.
- Remotes use the host-provided `shell` and `rocketride` shared singletons and
  should not bundle their own host runtime surface.
- `assetPrefix: auto` lets chunks resolve relative to the URL that served the
  remote entry.

### Runtime loading flow

1. The shell receives app entries from an unauthenticated probe or authenticated
   connection result.
2. Entries without a `remoteEntry` URL are dropped because they cannot load a UI
   bundle.
3. Valid entries register their Module Federation remotes.
4. The shell maps each server entry into a runtime app manifest with a lazy
   `load()` function.
5. When an app is activated, the loader imports `<moduleId>/AppDescriptor` and
   stores the loaded descriptor.
6. If a manifest entry's remote URL changes, the shell re-registers the remote
   and invalidates the cached descriptor.
7. Dev-owned remotes are not overwritten by manifest re-registration; the App
   Builder dev overlay remains live until stopped or cleared.

## Documentation update surfaces

Apply the co-located documentation rule whenever a public contract changes:

| Change | Update surface |
|---|---|
| VS Code custom editors, settings, commands, App Builder behavior, or extension UX | `apps/vscode/docs/` plus any co-located extension README/prose. |
| UI app public descriptor, app manifest, app readme, app configuration, or catalog metadata | The app's co-located README/docs and package manifest metadata. |
| Shell public API consumed by remotes | Shell API contract/docs and contract-freeze workflow; route generic command details to development/build/docs guidance. |
| `.pipe` schema or pipeline reference | Pipeline authoring/development docs guidance, not this sub-skill alone. |
| Engine/WebSocket/deployment protocol | Runtime/deployment docs guidance. |
| SDK or MCP public APIs | SDK or MCP sub-skills and their docs surfaces. |

After docs updates, the repo policy expects the docs site build to pass when the
Node workspace is available. Do not edit generated reference output directly; use
the responsible generator/build workflow via development/build/docs guidance.
