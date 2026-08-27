---
name: release-packaging
description: "Build and validate versioned FunClip source archives, checksums,
  release notes, templates, and GitHub release contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# release-packaging

Use this sub-skill for FunClip maintainer tasks around versioned source release
archives, checksum files, release notes, README download links, GitHub release
workflow checks, and contributor-facing templates.

## Start here

- Read [release workflow](references/release-workflow.md) for the version-sync
  contract, archive-builder usage, workflow expectations, and focused validation
  commands.
- Read [troubleshooting](references/troubleshooting.md) when a release contract,
  archive build, checksum, template, or GitHub release workflow check fails.
- Use the bundled [release archive builder](scripts/build_release_assets.py) when
  the task asks to build or verify FunClip source archives. It accepts explicit
  `--repository`, `--ref`, and `--output-dir` arguments so it can run from any
  current working directory.

## Best-fit prompts

- Build FunClip release archives or regenerate `SHA256SUMS`.
- Check why `tests/test_release_contract.py` fails.
- Update `VERSION`, release notes, and README download links for a new version.
- Verify issue templates, the pull request template, community links, and focused
  maintainer validation commands.
- Review the release workflow before a tag-based GitHub release.

## Boundaries

This sub-skill owns release packaging, release docs, checksums, GitHub release
workflow contracts, and contributor template expectations. Route runtime ASR,
Gradio, CLI clipping, subtitle, and media-flow questions to `clip-workflows`.
Route LLM provider/model routing or optional provider dependency work to
`llm-providers`, except for noting optional provider-test dependencies during
maintainer validation.

Do not perform or recommend live GitHub publication unless the user explicitly
authorizes maintainer credentials and publication. Without that authorization,
prepare archives, draft notes, validation commands, or workflow review only.
