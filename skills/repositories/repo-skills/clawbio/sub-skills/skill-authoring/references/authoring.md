# Authoring workflow

This reference turns the repository's template, `/new-skill` command, development
rules, and contributor guide into a repeatable scaffold-to-tested workflow.

## 1. Establish the contract before coding

Write down, in one paragraph, the single user task. Record:

- a lowercase-hyphenated folder/name and the lowercase-underscore Python module;
- accepted input formats, required columns/fields, encoding/build assumptions, and
  whether the skill consumes a file, a query, or both;
- primary output (`report.md` for report-producing skills), structured outputs,
  conditional artifacts, and the exact output tree;
- the authoritative databases, papers, thresholds, and algorithms (do not invent
  any during implementation);
- a synthetic demo and at least one malformed/empty input case;
- the CLI alias, whether a static `SKILLS` registration is needed, and whether
  deterministic chat routing needs `INTENTS.json`.

One skill should do one job. Split unrelated computation, routing, and reporting
rather than hiding several tasks behind a broad trigger.

## 2. Frontmatter, naming, and triggers

Start from `templates/SKILL-TEMPLATE.md`, not a blank document. A contributor
skill's frontmatter must contain the template's top-level `name`, `description`,
and `license`, plus the documented metadata fields for version, author, domain,
tags, inputs, outputs, dependencies, demo data, endpoints, and OpenClaw routing.
The `name` is exactly the folder name. Use MIT or Apache-2.0 for the skill's own
code unless a PR explains an exception; declare model and reference-data licenses
separately under metadata when applicable.

The generated operating sub-skill has its own deliberately smaller frontmatter
contract; do not copy that contract into a normal ClawBio contributor skill.

Make discovery explicit:

- include at least five natural-language “Fire this skill when” phrases covering
  synonyms, abbreviations, file-type language, and common user wording;
- include at least two “Do NOT fire when” cases naming adjacent skills or
  look-alikes;
- repeat the strongest phrases in `metadata.openclaw.trigger_keywords` (the
  formal audit requires at least three);
- distinguish an input format from a scientific intent: a VCF alone is not enough
  to route every VCF analysis to the same skill;
- avoid generic triggers such as “biology”, “analyze data”, or “report”.

## 3. Scaffold and write the specification

Create `skills/<name>/`, `tests/`, and, when useful, `examples/`. Fill every
required template section rather than deleting sections to make the document
shorter. The high-signal sections are:

- **Trigger**: loud fire/do-not-fire lists and disambiguation;
- **Scope**: one task only;
- **Input Formats**: required fields, formats, examples, and validation failures;
- **Workflow**: numbered steps, with prescriptive steps for fragile operations and
  flexible guidance only for narrative interpretation;
- **CLI Reference/Demo**: exact direct and registered commands;
- **Example Output/Output Structure**: realistic synthetic values and only files
  actually emitted;
- **Gotchas**: at least three concrete model failure patterns;
- **Safety/Agent Boundary**: local-first handling, disclaimer, traceable science,
  and the rule that the agent dispatches while the script executes;
- **Integration/Maintenance/Citations**: chaining, staleness signals, and sources.

The report disclaimer must be exactly:

> ClawBio is a research and educational tool. It is not a medical device and does
> not provide clinical diagnoses. Consult a healthcare professional before making
> any medical decisions.

If a skill writes any report, test that text rather than relying on a prose promise.

## 4. Red/green tests and synthetic demo

Write tests before implementation. The focused suite should cover the expected
path, demo mode, output structure, disclaimer, malformed input, and empty input;
add safety and overwrite cases when relevant. Run the new tests and observe the
red failure before adding implementation. Then implement the smallest safe path,
run green, refactor, and run green again. Do not claim a test cycle when tests
were only written but never run.

Demos are synthetic and deterministic. Include at least three to five entries that
exercise the important branches, label them as not real patient data, and ensure
`--demo --output <dir>` writes the documented bundle without network access unless
public test data is an explicit, documented exception. Never use a contributor's
personal genomic data in fixtures.

Typical focused commands are:

```bash
python -m pytest skills/<name>/tests/ -v
python skills/<name>/<name_with_underscores>.py --demo --output /tmp/<name>-demo
clawbio run <registered-alias> --demo --output /tmp/<name>-runner-demo
```

Use the direct command before registration. Use the runner command only after the
static registry entry and allowlist are correct. `--help` is a useful low-cost
contract check for both commands.

## 5. Registration and catalog distinctions

Keep these states separate in the handoff:

1. **SKILL.md only**: agent-readable and discoverable from the skills directory,
   but not executable through `clawbio run`.
2. **Executable but unregistered**: direct Python invocation and catalog fallback
   demo may work, but there is no stable `clawbio run <alias>` contract.
3. **Static CLI registration**: add a `SKILLS` entry in the package's CLI registry with
   the real script path, demo arguments, description, and exact `allowed_extra_flags` (plus
   boolean flags where needed). The alias may differ from the folder; record both.
4. **Intent descriptor**: `INTENTS.json` adds deterministic phrase/slot routing.
   A descriptor without a safe executable route can be discoverable but returns
   `needs_registration`; it does not replace a normal CLI registration decision.

For every flag accepted from a runner or descriptor, add it to the narrow per-skill
allowlist. Never bypass filtering by passing `--input`, `--output`, or `--demo` as
an extra flag. Do not add a catch-all passthrough. Treat file, config, credential,
reference, and model-path options as sensitive unless the runner's explicit design
supports them safely.

After changing SKILL.md YAML, run the target checkout's documented catalog-
generation command. Review the generated diff and check the entry's alias,
maturity, script/tests/demo booleans, trigger keywords, licenses, and demo
command. The catalog is generated output; fix its source inputs and regenerate
instead of hand-editing `skills/catalog.json`.

## 6. Contributor handoff and PR

A PR should keep one skill's change focused, use a branch named for the skill, and
include the test commands and demo output. Run the focused suite and the full
`python -m pytest -v` suite when feasible; verify `clawbio list` after registration. Regenerate the catalog when frontmatter changes. Keep paths portable
with `pathlib`, support Python 3.10+ in skill code where the repository contract
requires it, avoid hardcoded absolute paths and credentials, and warn before
overwriting an output directory.

The PR description should state scope, inputs/outputs, dependencies/licences,
safety boundaries, red/green evidence, demo command/result, and any network or
backend limitation. External correctness or benchmark interpretation belongs in
validation evidence, not in this authoring checklist.
