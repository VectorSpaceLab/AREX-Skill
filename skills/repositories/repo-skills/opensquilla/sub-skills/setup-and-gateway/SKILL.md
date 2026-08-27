---
name: setup-and-gateway
description: "Get OpenSquilla installed, onboarded, and running through a ready
  local gateway and Web UI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Setup and Gateway

Use this sub-skill for the path from a fresh install to the first successful gateway and Web UI run.

## Route elsewhere

- Provider catalog, router tier selection, and search provider setup: `../configuration-and-routing/SKILL.md`
- CLI automation, sessions, memory, diagnostics, replay, migration, and uninstall: `../cli-and-automation/SKILL.md`
- Terminal UI and desktop runtime details: `../tui-and-desktop/SKILL.md`

## What belongs here

- release-wheel vs source-install choices
- first-run onboarding and safe reruns with `--if-needed` or `--minimal`
- gateway lifecycle: `run`, `start`, `status`, `stop`, `restart`, `reload`
- `doctor` readiness checks and `bundle` diagnostics collection
- Web UI launch basics and local access
- source-install prerequisites and built-console expectations
- gateway bind/port behavior and safe exposure notes

## Fast operating path

1. Pick the install path.
   - Release wheel: normal terminal install, no Git or Node.js required.
   - Source install: only when the user is working from a checkout and needs to build the Web UI.
2. Run onboarding.
   - Interactive: `opensquilla onboard`
   - Idempotent rerun: `opensquilla onboard --if-needed`
   - Smaller first-run setup: `opensquilla onboard --minimal`
   - Script-friendly provider setup: `opensquilla onboard --provider <id> --api-key-env <ENV_VAR>`
3. Start the gateway.
   - Foreground: `opensquilla gateway run`
   - Managed background process: `opensquilla gateway start --json`
4. Confirm readiness.
   - `opensquilla onboard status`
   - `opensquilla gateway status`
   - `opensquilla doctor`
   - Open `http://127.0.0.1:18791/control/`
5. If the user needs public exposure, use the safer bind and auth notes in `references/gateway-lifecycle.md` first.
6. Use `references/troubleshooting.md` for the common first-run failures.

## When to hand off

- If the question is really about provider, router, or search setup, hand off to `configuration-and-routing`.
- If the question is about chat history, sessions, memory, cron, replay, or uninstall, hand off to `cli-and-automation`.
- If the question is about TUI or desktop packaging/runtime behavior, hand off to `tui-and-desktop`.

## Bundled references

- `references/install-and-first-run.md`
- `references/gateway-lifecycle.md`
- `references/web-ui.md`
- `references/troubleshooting.md`

## Notes

- `opensquilla bundle` is a shareable diagnostics zip and works even when the gateway will not start.
- Source installer scripts are reference-only here because they mutate the install and rebuild the Web UI; this sub-skill stays guidance-only.
