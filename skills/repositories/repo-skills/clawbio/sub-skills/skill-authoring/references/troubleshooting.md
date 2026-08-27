# Troubleshooting authoring failures

Use the smallest source-of-truth fix, rerun the read-only checker, then rerun the
focused test or generator. Do not patch generated artifacts blindly.

## Stale or mismatched catalog

**Symptoms:** `tests/test_generate_catalog.py` reports a count/entry mismatch, the
catalog has an old description or trigger, or a new skill is absent.

1. Confirm the skill has `SKILL.md` under `skills/<name>/` and is not intentionally
   excluded by the generator.
2. Check YAML frontmatter and the static registry/descriptor source, not the JSON
   first.
3. Run the target checkout's documented catalog-generation command.
4. Inspect `git diff -- skills/catalog.json`; confirm `skill_count`, alias,
   `demo_command`, `has_script`, `has_tests`, `has_demo`, triggers, licences, and
   maturity evidence.
5. Run `python -m pytest tests/test_generate_catalog.py -v`.

If the generated result is still wrong, diagnose the parser or source metadata and
fix that source. Never manually make one catalog entry “look right”: the next
regeneration will erase it and may conceal a registry problem.

## Missing script or runner alias

**Symptoms:** direct demo works but `clawbio run <alias>` says unknown skill or
script not found; catalog `cli_alias` is null or points elsewhere.

- Confirm the script exists at the path encoded by the static `SKILLS` entry and
  that its working-directory assumptions are portable.
- Confirm the alias is unique and distinguish it from the folder name. A registered
  alias can be `pharmgx` while the folder is `pharmgx-reporter`.
- Ensure `demo_args` are valid for the script and do not contain a stale absolute
  checkout path.
- Add only the required extra flags to `allowed_extra_flags`; do not solve a missing
  registration by passing arbitrary flags through the runner.
- Run `clawbio list`, `clawbio run <alias> --help`, and a demo.
- Regenerate the catalog after source changes and rerun catalog tests.

An executable but unregistered skill may still be run directly and may receive a
catalog fallback demo command. That is not evidence that `clawbio run` is supported.

## Invalid frontmatter or failed conformance

**Symptoms:** parser returns empty metadata, an agentskills validator rejects the
file, or the checker reports missing fields/sections.

- Start over from `templates/SKILL-TEMPLATE.md`; keep `---` delimiters at the first
  line and closing delimiter after the YAML.
- Set `name` exactly to the lowercase-hyphenated directory name.
- Keep `description` specific and scalar; avoid an accidental body heading before
  the closing delimiter. Use the required double-quoted description only for the
  generated operating sub-skill contract, not as a reason to remove contributor
  metadata from normal skills.
- Restore metadata for version, author, domain, tags, inputs, outputs,
  dependencies, demo data, endpoints, and OpenClaw triggers.
- Restore all audited sections: Trigger, Scope, Workflow, Example Output, Gotchas,
  Safety, Agent Boundary, Chaining Partners/Integration, and Maintenance.
- Keep output trees honest and test the exact disclaimer.

Run the checker with `--help` and an explicit `--root`; it is read-only. Fix YAML or
Markdown source, then regenerate the catalog if metadata changed.

## Descriptor ignored or `needs_registration`

**Symptoms:** an intent route never matches, a descriptor is not loaded, or a plan
returns `needs_registration`.

- Validate JSON syntax and exact `schema` value
  `clawbio.skill_intents.v1`.
- Ensure `routes` and each `plan` are non-empty, `intent_id`/skill/slot names use
  conservative identifiers, and trigger terms are specific.
- Check that `INTENTS.json` is in the skill directory and that any declared
  entrypoint/script, input, and output stays within that directory.
- A descriptor-only route without an executable local entrypoint is intentionally
  not executable. Add a safe conventional/declared entrypoint or register the
  target skill; do not point outside the skill subtree.
- Test a normal phrase, a missing-required-slot phrase, and an explicit demo phrase.
  Demo text must be explicit; a requested mode alone is not enough.

## Descriptor args filtered or dropped

**Symptoms:** a route plans without an expected optional flag or warns that an arg
was skipped.

The planner accepts only literal args for a statically registered skill's explicit
allowlist. It blocks core controls and sensitive/path-oriented fragments, including
input/output/profile/demo/help and credentials/config/reference/data-path flags.
Use `input` or `input_template` for request data, and a confined `output` path for
outputs. Add a narrowly justified user-facing value flag to the static registry
allowlist only after tests; never add a catch-all.

## Package missing a skill file

**Symptoms:** source checkout works but an installed wheel lacks `SKILL.md`, a
script, a descriptor, or a reference.

- Check the file suffix against `hatch_build.py`'s logic/source and small-data rules.
- Keep non-headline fixture files at or below the small-data limit, or revise the
  packaging rule deliberately with a test and PR explanation.
- Confirm the sdist includes `skills/` and that the custom hook runs during build.
- Build/inspect the wheel, then run `clawbio/tests/test_packaging.py`.
- Do not add generated or private cache files merely to make an installed test pass.

## Test/demo failures

**Symptoms:** red tests persist, demo overwrites output, or the runner and direct
script disagree.

First reproduce with the focused command. Check input validation and output path
creation, then check the script's `--help` and direct demo. Ensure demos are
synthetic and deterministic, and that existing output triggers a warning rather
than silent overwrite. Keep the task open when a required backend, dependency, or
scientific assertion remains unresolved; report the gap instead of weakening the
check.
