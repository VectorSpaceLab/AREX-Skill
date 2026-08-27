# Cross-cutting Troubleshooting

## Choose the correct product surface

**Symptom:** A task refers to AutoGPT but the commands, package names, or
architecture do not line up.

**Recovery:** Determine whether it targets Platform (`autogpt_platform`) or
Classic (`classic`). Platform is the current self-hosted stack. Classic uses a
separate Poetry project, has known vulnerabilities, and should not be proposed
as the default for new production work.

## Missing environment files or secrets

**Symptom:** Services start with configuration, auth, database, or provider
errors.

**Recovery:** Read `platform-stack` configuration guidance. Create missing
local `.env` files from their matching defaults without overwriting existing
local files. Compare an existing `.env` with its current default before adding
new keys. Keep all secrets out of commits and prompts.

## Service startup or port conflicts

**Symptom:** Docker Compose fails, a frontend moves to another port, or backend
clients cannot connect.

**Recovery:** Check the Platform preflight helper, Compose status, logs, and
configured port values. Do not reset a database volume merely to resolve a port
conflict. Stop only the conflicting process or choose a documented alternate
configuration.

## Backend and frontend disagree about an API

**Symptom:** A generated frontend hook is absent, has stale types, or calls an
endpoint that no longer exists.

**Recovery:** Confirm the backend route and OpenAPI operation first, then use
the frontend API generation workflow. Do not hand-edit generated endpoint
files; regenerate after the backend schema is correct.

## Package installation/import failures

**Symptom:** Poetry, pnpm, or imports fail before a targeted test can run.

**Recovery:** Use the matching sub-skill's setup section. Confirm the required
runtime version before reinstalling. Platform backend and Classic have separate
Python dependency constraints; do not mix their environments casually. Node 24
and Corepack-managed pnpm are expected by the Platform frontend.

## Unsafe validation defaults

**Symptom:** A proposed command would start a stack, reset a database, run a
benchmark, contact a provider, or load production data.

**Recovery:** Start with help, static inspection, imports, or focused unit
checks. Obtain explicit intent before commands that mutate containers, database
state, remote systems, credentials, or large local artifacts.
