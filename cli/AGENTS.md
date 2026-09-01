# CLI maintenance rules

## Provenance and release

The npm release runs from `cli/` and verifies the checked-in
`packages/coding-agent/UPSTREAM_MANIFEST.json` with:

```bash
npm run verify:provenance
```

This release check is local-only. It reads the current `cli` files and the
checked-in manifest; it does not read or infer a path to an external Pi
checkout.

The following directories are covered by the local provenance inventory:

```text
packages/coding-agent/src
packages/coding-agent/test
docs
examples
```

After intentionally changing an existing file in one of these directories, run
the local refresh before the final release verification:

```bash
npm run refresh:provenance
```

When intentionally adding a new DisCo-owned file, approve it explicitly:

```bash
npm run refresh:provenance -- --add-local docs/dynamic-workflows.md
```

Repeat `--add-local` for multiple new files. Review the manifest diff after the
refresh. The refresh must not silently absorb unknown files, accept missing
declared files, or change upstream hashes and mappings.

Use the full upstream workflow only when the Pi baseline or upstream mapping is
actually changing:

```bash
node scripts/upstream-provenance.mjs --write --upstream-root /path/to/pi
```

That workflow is separate from normal release. It requires an exact pinned Pi
repository/tag/commit and a clean upstream checkout because it reads upstream
files to rebuild the full manifest. Do not clean, restore, or otherwise modify
an external Pi checkout merely to release the current `cli` package.

`scripts/build-from-source-link.sh` is a build/link smoke workflow, not a full
release check. Before publishing, run `npm run prepublishOnly` or the release
dry-run and inspect the resulting package checks.

The AREX-Skill Git worktree does not have to be clean, and `git add`/`git commit`
are not technical prerequisites for npm release. Nevertheless, commit or tag
the reviewed release state before a real publish when possible so the published
package can be traced back to an exact source revision.
