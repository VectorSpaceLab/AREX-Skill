---
name: packaging
description: "Plan, preflight, and troubleshoot Open Interface packaging and
  release workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Open Interface packaging sub-skill

Use this sub-skill when the task is to inspect, plan, or troubleshoot Open Interface packaging, PyInstaller builds, release archives, version bump checks, platform packaging dependencies, macOS signing/notarization, or static preflight diagnostics.

Do not use this sub-skill for normal app configuration, model selection, API-key entry, prompt/JSON contract debugging, or desktop automation behavior; route those topics to `../desktop-runtime/`.

## Safety boundary

Automated-safe work:

- Read these bundled references rather than the original repository docs or build script.
- Run the bundled preflight helper: `python scripts/build_preflight.py --repo-root <repo-root>`.
- Add `--json` for machine-readable output or `--compile` for a syntax-only compile check that uses a temporary pycache prefix and does not create `dist/` or `build/` artifacts.
- Inspect generated preflight output for missing resources, hidden imports, platform branch expectations, and version evidence before any manual build is considered.

Manual or approval-required work:

- Running the original `build.py`, PyInstaller, `pip install -r requirements.txt`, package manager installs, archive creation, `codesign`, `notarytool`, `stapler`, or cleanup/deletion of stale release artifacts.
- Launching the packaged GUI app, testing keyboard/mouse automation, granting Accessibility or Screen Recording permissions, or using live OpenAI/Gemini/custom LLM API keys.
- Supplying Apple signing identities, keychain profiles, or any credential-bearing command.

Explicitly excluded: the media conversion helper under the source `assets/` area is not part of the packaging skill. It is hard-coded to specific demo media, depends on moviepy/ffmpeg, and performs destructive removal of an output GIF.

## Routing checklist

1. Classify the request:
   - "Can this build?" / "What would PyInstaller include?" / "Why did the packaged app miss a file?" → read [references/building.md](references/building.md) and run [scripts/build_preflight.py](scripts/build_preflight.py).
   - "How should a release be prepared?" / "Did we bump the version?" / "What does CI prove?" → read [references/release-notes.md](references/release-notes.md).
   - "Build failed with import/resource/signing/platform errors" → read [references/troubleshooting.md](references/troubleshooting.md) first, then use the preflight helper for safe facts.
   - "The app launches but cannot use an API key, screenshot, display, JSON response, or automation action" → route to `../desktop-runtime/` after noting whether the issue happens only inside a packaged build.
2. Prefer safe preflight diagnostics before any full build. The original build workflow is interactive and side-effectful.
3. If a full build or release action is unavoidable, ask for explicit platform, target artifact, dependency-install approval, artifact cleanup approval, and signing/notarization credential boundary before proceeding.

## Bundled materials

- [references/building.md](references/building.md) — distilled `build.py` behavior, exact PyInstaller options, platform branches, dependency notes, resource inclusion, and safe build-planning sequence.
- [references/release-notes.md](references/release-notes.md) — version/release checklist, archive naming, README install promises, CI/static lint context, and private credential boundary.
- [references/troubleshooting.md](references/troubleshooting.md) — predictable install/import, optional dependency, API-key, display/permissions, JSON schema, CLI/API misuse, PyInstaller resource, signing, and stale artifact failures.
- [scripts/build_preflight.py](scripts/build_preflight.py) — standalone static helper that inspects a candidate source tree and build script text without importing PyInstaller, running `build.py`, creating `dist/`/`build/`, signing, notarizing, or launching the GUI.
