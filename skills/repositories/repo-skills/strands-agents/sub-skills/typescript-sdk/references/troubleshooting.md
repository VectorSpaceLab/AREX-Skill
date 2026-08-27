# Troubleshooting

## Quick diagnosis table

| Symptom | Likely cause | What to check | Typical fix |
| --- | --- | --- | --- |
| `npm install` changed the workspace unexpectedly | Dependency drift or an outdated lockfile | Compare `package.json`, workspace scripts, and lock state | Use `npm ci` for normal installs; refresh the lockfile only when dependencies changed |
| A public import is undefined at runtime | Barrel omission or type-only export | Check the relevant barrel and package export entry | Add the missing named export and keep it a value export when runtime access is required |
| Browser bundle fails on Node builtins | Node/browser split leaked into the browser path | Check the default barrel and any direct Node imports | Move the code behind the Node entry point or a Node-only subpath |
| Provider tests fail without credentials | A live integration test ran in the wrong context | Confirm whether the test is mocked or credential-backed | Keep offline unit tests mocked; run provider-backed checks only when explicit credentials are available |
| Browser tests fail because Chromium is missing | Playwright browser install has not been done | Check whether the browser test helper was run | Install the browser runtime before browser tests |
| Example commands fail in one example but not another | Example project isolation or missing local install | Check the example's own `package.json` and workspace assumptions | Treat each example as a standalone project and install its dependencies explicitly |
| Type-check fails on optional properties or exported types | Strict TS rules, barrel shape, or interface/type mismatches | Check signatures, TSDoc, and exact optional-property usage | Fix the declaration shape rather than suppressing the error |
| Lint fails on logging or comments | SDK style rules | Check for printf logging, `any`, or non-evergreen comments | Rephrase the log line or comment to match the established style |

## Workspace dependency drift

Use this pattern when the workspace feels inconsistent:

1. Prefer `npm ci` for a clean install.
2. Change dependencies only through `npm install` or `npm update`.
3. After dependency edits, refresh the lockfile with the workspace lock-refresh command.
4. Re-run the packaging check so the tarball still contains the expected files only.
5. If the dependency graph changed, refresh the lockfile with `npm run lock:refresh -w strands-ts`.

## Peer dependency classification

If a package crosses a consumer API boundary, it must be a peer dependency.

That means:

- tool schemas that consumers construct should keep schema libraries in peers
- provider SDKs that users pass into constructors should stay peers
- build tools, test frameworks, and linting tools stay in devDependencies
- optional peers should also appear in devDependencies for repository work

## Export and barrel omissions

Symptoms:

- compile-time import failures
- runtime `undefined` exports
- a symbol exists in source but not from the public barrel

What to do:

1. Check the relevant barrel first.
2. Confirm whether the export must be a value export or a type export.
3. Update the package export map if the public path changed.
4. Add a regression test that imports the public surface the way a consumer would.

## Node vs browser split

Symptoms:

- browser bundle failures
- `process`, `fs`, `child_process`, or similar builtins leaking into browser code
- Node defaults not registered when expected

What to do:

- Keep Node-specific setup in the Node entry point or a Node-only helper.
- Keep browser-safe paths free of Node-only imports.
- Re-run the browser bundle check after touching top-level exports or model imports.
- Use the browser helper script to print the install reminder before browser tests.

## Provider credential tests

Treat provider-backed checks as conditional.

- Mocked unit tests should not need live credentials.
- Live Bedrock, OpenAI, Anthropic, or Google checks should be explicit about their credential and network needs.
- If a provider test fails, first confirm the test is pointed at the right backend and the required credentials are present.
- Keep provider error translation tests mocked so they remain fast and deterministic.

## Playwright and browser install

If browser unit tests fail early:

1. Confirm Playwright is installed for the workspace.
2. Confirm Chromium is installed.
3. Re-run the browser bundle check separately from the browser test project.
4. Keep browser-only failures isolated from Node-only checks.

## Example project isolation

The examples are standalone projects.

- Do not assume the root workspace state is enough.
- Do not assume one example's dependencies satisfy another example.
- Use each example's own commands and read its local `package.json` before changing it.
- The browser example is intentionally unsafe for untrusted code and should stay clearly labeled as a demo.

## Strict type and lint failures

The common causes are:

- `any` in a signature or callback
- missing return type annotations on functions and methods
- wrong `interface`/`type` choice
- missing TSDoc on exports
- non-evergreen comments
- logging with printf-style placeholders instead of the established structured format

Fix the shape, not the symptom.

## Native candidate escalation

If a failure only appears in a browser, credentialed, or example-specific path:

- keep the unit path mocked
- move the live check to the appropriate conditional candidate
- do not promote a conditional path to the default verification set without a clear reason
