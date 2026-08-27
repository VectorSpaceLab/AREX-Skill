# Validation and packaging

This reference covers authoring checks only. Scientific correctness, benchmark
interpretation, and native backend evidence are handed to `validation-safety`.

## Read-only static check

Use the bundled checker with an explicit repository root and, preferably, the
specific skill being changed:

```bash
# Run from the generated ClawBio skill root; point --root at the target checkout.
python sub-skills/skill-authoring/scripts/check_skill_assets.py \
  --root <ClawBio-checkout> --skill <ClawBio-checkout>/skills/<name> \
  --catalog <ClawBio-checkout>/skills/catalog.json
python sub-skills/skill-authoring/scripts/check_skill_assets.py --help
```

It checks, without writing files:

- frontmatter delimiters, name/folder alignment, description, and core sections;
- executable files, tests, demo evidence, and output-contract signals;
- static `SKILLS` aliases and script paths when `clawbio/cli.py` is present;
- catalog count, names, script/test/demo booleans, and registered alias/path
  consistency when `skills/catalog.json` is supplied;
- descriptor JSON schema, identifiers, routes, safe local paths, slots, and
  allowlisted/blocked args.

The checker is a fast static gate, not a substitute for running the skill or
reviewing domain science. It has no write mode and no option that regenerates the
catalog.

## Focused and integrated tests

Use the smallest applicable command first:

```bash
python -m pytest skills/<name>/tests/ -v
python -m pytest tests/test_generate_catalog.py tests/test_core_skill_intents.py -v
python -m pytest clawbio/tests/test_packaging.py tests/test_cli_smoke.py -v
python -m pytest -v
```

The catalog, intent, packaging, and CLI suites are native candidates and are
intentionally deferred until the whole generated skill is integrated. A focused
skill test passing does not prove static registration, descriptor routing, or wheel
inclusion.

Required red/green evidence for implementation changes:

1. write/update tests for expected behavior and failure behavior;
2. run the focused tests and record the red result;
3. implement the smallest safe change;
4. rerun focused tests green;
5. refactor only with a final green run;
6. run the checker, demo, and relevant native suites.

For a pure `SKILL.md` or descriptor change, still run static validation and the
closest routing/catalog tests; do not fabricate a red phase for code that has no
new executable behavior.

## Registration and catalog generation

A static CLI registry entry must point to an existing script, include
`demo_args`, and expose only the skill's intended extra flags through
`allowed_extra_flags` or `allowed_extra_flags_without_values`. Core `--input`,
`--output`, and `--demo` remain runner-owned. Run:

```bash
clawbio list
clawbio run <alias> --help
clawbio run <alias> --demo --output /tmp/<alias>-demo
```

When YAML frontmatter changes, run the target checkout's documented catalog-
generation command, then inspect the generated catalog diff. The generator derives
aliases from
the static registry, derives script/test/demo state from files, and carries trigger,
license, dependency, maturity, and chaining metadata. If the result is wrong, fix
the SKILL.md, source registry, exclusions, or generator input and regenerate. Do
not hand-edit a generated entry because it will be overwritten on the next run.

## Wheel/package layout

The package build uses `hatch_build.py` to force-include a curated subset under
the `clawbio/` namespace while retaining the repository's root `skills/` layout.
For every skill, logic/source suffixes such as `.md`, `.py`, `.yaml`, `.yml`, `.sh`,
`.cff`, `.toml`, and `.cfg` are included. Non-headline `.json`, `.csv`, `.tsv`, and
`.txt` data are included only when at most 256 KiB; headline skills receive their
full demo payload. `examples/` is included wholesale. Cache directories, bytecode,
and editor files are excluded.

Therefore:

- keep required scripts, references, descriptors, YAML, and shell helpers in the
  skill subtree with supported suffixes;
- keep non-headline fixtures small, synthetic, and reproducible;
- do not rely on large ignored data silently appearing in a wheel;
- use portable `pathlib` resolution and write outputs outside read-only package
  data; never assume the checkout is writable after installation;
- add a packaging test when a new file type or packaging rule is necessary, and
  inspect the built wheel when inclusion is material to the skill.

The package project requires Python >=3.11, while the repository's contributor
skill guidance targets Python 3.10+ for skill code. Follow the actual project
matrix and any skill-specific dependency declaration; do not broaden claims based
on one local interpreter.

## PR expectations

Keep one skill per PR and include:

- exact scope, trigger/do-not-trigger cases, inputs, outputs, dependencies, and
  third-party model/data licences;
- synthetic demo command and representative output or a documented limitation;
- focused test command plus red/green result, and relevant full/native test results;
- `clawbio list`/runner evidence for registered skills;
- catalog regeneration evidence when metadata changed;
- local-first behavior, overwrite warning, disclaimer, and credential/network notes;
- unresolved backend or scientific validation gaps, which belong in the handoff and
  must not be hidden by claiming “validated.”

Use permissive licensing for wrapper code unless an exception is explained. Do not
claim that the wrapper's MIT licence relicenses third-party weights or data.
