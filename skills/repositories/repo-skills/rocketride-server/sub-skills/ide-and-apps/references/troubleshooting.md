# IDE and Apps Troubleshooting

## Safety boundary

Start with static checks. Do not launch VS Code, start RocketRide services, run
Docker, perform broad `pnpm install`, or build shell/remotes unless the user
explicitly asks for live IDE/app execution and the workspace has the required
Node tooling.

## `.pipe` opens as text instead of the visual editor

Likely causes:

- The file name does not match `*.pipe` or `*.pipe.json`.
- The extension is not activated or failed during activation.
- The custom editor contribution for `rocketride.PageProject` is missing or out
  of sync with the registration code.
- The user explicitly opened the file as text or changed VS Code default editor
  preferences.
- The file is outside the workspace lifecycle the extension expects for new-file
  save behavior.

Static triage:

1. Confirm the file suffix is exactly `.pipe` or `.pipe.json`.
2. Confirm the extension manifest still contributes `rocketride.PageProject` for
   both patterns.
3. Confirm activation and registration paths still register a custom editor with
   viewType `rocketride.PageProject`.
4. If the user created a new pipeline from the command, expect a nameless
   untitled JSON document seeded with `{ "components": [] }` before first save.
5. If save behavior is wrong, check that the `rocketride.pipeline.save`
   keybinding remains scoped to `activeCustomEditorId == 'rocketride.PageProject'`.

Route `.pipe` JSON schema, lane wiring, and engine validation issues to pipeline
authoring. This sub-skill only owns the editor/file-association layer.

## `.rrapp` opens as JSON or App Builder says no bound app

Likely causes:

- The marker file does not end in `.rrapp`.
- The marker JSON is invalid and there is no fallback `appManifest.id` in the
  containing folder.
- The marker `id` does not match any workspace app's `package.json`
  `appManifest.id`.
- The app package is not in a scanned location: the workspace root, one level
  below it, or `apps/<name>/`.
- The custom editor contribution/registration for `rocketride.appBuilder` drifted.

Expected marker shape:

```json
{
  "id": "your.org.app"
}
```

Static triage:

1. Parse the `.rrapp` marker as JSON and read `id`.
2. Parse the containing app package's `package.json` and read `appManifest.id`.
3. Compare both ids with the exported `AppDescriptor.id`.
4. Check that the package's manifest-derived module id replaces dots and hyphens
   with underscores.
5. If an app predates markers, opening it from the App Builder command should
   create the marker automatically; if only double-clicking a stale or malformed
   marker fails, fix the marker or package binding.

## Pipeline changes do not restart a running task

Check the IDE-facing restart setting before debugging engine behavior:

| Setting value | Expected IDE behavior |
|---|---|
| `auto` | Restart automatically when a `.pipe` changes. |
| `manual` | Never auto-restart; user must restart. |
| `prompt` | Ask before restart; this is the default. |

If the setting is correct but behavior is still wrong, separate these causes:

- File watcher/editor layer did not notice the `.pipe` change.
- The task was not actually running when the edit landed.
- Webview/sidebar state is stale; refresh or reconnect may update display state.
- Engine/task failure occurred after restart; route runtime behavior to the
  runtime/deployment sub-skill.

## Default pipeline location is wrong

Facts to check:

- The extension contribution documents `${workspaceFolder}/pipelines` as the
  default path.
- Internal code falls back to `pipelines` when the setting is unset.
- The setting is `rocketride.defaultPipelinePath` and should be interpreted
  relative to the workspace root for normal pipeline creation.

If a new untitled pipeline silently saves somewhere unexpected, distinguish VS
Code's native untitled document behavior from RocketRide's custom save handler.
RocketRide intentionally creates nameless untitled documents so the first save can
present the normal save lifecycle instead of binding prematurely to a path.

## Connection mode does not behave as expected

Use the development/deployment group model:

- `rocketride.development.connectionMode` defaults to `local`.
- `rocketride.deployment.connectionMode` defaults to `null`, meaning deployment
  follows development settings.
- `cloud` uses the cloud URI fallback and ignores stale host URLs from other
  modes.
- `onprem` requires a valid host URL.
- `docker`, `service`, and `local` do not require host URL validation in the
  config manager, but they still depend on their runtime backend when actually
  connecting.
- API keys are stored in VS Code secure storage, not as plain JSON settings.

Common fixes:

| Symptom | Check |
|---|---|
| Cloud points to an old custom URL | Cloud mode intentionally ignores stale `hostUrl`; check the configured build/runtime cloud URI and account flow. |
| On-prem refuses to save/connect | Host URL must normalize to a valid URL and API key must be available for the correct group. |
| Deployment uses development target | `rocketride.deployment.connectionMode` is probably `null`; set an explicit deployment mode if needed. |
| Mode changes cause unexpected engine restart | Per-group checksum changes can trigger reconciliation; this is expected when mode, host URL, API key, or engine version changes. |
| Old settings appear ignored | Flat/deprecated keys are migrated to `development.*` and `deployment.*`; use grouped keys. |

Route port 5565, Docker, service installation, Helm, and engine start failures to
runtime/deployment guidance.

## App Builder preview is blank, stale, or says `App not found`

First separate preview-shell selection from app build status.

Likely causes:

- `rocketride.appdev.shellUrl` points at a different origin than the connected
  development server. The dev overlay registers on the connected server, so a
  preview shell from another origin cannot see it.
- The extension is not connected, so the App Builder cannot vendor the platform
  package or register the dev overlay.
- The `.rrapp` marker id, package `appManifest.id`, and descriptor id differ.
- `rocketride.appdev.autoWatch` is `false`, so no watch session starts on open.
- The watch loop could not run package installation or `rsbuild dev`.
- The app package lacks the expected app manifest or build-time dependencies.

Static triage:

1. Compare preview base URL with the connected development server's origin.
2. Check `.rrapp` marker id, package `appManifest.id`, descriptor id, and
   manifest-derived module id.
3. Confirm the app package declares build scripts and an app manifest.
4. If live dev is authorized, inspect the App Builder Console/Errors panes for
   the first failing phase: platform package vendoring, workspace install,
   rsbuild start, remote entry registration, or descriptor import.
5. If live dev is not authorized, report the unverified requirement instead of
   running the watch loop.

## Module Federation app is not registered or will not load

Likely causes:

- The server/app manifest entry has no `remoteEntry` URL; the shell drops such
  entries because they cannot load a UI bundle.
- The remote URL changed but the descriptor cache was not invalidated.
- The remote does not expose `./AppDescriptor` or default export an `AppDescriptor`.
- The manifest `moduleId` does not match the remote federation name.
- The remote bundles incompatible React/shell/SDK instances instead of consuming
  the host-provided singletons.
- A dev-owned remote is being overwritten by a manifest re-registration.
- A previously failed remote container is half-initialized and needs reset before
  retry.

Static triage:

1. Confirm app manifest fields: `id`, `moduleId`, `name`, and remote entry URL.
2. Confirm the app remote exposes `./AppDescriptor`.
3. Confirm `AppDescriptor.id` equals the manifest id.
4. Confirm remote sharing treats `shell` and `rocketride` as host-provided
   singletons.
5. If a dev preview is involved, confirm the preview receives the dev remote
   registration for the locked app before descriptor load.

When live browser logs are available, useful signatures are:

- `Invalid AppDescriptor`: the module loaded but did not export a usable app
  descriptor, especially a missing `app` mount point.
- `dev remote ... failed to load`: the dev `remoteEntry.js` or shared-scope
  negotiation failed.
- `RUNTIME-012` or share-scope errors: usually duplicate/missing Module
  Federation shared instances or a dev remote overriding an already-initialized
  container.
- Repeated `App not found` in dev preview: preview shell and connected server are
  probably not the same origin, or the app id was not registered in the overlay.

## App descriptor metadata does not show correctly

Check descriptor and manifest separately:

| Bad display | Check |
|---|---|
| Wrong app name in app switcher | Lightweight manifest `name`, then full descriptor `name`. |
| Wrong sidebar/welcome branding | Full descriptor `branding.appName`, icons, welcome title/subtitle. |
| Icon missing | Manifest icon path or descriptor `icon`/branding icon fields; large or missing icon files can fall back to generic display. |
| App requires login unexpectedly | Manifest `authenticated`; absence usually means authenticated by default. |
| Settings not appearing | Manifest `configuration` must use VS Code-style `contributes.configuration` shape with dotted keys. |
| Active app disappears after login | Pre-auth and post-auth manifests differ; check app entitlement/desktop status and remote URL. |

Do not solve display metadata drift by editing broad React internals first. Start
with manifest and descriptor identity/branding fields.

## Docs drift after extension or app changes

Use these surfaces:

- VS Code custom editors, settings, commands, App Builder UX: update
  `apps/vscode/docs/` and related extension prose.
- UI app public metadata/config/descriptor behavior: update the app's co-located
  README/docs and package manifest metadata.
- Shell API consumed by remotes: update shell API contract/docs through the
  development/build/docs workflow.

Do not hand-edit generated docs/reference output. If the docs build or generator
requires unavailable Node workspace dependencies, record that as an environment
blocker rather than pretending the docs were verified.

## Narrow static checks you can do safely

Use these checks conceptually or with equivalent project-local commands; they do
not require starting services:

- Parse extension and app package manifests as JSON.
- Search for custom editor viewType strings and verify they match manifest
  contributions.
- Parse `.rrapp` markers and compare ids to package `appManifest.id`.
- Inspect exported `AppDescriptor` objects for `id`, `name`, `branding`, and
  `app` fields.
- Compare app ids to Module Federation module ids by applying the expected
  dot/hyphen-to-underscore transformation.
- Review settings keys for grouped development/deployment mode and deprecated
  flat-key migration.

Escalate only after static checks identify a live runtime need: VS Code launch,
engine connection, App Builder watch, shell build, remote app build, Docker,
Kubernetes, or external credentials.
