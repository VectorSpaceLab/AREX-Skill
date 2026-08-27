# Release packaging troubleshooting

Use this guide when release archives, release contract tests, templates, checksums,
or the tag-based GitHub release workflow fail.

## Fast triage commands

```bash
python -m pytest -q tests/test_release_contract.py
python -m pytest -q tests/test_release_contract.py -k <failing-test-name>
# From the generated funclip skill root:
python sub-skills/release-packaging/scripts/build_release_assets.py \
  --repository . --ref HEAD --output-dir dist
```

If the failure is about issue/PR templates or community links, add:

```bash
python -m pytest -q \
  tests/test_github_templates.py \
  tests/test_community_links.py \
  tests/test_canonical_qwenaudio_links.py
```

## Release contract failure map

| Symptom or failing area | Likely cause | Fix |
| --- | --- | --- |
| `VERSION must be semantic x.y.z` | `VERSION` is blank, prefixed with `v`, or has a non-`x.y.z` suffix. | Set `VERSION` to plain semantic form such as `2.1.1`; put the `v` only in the Git tag. |
| README release routes are out of sync | One of `README.md` or `README_zh.md` still references an old tag, archive name, or missing `SHA256SUMS`. | Update both readmes to the same release page, `FunClip-X.Y.Z.tar.gz`, `FunClip-X.Y.Z.zip`, and `SHA256SUMS`. |
| Missing release notes | `docs/releases/vX.Y.Z.md` was not created or the workflow tag does not match `VERSION`. | Create the release note file for the exact tag and keep the tag equal to `v${VERSION}`. |
| Release notes asset-boundary test fails | Notes omit install/runtime boundaries or important dependency/model facts. | Mention archive names, `SHA256SUMS`, dependency install path, that model weights are not bundled, and any release-specific runtime constraints. |
| Workflow contract test fails | `.github/workflows/release.yml` changed away from the expected tag, pinned-action, draft-release, asset verification, or `pytest==8.3.5` contract. | Restore the tag trigger, pinned action SHAs, `tests/test_release_contract.py` step, builder step, `gh release view/create/edit/upload`, digest verification, `--verify-tag`, draft flow, and `--draft=false` only after verification. |
| Template tests fail | Issue or PR templates no longer collect required repro, impact, validation, or screenshot/clip fields. | Re-add the fields listed in the template expectations section of `release-workflow.md`. |

## Archive builder errors

### `release ref must resolve to a commit`

The builder rejects tree, blob, or otherwise non-commit refs. Use a commit SHA,
branch, or tag that resolves to a commit:

```bash
git rev-parse --verify <ref>^{commit}
# From the generated funclip skill root:
python sub-skills/release-packaging/scripts/build_release_assets.py \
  --repository . --ref <commit-or-tag> --output-dir dist
```

### `release archive is missing: ...`

The selected commit does not contain one or more required root files:
`VERSION`, `README.md`, `requirements.txt`, or `LICENSE`. Add or restore the
missing tracked file before rebuilding. Do not patch the archive by hand.

### `release archive contains a path outside FunClip-X.Y.Z/`

The archive was not produced with the expected versioned prefix, or a nonstandard
archive command bypassed the release builder. Rebuild with the bundled builder so
all files are under `FunClip-X.Y.Z/`.

### `release archive contains generated metadata: ...`

The archive contains tracked generated files such as `.git`, `__pycache__`,
`.pyc`, or `.pyo` paths. Remove generated metadata from the tracked source,
commit the cleanup, and rerun the builder from that commit.

### `tar.gz and zip archives contain different files`

The release contract requires both archives to contain the same tracked member
set. Rebuild both archives from the same commit with the bundled builder and do
not mix assets from different commits or manually edited archives. If the mismatch
persists, compare member lists to find the divergent path before publishing.

## SHA256SUMS and asset verification

- `SHA256SUMS` should contain exactly one line for the tar archive and one line
  for the zip archive, with two spaces between digest and filename.
- Verify local assets from the dist directory:

```bash
cd dist
sha256sum -c SHA256SUMS --ignore-missing
```

- If GitHub release asset verification fails, compare each asset by name, byte
  size, and digest. The workflow expects release API digests in `sha256:<hex>`
  form.
- If a release is still a draft, re-upload assets with `--clobber`, verify them,
  and only then publish. If it is already published, do not replace or republish
  assets without explicit maintainer authorization.
- If the release is immutable, the safe path is to verify that existing assets
  match. If they do not match, stop and ask the maintainer for the desired policy;
  do not force-delete or recreate a release from this sub-skill.

## Dependency and validation environment issues

- `pytest: command not found` or `No module named pytest`: install the release
  test dependency, then rerun the focused check:

```bash
python -m pip install --disable-pip-version-check pytest==8.3.5
python -m pytest -q tests/test_release_contract.py
```

- `No module named litellm` while running provider tests: this is optional and
  belongs to provider-route validation, not core release archive packaging. Only
  install it when the change actually touches LiteLLM provider behavior:

```bash
pip install 'litellm>=1.83.0'
python3 -m pytest -q tests/test_litellm_api.py
```

- If broader maintainer commands fail in ASR, Gradio, clipping, or provider code,
  route the debugging task to the owning sub-skill unless the failure is only a
  release-doc, checksum, workflow, or template contract issue.
