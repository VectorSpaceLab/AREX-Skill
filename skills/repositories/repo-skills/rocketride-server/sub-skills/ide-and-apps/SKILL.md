---
name: ide-and-apps
description: "Operate RocketRide IDE extension, visual editors, app descriptors,
  and Module Federation app surfaces."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# RocketRide IDE and Apps

Use this sub-skill when a task involves the RocketRide VS Code extension, visual
pipeline/app editors, `*.pipe` or `*.rrapp` file associations, development versus
deployment connection settings, App Builder behavior, Module Federation shell/app
loading, or UI app descriptors.

## Route first

- For extension settings, custom editors, connection modes, App Builder markers,
  Module Federation loading, app descriptors, and documentation surfaces, read
  [VS Code extension and apps](references/vscode-extension-and-apps.md).
- For editor/app-loading failures, file association problems, App Builder watch
  issues, preview mismatch, or Module Federation share-scope errors, read
  [troubleshooting](references/troubleshooting.md).

## Use this for

- Opening or diagnosing the visual pipeline editor for `.pipe` and `.pipe.json`
  files.
- Opening or diagnosing the App Builder for `.rrapp` marker files.
- Explaining `cloud`, `docker`, `service`, `onprem`, and `local` connection modes
  for development and deployment groups.
- Reasoning about default pipeline path, restart behavior, TTL, trace level,
  task arguments, and debug-output settings as IDE-facing defaults.
- Maintaining app manifests/descriptors and the shell/remotes boundary.
- Deciding which co-located docs must change for extension or app public surface
  edits.

## Do not use for

- `.pipe` schema depth, node wiring, or workflow recipes → `../pipeline-authoring/SKILL.md`.
- Python/TypeScript SDK calls, CLI usage, tokens, or API signatures → `../sdk-clients/SKILL.md`.
- Engine startup, Docker, Helm, port 5565, or deployment protocol operations → `../runtime-deployment/SKILL.md`.
- MCP, n8n, webhooks, or external automation integrations → `../mcp-and-integrations/SKILL.md`.
- Broad React component internals, visual styling refactors, or app business logic
  unrelated to the public descriptor/shell/extension surface.

## Operating rules

1. Treat the VS Code manifest and extension configuration as the public IDE
   contract: custom editor ids, commands, keybindings, file associations, and
   `rocketride.*` settings must stay aligned.
2. Treat app identity as a three-way contract: `package.json` `appManifest.id`,
   exported `AppDescriptor.id`, and `.rrapp` marker `id` must match.
3. Keep the shell/remotes boundary intact: the shell hosts shared singletons and
   dynamically loads remote `AppDescriptor`s; app remotes expose descriptors and
   must not own the host runtime.
4. Prefer static inspection and narrow docs/config checks. Do not launch VS Code,
   start services, run Docker, run broad `pnpm install`, or build shell/remotes
   unless the user explicitly asks and the environment is prepared.
5. If a public extension or app contract changes, update the matching co-located
   documentation in the same change and route generic builder/docs commands to
   the development/build/docs guidance.

## Good output looks like

- Clear distinction between development and deployment configuration groups.
- Correct custom editor ids: `rocketride.PageProject` for pipeline files and
  `rocketride.appBuilder` for app marker files.
- Correct file extensions: `.pipe`, `.pipe.json`, and `.rrapp`.
- Accurate app descriptor fields and Module Federation loading flow.
- Troubleshooting that separates editor registration, file association,
  connection mode, App Builder watch, and shell remote-loading causes.
