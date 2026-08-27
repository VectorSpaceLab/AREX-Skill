# FunClip release workflow

This reference is for maintainer-style release packaging work: synchronizing the
version contract, building source archives, validating checksums, checking the
GitHub release workflow, and keeping contributor templates aligned.

## Version and release checklist

Treat `VERSION` as the release source of truth.

1. Set `VERSION` to semantic `x.y.z` form, for example `2.1.1`.
2. Use tag name `vX.Y.Z`; the release workflow checks that the tag equals
   `v${VERSION}`.
3. Add or update release notes at `docs/releases/vX.Y.Z.md` before tagging.
4. Update both `README.md` and `README_zh.md` so public download routes use the
   same version:
   - release page: `https://github.com/modelscope/FunClip/releases/tag/vX.Y.Z`
   - tar archive: `FunClip-X.Y.Z.tar.gz`
   - zip archive: `FunClip-X.Y.Z.zip`
   - checksum asset: `SHA256SUMS`
5. In release notes, keep the asset boundary explicit: archives contain tracked
   source, docs, and dependency manifest; runtime dependencies and model weights
   are not bundled.
6. Keep dependency notes that affect fresh installs visible. For the v2.1.1
   contract, release notes mention `funasr>=1.3.29`, `starlette<1.0`, Fun-ASR-
   Nano, SenseVoice, MiniMax, TwelveLabs, case-insensitive transcript matching,
   both archive names, `SHA256SUMS`, and that model weights are not bundled.
7. Run the focused validation commands below before considering a release ready.

## Archive builder usage

Use the bundled builder from this sub-skill when a future agent needs to build
or check release assets without reopening the original source script. From the
`funclip` generated skill root, run:

```bash
python sub-skills/release-packaging/scripts/build_release_assets.py \
  --repository <funclip-repository> \
  --ref <commit-or-tag-that-resolves-to-a-commit> \
  --output-dir <dist-directory>
```

The builder reads `VERSION` from the selected Git commit, creates both archives
under the `FunClip-X.Y.Z/` prefix, validates required files, rejects generated
metadata, compares tar/zip members, and writes:

- `FunClip-X.Y.Z.tar.gz`
- `FunClip-X.Y.Z.zip`
- `SHA256SUMS`

Recommended local checksum check after a build:

```bash
cd <dist-directory>
sha256sum -c SHA256SUMS --ignore-missing
```

For reproducibility-sensitive release work, build twice from the same commit and
compare output directories byte-for-byte before publication.

## GitHub release workflow contract

The release workflow is tag-driven and intentionally conservative:

- Trigger: pushes to tags matching `v*.*.*`.
- Permissions: `contents: write` only for release asset management.
- Checkout and setup actions are pinned to commit SHAs rather than floating
  `@v...` references.
- Python setup installs `pytest==8.3.5` for the release contract check.
- Before building, the workflow verifies:
  - `GITHUB_REF_NAME` equals `v${VERSION}`.
  - `docs/releases/${GITHUB_REF_NAME}.md` exists.
- The workflow runs `python -m pytest -q tests/test_release_contract.py`.
- Assets are built with `python scripts/build_release_assets.py --ref "$GITHUB_SHA" --output-dir dist`.
- Release creation uses GitHub CLI draft flow:
  - inspect current release state with `gh release view --json apiUrl,isDraft,isImmutable`;
  - create a draft with `gh release create --verify-tag --draft --notes-file ...` when absent;
  - refresh draft title/notes with `gh release edit --draft`;
  - upload `dist/FunClip-*.tar.gz`, `dist/FunClip-*.zip`, and `dist/SHA256SUMS` with `--clobber`;
  - verify asset name, size, and `sha256:` digest through the release API;
  - only then publish with `gh release edit --draft=false --latest`.
- If a release is already published, the workflow verifies existing assets and
  exits successfully only when they match the expected size and digest.

Do not use this sub-skill to publish a live release manually unless the user has
explicitly provided maintainer authorization and credentials.

## Focused maintainer validation commands

Run the smallest command set that matches the change.

### Packaging or release-doc changes

```bash
python -m pytest -q tests/test_release_contract.py
# From the generated funclip skill root:
python sub-skills/release-packaging/scripts/build_release_assets.py \
  --repository . --ref HEAD --output-dir dist
```

### Issue, pull request, community, or canonical-link changes

```bash
python -m pytest -q \
  tests/test_github_templates.py \
  tests/test_community_links.py \
  tests/test_canonical_qwenaudio_links.py
```

### Contributor-guide validation path

The contributor guide's focused path for docs, issue templates, package metadata,
and provider-routing changes includes:

```bash
python3 -m pytest -q tests/test_github_templates.py tests/test_funasr_requirement.py tests/test_openai_api.py
python3 -m py_compile funclip/launch.py funclip/videoclipper.py funclip/utils/subtitle_utils.py
git diff --check
```

Only run provider-specific optional checks when the task touches that provider
surface. For LiteLLM changes, install the optional dependency first:

```bash
pip install 'litellm>=1.83.0'
python3 -m pytest -q tests/test_litellm_api.py
```

## Issue and pull request template expectations

Template checks protect maintainer throughput as part of release readiness:

- Bug reports should request FunClip version or commit, FunASR version, OS,
  Python version, installation method, browser/Gradio version when relevant,
  hardware/CUDA when relevant, input type/duration/language, ASR model and
  hotwords, LLM provider/model if semantic clipping is involved, reproducible
  steps, expected behavior, actual behavior, logs/traceback, and screenshots or
  clips when useful.
- Feature requests should capture the use case, proposed behavior, current
  workaround, input/output examples, user impact, and related references.
- The pull request template should keep `Summary`, `User impact`, `Validation`,
  `Screenshots or clips`, and reviewer notes visible.
- Issue template config should keep blank issues disabled and route broad ASR,
  deployment, or model-selection questions to FunASR documentation or
  discussions rather than release packaging.
