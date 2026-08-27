# Contributor workflows

Use these workflows when reviewing or making repository-maintenance changes. They are intentionally offline-first and maintainer-specific.

## 1. Classify the change before editing

Pick the smallest matching class:

- prompt/gallery entry or category maintenance;
- README/docs wording or install guidance;
- CLI flag/default/behavior change;
- package metadata or console-script change;
- plugin metadata change;
- release, support, security, or contribution policy update;
- generated runtime skill maintenance.

If the task is to generate or edit an image, stop and route to the CLI/API or prompt-gallery sub-skill instead of using this maintenance workflow.

## 2. Prompt/gallery entry workflow

Use for adding, removing, moving, or correcting gallery entries.

1. Read the actual prompt text before choosing or changing a category. Do not categorize from only a filename or title.
2. Place new gallery images under `docs/<category-slug>/<short-slug>.png` unless maintaining an existing legacy/community index location.
3. Update `README.md` and `README.zh.md` together:
   - same entry order;
   - same image path;
   - same numbering;
   - matching category/index counts;
   - one divider between entries, no duplicate dividers.
4. Update `skills/gpt-image/references/gallery.md` when category ranges, counts, or links change.
5. Update the matching `skills/gpt-image/references/gallery-<category>.md` file with prompt text, path, metadata, and attribution.
6. If the entry belongs to the community-picks data set, update both `docs/community-prompt-picks.json` and `docs/community-prompt-index.md`.
7. Preserve attribution visibly:
   - `Original` for repo-generated examples;
   - `Author + Source` for outside-source prompts.
8. Re-run the offline content checker and inspect the docs image inventory for accidental bloat or misplaced root images.

## 3. README/docs workflow

Use for install text, usage examples, selected showcase wording, contribution links, and bilingual public docs.

1. Decide whether the change is English-only, Chinese-only, or public behavior that must be mirrored in both READMEs.
2. Keep command examples consistent with `pyproject.toml` and `src/gpt_image_cli/cli.py`.
3. Avoid promising automatic setup, global/shared installs, or secret-file edits unless the project intentionally supports that behavior.
4. Keep README links to skills, references, contribution, security, and support files repository-relative.
5. For gallery prose edits, verify that headings, anchors, image paths, and counts still match the gallery references.

## 4. CLI/package workflow

Use for parser flags, defaults, endpoint routing, dependency changes, entry points, or public command behavior.

1. Edit `src/gpt_image_cli/cli.py` for CLI behavior; edit `src/gpt_image_cli/__init__.py` only when the package wrapper changes.
2. Preserve the package expectation unless intentionally changing it:

   ```toml
   [project]
   name = "gpt-image-cli"

   [project.scripts]
   gpt-image = "gpt_image_cli.cli:main"
   ```

3. Update `pyproject.toml` for dependency, Python-version, keyword, URL, version, or console-script changes.
4. Update README usage tables and examples in both languages when public behavior changed.
5. Update `skills/gpt-image/SKILL.md` and generated CLI/API references so agents use the current flags and safety policy.
6. Add a `CHANGELOG.md` note for visible behavior, packaging, or compatibility changes.
7. Run `python3 -m py_compile src/gpt_image_cli/cli.py src/gpt_image_cli/__init__.py` and `uv run gpt-image --help` when the parser/package surface changed.

## 5. Plugin metadata workflow

Use when changing package discovery, marketplace text, version, homepage/repository links, keywords, or install guidance.

1. Update `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` together when plugin discovery text changes.
2. Keep plugin description, package description, README install text, and changelog consistent.
3. Check that plugin metadata remains valid JSON.
4. Do not add runtime-specific generated-agent files as part of this repository-maintenance sub-skill.

## 6. Release, support, and security workflow

Use for policy files and contributor templates.

- `CHANGELOG.md`: user-visible changes, releases, compatibility notes.
- `CONTRIBUTING.md`: gallery rules, attribution rules, verification expectations, PR notes.
- `SECURITY.md`: private vulnerability reporting and secret-handling policy.
- `SUPPORT.md`: how users should request help and what environment details to include.
- `.github/PULL_REQUEST_TEMPLATE.md`: reviewer checklist and required PR notes.
- `.github/ISSUE_TEMPLATE/*.yml`: structured bug/gallery triage fields.

Keep security/support text concise. Never ask users to paste API keys, private images, or raw API responses containing secrets.

## 7. Safe pre-PR checks

Recommended offline sequence:

```bash
git diff --check
python3 -m py_compile src/gpt_image_cli/cli.py src/gpt_image_cli/__init__.py
python skills/disco/gpt-image-cli/sub-skills/repo-maintenance/scripts/check_repo_content.py .
```

Use this only for help/packaging surface validation, not image generation:

```bash
uv run gpt-image --help
```

Before opening a PR, summarize:

- changed surface and reason;
- files updated;
- gallery counts/paths checked, if relevant;
- metadata/docs/policy mirrors checked;
- commands run and whether they were offline;
- known gaps, especially any live API behavior intentionally not tested.

## 8. Anti-patterns

Avoid these common maintenance mistakes:

- changing only one README for public-facing behavior;
- adding an image under `docs/` root when it should live in a category folder;
- updating a README gallery entry without updating `skills/gpt-image/references/gallery*.md`;
- changing CLI flags without updating the runtime skill and README examples;
- running real image-generation calls as a maintainer check;
- printing or committing API keys, `.env` content, private prompts, or private images;
- writing generated-skill text that depends on a particular local checkout path.
