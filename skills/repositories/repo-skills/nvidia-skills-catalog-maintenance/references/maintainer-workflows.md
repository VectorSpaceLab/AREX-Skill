# Maintainer Workflows

## Purpose

Use this reference for source-of-truth catalog edits: component onboarding, removal, README/doc updates, direct exceptions, and pull-request preparation.

## Onboard A New Product Or Skill

1. Confirm the source repo is public, under an NVIDIA-owned GitHub org, and has completed the required IP/license review.
2. Add or edit `components.d/<slug>.yml`. The slug should be lowercase kebab-case and should match the component file purpose.
3. For every skill entry, set:
   - `path`: source repo directory containing one skill `SKILL.md`.
   - `catalog_dir`: unique top-level directory name under the catalog `skills/` tree.
4. Ensure each source skill already carries required publication artifacts: `SKILL.md`, `skill-card.md`, `skill.oms.sig`, eval JSON, and `BENCHMARK.md`.
5. Regenerate/check local catalog outputs as appropriate:
   ```bash
   python <this-skill>/scripts/run_catalog_checks.py --repo-root <repo> --profile pre-pr --plan
   ```
6. In PR text, satisfy the onboarding affirmations: open-source clearance, license, no new third-party/license surprise, public NVIDIA source repo, and DCO sign-off.

## Remove Or Rename A Catalog Skill

1. Change the relevant `components.d/*.yml` entry first.
2. Decide whether the old `skills/<catalog_dir>` should be pruned, retained temporarily as a direct exception, or replaced by a renamed catalog directory.
3. If retaining without registration, add a documented `catalog-exceptions.yml` entry with reason, owner, and component.
4. Run orphan-prune logic only through the repository workflow or an explicit maintainer-approved local command. If more than the prune cap would be removed, stop for human triage.
5. Regenerate README and metadata outputs after the source change.

## Manual Or Direct-PR Skills

Use `.github/scripts/manual-components.yml` for temporary manually staged products that should appear in README tables even without public upstream sync. Use `catalog-exceptions.yml` for individual top-level skill directories that intentionally exist without a `components.d` registration.

Do not use either file to hide ordinary registration drift. Every exception needs a reason and an owner.

## README And Docs Maintenance

The root README is partially generated. Edit prose outside generated table markers normally, but rebuild generated tables after component changes. The docs site content lives in `docs/*.mdx`; navigation is in `fern/docs.yml`; local preview requires Node/npm and Fern only when editing docs.

Recommended local sequence for doc-only changes:

```bash
npm --version
# If Fern is installed and docs are in scope:
fern check
```

Do not require Fern for non-doc catalog maintenance.

## PR Readiness Checklist

Before handing off a PR:

- `git status --short` contains only intended changes.
- Component YAML parses and uses unique `catalog_dir` values.
- Generated README/metadata/plugin/benchmark files are either up to date or explicitly left for the scheduled automation with a reason.
- New or changed skills have `SKILL.md`, `skill-card.md`, eval JSON, `BENCHMARK.md`, and `skill.oms.sig`.
- The signature content matches signed files when `skill.oms.sig` changed or when content moved.
- The PR template's author confirmations and DCO sign-off are addressed.
- User-facing discovery or install requests have not been routed into this maintainer skill; they belong to `nvidia-skill-finder`.
