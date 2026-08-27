# Metadata, Benchmark, Release, and Integrity Reference

## Purpose

Use this for `metadata.json`, `skills.sh.json`, `benchmarks.json`, signature drift, content-integrity checks, skill cards, eval artifacts, and release gates.

## Metadata Generation

The canonical inventory lives at `.github/scripts/marketplace/metadata.json`. The public index at root `skills.sh.json` is derived from it and grouped by catalog subdomain.

The generator discovers `skills/**/SKILL.md`, parses frontmatter, maps registered skills to `components.d`, carries forward valid existing metadata, and uses constrained AI enrichment only when required fields cannot be filled deterministically. Pull requests run deterministic check mode:

```bash
python3 .github/scripts/marketplace/generate-skill-metadata.py --check --no-ai
```

Manual or post-sync regeneration can use AI enrichment in CI when configured with repository secrets/variables. Do not put inference API keys in prompts, local logs, or generated skill content.

## Benchmark Aggregation

Each published skill should include a `BENCHMARK.md` report. Root `benchmarks.json` is generated from those per-skill reports and is checked in PRs:

```bash
python3 .github/scripts/aggregate_benchmarks.py --check
```

If aggregation fails, inspect the changed `BENCHMARK.md` format before editing the aggregator. Two benchmark report layouts are supported by the current parser.

## Signature And Artifact Gates

Every catalog skill must include:

- root `skill.oms.sig`;
- `skill-card.md`;
- eval JSON in an accepted eval/evals/benchmark location;
- `BENCHMARK.md`.

The sync workflow detects three signature-related conditions:

1. Missing root signature: preserve the prior signed version when possible, otherwise drop a new unsigned skill.
2. Signature drift: content changed but `skill.oms.sig` did not; revert or drop until the source team reruns signing.
3. Signature mismatch: incoming signature changed but signed file hashes do not match; revert or drop until the source repo is internally consistent.

The daily and PR integrity workflow recomputes hashes listed in `skill.oms.sig` and fails on mismatches or missing signed files.

## Release Trust Pipeline

The catalog release story uses layered evidence:

1. SkillSpector security scan inside SkillEvaluator/NVSkills-Eval Tier 1.
2. Semantic deduplication when configured.
3. Live agent evaluation with and without the skill; results captured in `BENCHMARK.md`.
4. Human-readable `skill-card.md` with owner, use case, risks, dependencies, output shape, references, and version.
5. Detached OMS signature (`skill.oms.sig`) over the exact reviewed directory.
6. Public verification using `model_signing verify certificate` and the NVIDIA agent root certificate.

A signature proves integrity of a reviewed artifact; it does not by itself prove safety or usefulness.

## Safe Local Profiles

Use the bundled script to plan or run check-only profiles:

```bash
python <this-skill>/scripts/run_catalog_checks.py --repo-root <repo> --profile metadata --plan
python <this-skill>/scripts/run_catalog_checks.py --repo-root <repo> --profile integrity --plan
python <this-skill>/scripts/run_catalog_checks.py --repo-root <repo> --profile pre-pr --plan
```

`--execute` runs commands that exist in the checkout. Prefer `--plan` first on dirty worktrees.
