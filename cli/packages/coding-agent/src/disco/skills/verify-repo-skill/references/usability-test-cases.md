# Usability Test Cases

## Purpose

Read this reference after creating and integrating the generated skill files. It defines how to automatically generate usability test case directories that simulate realistic future users asking agents to use the generated repo skill.

The goal is not merely to create simple prompts. These cases are a validation
surface for routing, workflow depth, support workflows, troubleshooting,
self-containment, and consistency with repository evidence.

These test cases are review artifacts, not generated skill runtime content.
They live under the artifact root's `test-cases/` subtree. Keep them separate
from self-refine eval files, automatic verification reports, human-review
notes, publication checklists, prompt samples, staleness audits, and benchmark
notes, which belong under the artifact root's `reports/` subtree.

## Output Location

- If the user specified a test case, review, verification, or artifact output
  path, treat that path as the artifact root and write test case directories
  under `<artifact-root>/test-cases/`.
- Otherwise write them under
  `<repository-path>/skills/tests/<chosen-skill-id>/test-cases/`.
- Do not create standalone markdown case files such as `inference/basic-user.md`. Each case must be a directory with the required files below.
- Do not put verification reports, human-review notes, publication checklists,
  prompt samples, native verification reports, or eval notes in `test-cases/`;
  those belong under `<artifact-root>/reports/`.

Do not put these usability test cases inside the generated skill directory. Do
not link them from generated `SKILL.md` files as runtime documentation.

## Case Directory Format

Each test case is one directory named from the target skill area plus the scenario being tested:

```text
<artifact-root>/
  test-cases/
    index.md
    sub-skills/
      <sub-skill-id>/
        <scenario-slug>/
          user_request.txt
          README.md
          assertions.json
          fixtures/        # optional, only when the prompt needs small local inputs
    root/
      <scenario-slug>/
        user_request.txt
        README.md
        assertions.json
    integration/
      <scenario-slug>/
        user_request.txt
        README.md
        assertions.json
```

Use `sub-skills/<sub-skill-id>/<scenario-slug>/` when the case targets a
sub-skill, for example `sub-skills/inference/minimal-smoke-test/` or
`sub-skills/training/invalid-config-debugging/`. Use `root/<scenario-slug>/`
when the generated skill has no sub-skills or when the prompt primarily tests
root routing. Use `integration/<scenario-slug>/` for cross-sub-skill cases
created after whole-skill integration. Normalize every directory segment to
lowercase hyphen style, keep scenario slugs descriptive, and avoid generic names
such as `case-1` or `basic`.

A single sub-skill can and usually should have multiple case directories when it has multiple important scenarios. For example, `inference-minimal-smoke-test`, `inference-batch-inputs`, and `inference-missing-model-debugging` can all target the same `inference` sub-skill.

Every case directory must contain:

- `user_request.txt`: the exact future-user prompt. The whole file must be directly copyable into an agent input box. Do not add a title, markdown heading, metadata, explanation, "User Prompt:" label, or surrounding commentary.
- `README.md`: the reviewer-facing explanation of the case, including the user persona, scenario coverage, expected successful behavior, failure signals, and any important notes about why the case should trigger the generated skill.
- `assertions.json`: machine-readable assertions used during self-refine and
  review. Assertions must be specific enough to grade with `PASS` or `FAIL`
  from a future agent response or from direct inspection of generated skill
  files.

Case directories may contain a `fixtures/` directory when small inputs make the
prompt realistic, such as a tiny JSONL file, a minimal YAML config, a short
CSV, or an intentionally invalid example. Keep fixtures safe, small, and
publishable. Do not include private data, large files, model weights, generated
caches, or source-repo files copied wholesale only to make a test pass.

Use this `assertions.json` shape:

```json
{
  "schema": "disco.usability-case.v1",
  "target_skill_area": "sub-skill-or-root-id",
  "target_capability": "short capability name",
  "difficulty": "basic | intermediate | advanced | troubleshooting",
  "evidence_basis": [
    "README.md",
    "examples/infer.py",
    "tests/test_infer.py"
  ],
  "expected_skill_files": [
    "sub-skills/inference/SKILL.md",
    "sub-skills/inference/references/workflows.md",
    "sub-skills/inference/scripts/check_input.py"
  ],
  "assertions": [
    "The response routes to the inference sub-skill.",
    "The response validates the input schema before running inference.",
    "The response uses or references the bundled check_input.py helper.",
    "The response does not tell the user to open examples/infer.py from the original repo checkout.",
    "The response explains the documented missing-column error."
  ]
}
```

`evidence_basis` paths should be relative source repo evidence paths when they
are safe to record as review artifacts. `expected_skill_files` paths must be
relative to the generated runtime skill directory and should resolve inside
that directory.

## Default Generation Strategy

If the user explicitly asks for a specific type, number, format, role, workflow, or difficulty of cases, follow that request while preserving the required case-directory shape unless the user explicitly overrides it. Otherwise use this default strategy.

Create enough test cases to exercise the generated skill's actual surface area:

- For small single-workflow repos, create at least 4-6 case directories.
- For medium repos with several sub-skills, create roughly 2-4 case directories per major sub-skill.
- For large repos, create a broad representative set across all major user-facing capabilities identified in the coverage/depth matrix. Do not create hundreds of cases; prioritize coverage of distinct workflows, CLIs, APIs, data formats, configuration paths, and troubleshooting situations.
- For every generated sub-skill, create one or two new difficult synthetic case
  directories under `test-cases/sub-skills/<sub-skill-id>/` in addition to any
  cases copied or directly adapted from original repo tests/examples. These
  synthetic cases must be grounded in repo evidence but should go beyond the
  original tests by combining edge conditions, error recovery, constraints,
  fixtures, API/CLI specificity, or support workflow requirements.
- After all sub-skills are integrated, create one or two integrated difficult
  case directories under `test-cases/integration/`. Prefer scenarios adapted
  from original repo tests/examples that cross multiple capabilities. If the
  repo has no suitable integrated native candidate, synthesize a cross-skill
  scenario from the coverage/depth matrix and record why it is synthetic in the
  case `README.md` and `assertions.json` evidence notes.

Design cases for diversity along three axes:

- User role and familiarity: include novice users who only know the repo's broad purpose, users who know the task but not the repo API, experienced users who name specific modules/classes/CLIs, maintainers integrating the package into a larger project, and users debugging a failure.
- Scenario difficulty: include minimal setup or smoke-test prompts, ordinary end-to-end workflows, parameter/config changes, migration or integration tasks, edge cases, and challenging troubleshooting prompts involving errors, missing dependencies, invalid data, performance constraints, or confusing API behavior.
- Functional breadth: cover every major sub-skill and public capability from the coverage/depth matrix when practical. If a capability is too minor for a dedicated case, include it in a broader case or explain in an index why it was not tested.

Use the repo's actual workflow structure, not just the obvious top-level nouns.
A good case set usually includes:

- At least one primary workflow prompt for each major user-facing route.
- At least one support-workflow prompt for any data preparation, validation,
  conversion, command-building, data-layout, or optional-dependency task that
  makes the primary workflow usable.
- At least one maintainer or repo-development prompt when the repo documents
  contributor policies, duplicated-code rules, release maintenance, or docs
  update practices.
- At least one troubleshooting prompt that forces the skill to surface a
  concrete failure mode instead of only happy-path instructions.

When a repo has a broad workflow area with several common entry points, create
multiple cases for that area instead of one generic umbrella prompt. For
example, if a skill needs to support data validation plus command generation,
those should be separate cases if they have different scripts, parameters, or
failure signals.

Use this minimum difficulty distribution unless the user requests otherwise or
the repo is too small:

- For every primary workflow, create at least one ordinary happy-path case, one
  realistic variant or integration case, and one troubleshooting or edge-case
  case.
- For every non-trivial support workflow, create at least one case that forces
  the agent to use the support workflow directly, such as validation,
  conversion, command construction, data-layout checking, optional-dependency
  diagnosis, environment checking, or schema debugging.
- For each major sub-skill, include at least one novice or broad-purpose prompt
  and at least one expert or API/CLI-specific prompt when practical.
- When repo evidence includes tests or examples for a capability, anchor at
  least one synthetic case to that evidence through `assertions.json`.

Avoid weak prompts that can pass with generic advice. A valid case should
usually contain at least one concrete constraint: a file shape, sample data,
desired output, error message, CLI flag, API name, configuration key, hardware
or backend limitation, dependency issue, performance constraint, or maintainer
policy. Prompts such as "Help me use this repo" or "Explain training" are too
thin unless wrapped in a specific scenario with observable success criteria.

## `user_request.txt` Requirements

Write the prompt exactly as a real user might ask later:

- Usually do not mention the generated skill by name. The point is to test whether the skill triggers and routes correctly from a natural request.
- Include enough task context for an agent to act, such as the user's goal, relevant files or data shape, constraints, error messages, or desired output.
- Do not expose research notes, the original repo checkout path, the temporary inspection environment, or the fact that this is a test case.
- Keep the prompt copy-pasteable as a single complete request. If the scenario needs multiline input, include it naturally in the request body without adding explanatory wrappers outside the user's voice.

## `README.md` Template

Each case `README.md` must explain the test case without being the prompt itself. Use this structure unless the user requested additional sections:

```markdown
# [Short Case Title]

## User Persona
[Who the user is, their repo familiarity, and what they already know.]

## Scenario Coverage
- Skill area: [root skill or sub-skill id]
- Capability: [workflow/API/CLI/config/troubleshooting target]
- Difficulty: [basic/intermediate/advanced/troubleshooting]
- Prompt file: `user_request.txt`
- Expected references/scripts: [generated skill files the future agent should naturally use]
- Trigger expectation: [why the generated skill should trigger for this prompt, or why the case intentionally tests a borderline trigger]

## Expected Successful Behavior
[Concrete behavior that would show the skill is usable: commands, files, APIs, decisions, troubleshooting steps, or verification checks the agent should produce.]

## Failure Signals
[Observable signs that the generated skill is too thin, missing routing, missing references/scripts, relying on original repo paths, leaking local environment details, disabling auto-invocation unexpectedly, giving unverified claims, or failing assertions from `assertions.json`.]
```

## Index

Also write an `index.md` in the test case output directory. The index must list every case directory, the target root skill or sub-skill, user role, scenario, covered capability, and difficulty.

Include a short coverage note comparing the case set against the coverage/depth matrix. If any generated sub-skill or major capability has no test case directory, mark that as a coverage gap unless the user explicitly scoped the cases.

The index should also call out whether each case is meant to test route
discovery, workflow depth, bundled-script executability, support-workflow
discoverability, regression against an older supported workflow, or
troubleshooting clarity. That extra label helps reviewers see whether the
generated skill covers only the headline workflow or also the support and
failure paths that make the skill actually usable.

The index must summarize difficult-case coverage separately:

- Per-sub-skill difficult synthetic cases: each sub-skill id, case count, case
  paths, and the repo evidence each case extends.
- Integrated difficult cases: case paths, capabilities crossed, whether each
  came from an original repo test/example or was synthesized, and the reason for
  any synthetic integrated case.
- Original repo-native cases: case paths or native candidate ids used directly
  as evidence, so reviewers can see that synthetic cases complement rather than
  replace repo-native tests.

Also summarize assertion coverage:

- Number of cases with `assertions.json`.
- Capabilities with native repo evidence anchoring at least one assertion.
- Capabilities covered only by synthetic assertions.
- Capabilities lacking assertions and why.
- Any cases with fixtures and what fixture behavior they test.
