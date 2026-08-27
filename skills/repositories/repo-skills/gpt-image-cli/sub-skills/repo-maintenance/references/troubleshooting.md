# Troubleshooting

This page covers maintainer-facing repository drift. For normal image generation, editing, or prompt crafting, route to the CLI/API or prompt-gallery sub-skill instead.

## Packaging or entry-point drift

**Symptoms**

- `gpt-image --help` is missing or shows stale flags.
- `python -m gpt_image_cli.cli --help` fails.
- The package installs but no `gpt-image` console command appears.
- README examples describe flags that the parser no longer accepts.

**Check**

- `pyproject.toml` still has project name `gpt-image-cli` and console script `gpt-image = "gpt_image_cli.cli:main"`.
- `src/gpt_image_cli/cli.py` contains the parser and `main()` entry point.
- `src/gpt_image_cli/__init__.py` wrapper still delegates correctly if used.
- README parameter tables and `skills/gpt-image/SKILL.md` agree with parser flags.

**Fix**

Restore the intended entry point or update all public docs and skill references when the command intentionally changed. Re-run `python3 -m py_compile ...`, the bundled content checker, and `uv run gpt-image --help` for CLI-surface changes.

## Stale gallery index

**Symptoms**

- Category links in `skills/gpt-image/references/gallery.md` point to missing files.
- Category ranges or counts do not match the actual prompt files.
- `README.md` and `README.zh.md` list different image paths, numbering, or order.
- A prompt appears in the README but not the reference gallery, or the reverse.

**Check**

- `skills/gpt-image/references/gallery.md` category table.
- The relevant `skills/gpt-image/references/gallery-<category>.md` file.
- Both README gallery sections and the top gallery size/count text.
- `docs/community-prompt-picks.json` and `docs/community-prompt-index.md` for community-picks entries.

**Fix**

Update the index and the category file in the same change. Keep README entries mirrored across languages. Preserve `Original` or `Author + Source` attribution markers.

## Accidental API calls or keys in checks

**Symptoms**

- A maintainer check attempts an image generation/edit request.
- A script requires `OPENAI_API_KEY` for a content-only check.
- Logs, issue text, or docs reveal key values, `.env` contents, private prompts, or private images.

**Check**

- Shell commands in the PR description and docs.
- New or changed scripts under `scripts/` or generated skill trees.
- README examples for commands that could be mistaken for verification steps.

**Fix**

Keep content checks offline. Use `--help`, syntax checks, and static inventory scripts for maintenance verification. If live image behavior must be tested, treat it as a separate explicitly approved runtime task and never print secrets.

## Large image asset bloat

**Symptoms**

- A PR adds many or very large images unexpectedly.
- New images appear directly under `docs/` instead of category folders.
- Gallery pages become slow or noisy.

**Check**

Run the bundled checker and inspect its docs image inventory:

```bash
python skills/disco/gpt-image-cli/sub-skills/repo-maintenance/scripts/check_repo_content.py . --json
```

Look at total image count, total bytes, top-level directory counts, largest images, and root-level docs images.

**Fix**

Keep only representative gallery images, compress oversized assets, move new assets into the correct category folder, and update every path reference after moving files.

## Runtime-skill path mistakes

**Symptoms**

- Generated skill text links to a machine-specific checkout path.
- A runtime skill points to review reports, test-case artifacts, or other non-runtime files.
- Edits intended for the published `skills/gpt-image/` skill land in the generated `skills/disco/gpt-image-cli/` tree, or vice versa.

**Check**

- `skills/gpt-image/` is the repo-owned published runtime skill for normal GPT Image use.
- `skills/disco/gpt-image-cli/` is the generated DisCo operating skill tree.
- Links inside generated public files are repository-relative.

**Fix**

Rewrite links to be relative to the runtime file location. Keep review notes, verification reports, and synthetic test cases outside the runtime skill tree. Do not add import/export instructions when the task is only repository maintenance.

## Plugin metadata drift

**Symptoms**

- Plugin marketplace text promises different behavior from README install text.
- Plugin version, homepage, repository, keywords, or description no longer match package metadata.
- Install/update instructions mention a stale command or folder name.

**Check**

- `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` are valid JSON.
- `pyproject.toml` description/keywords and README install sections tell the same story.
- `CHANGELOG.md` records visible discovery or packaging changes.

**Fix**

Update plugin JSON, README install text, package metadata, and changelog together when discovery changes. Re-run JSON parsing and offline content checks.

## Quick recovery pattern

1. Identify the owning surface from `repository-layout.md`.
2. Fix the smallest broken file first.
3. Update all mirrors that describe that surface.
4. Run the no-network checker and any syntax/help checks relevant to the changed surface.
5. Document untested live behavior separately instead of hiding it in maintainer verification.
