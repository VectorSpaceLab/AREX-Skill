---
name: testlib-cpp-judging
description: "Guide C++ competitive-programming judging with the bundled testlib.h. Use when the user asks to author special or scored checkers, strict validators, deterministic generators, basic interactors, or a minimal local solution-checker workflow."
---

# Testlib C++ Judging

## Scope

Use this skill when a task involves `testlib.h`, a special judge, a custom
checker or scorer, an input validator, a deterministic test generator, or a
testlib interactor. It is intentionally C++-only and header-only. Do not create
a Python harness for the ordinary local judging workflow.

This skill owns concrete Testlib APIs, streams, verdicts, command lines, and
templates. When evaluator-facing evidence has triggered independent contract or
oracle work, use [checker and local evaluation](../checker-and-local-evaluation/SKILL.md)
to choose checker/scorer/interactor architecture, reconstruct legality and
objectives, and validate the evaluator itself. Do not enter that route merely
because a previously specified generator or validator is being implemented.

## Start Here

1. Read [the testlib usage guide](references/testlib-usage.md) before writing
   checker, validator, generator, or interactor code.
2. Copy the bundled [testlib.h](scripts/testlib.h) into the working directory
   beside the C++ sources, or add its directory to the compiler include path.
3. Put `#include "testlib.h"` before other includes.
4. Select exactly one registration function for each executable.
5. For ordinary offline judging, use the minimal commands below rather than
   building a separate evaluation framework.

## Choose the Executable Role

| Role | Registration | Main testlib interfaces | Purpose |
| --- | --- | --- | --- |
| Checker | `registerTestlibCmd(argc, argv)` | `inf`, `ouf`, `ans`, `quitf` | Judge contestant output against the input and reference answer |
| Validator | `registerValidation(argc, argv)` | strict `inf`, `ensuref` | Reject malformed or out-of-constraint input |
| Generator | `registerGen(argc, argv, 1)` | `rnd`, `opt`, `println` | Produce deterministic tests from command-line parameters |
| Interactor | `registerInteraction(argc, argv)` | `inf`, `ouf`, `tout`, stdout | Exchange a protocol with an interactive solution |

## Generate Data as Reproducible Code

Testlib includes input-generation support; it is not limited to checkers and validators. When a local problem-finding campaign needs randomized, batch, or maximum-scale data, implement a problem-specific `generator.cpp` instead of hand-authoring large inputs or copying many variants. Parameterize the relevant case family, size, density/bias, structure, and seed tag with `opt`; use `rnd` for all randomness. The full command line determines Testlib's deterministic seed, so preserve that command exactly.

Define the coverage families and their expected oracle, invariant, or failure target before generating volume. Use one deterministic generator invocation per case, or a small coded batch driver that records every invocation in a manifest. Validate every intended-valid generated case with an independent validator before running the solution, and retain the generator command, input hash, validator result, and any failing seed and artifacts. Follow [Checker and Local Evaluation](../checker-and-local-evaluation/SKILL.md#build-problem-finding-data-end-to-end) for the complete coverage-to-retention workflow.

## Critical Checker Contract

Always invoke a checker in this exact order:

```
checker <input-file> <contestant-output> <standard-answer>
```

After registration, the mapping is:

- `inf`: input file
- `ouf`: contestant or participant output
- `ans`: standard or jury answer

Never swap `ouf` and `ans`. Even a checker that does not use the standard
answer still needs the third file argument; pass an empty placeholder file if
necessary.

## Minimal Local Judging Flow

Run these commands from a directory containing `testlib.h`, `solution.cpp`,
`checker.cpp`, `case.in`, and `case.ans`:

```bash
g++ -std=c++17 -O2 solution.cpp -o solution
g++ -std=c++17 -O2 -I. checker.cpp -o checker

timeout 2s ./solution < case.in > case.out
solver_status=$?
if [ "$solver_status" -ne 0 ]; then
  echo "solution failed with status $solver_status" >&2
  exit "$solver_status"
fi
./checker case.in case.out case.ans
checker_status=$?
echo "$checker_status"
exit "$checker_status"
```

If the problem has `validator.cpp`, compile it and validate the input before
running the solution:

```bash
g++ -std=c++17 -O2 -I. validator.cpp -o validator
./validator < case.in || exit 1
```

Capture `solver_status` before running the checker; a timeout, signal, or other
nonzero solution exit is a solver failure and must not be relabeled as an output
verdict. Capture `checker_status` immediately after the checker. For a
verdict-only checker under the default local Testlib configuration, status `0`
means accepted and nonzero means rejection or judge failure. A points checker
using `quitp` instead returns a partial-points status (default `7`) that a
points-aware runner must parse separately. Preserve checker diagnostics and any
reported points with the status.

## Authoring Rules

- Use testlib readers instead of raw parsing for judged files.
- Return `_wa` for a semantically wrong contestant answer, `_pe` for malformed
  contestant output when you detect it explicitly, `_fail` for a broken jury
  answer or checker invariant, and `_ok` only after all required checks pass.
- In validators, describe the exact grammar with `readSpace`, `readEoln`, and
  `readEof`; use bounded reads and `ensuref` for semantic constraints.
- In generators, use `rnd` rather than `rand`, `srand`, or
  `random_shuffle`; identical command lines should reproduce identical data.
- Implement batch and large-case generation in generator code; do not maintain
  hand-edited large input files as the source of truth.
- Run every intended-valid generated case through the independent validator and
  preserve its full generator command and seed tag.
- Flush every interactor query with `std::endl` or an explicit flush.
- Keep `solution.cpp`, checker logic, validator logic, and answer generation as
  separate concerns.

## Boundaries

- This skill explains the public `testlib.h` workflow, not development of the
  testlib repository itself.
- For evaluator roles, this skill implements a previously derived contract. Use
  [checker and local evaluation](../checker-and-local-evaluation/SKILL.md) only
  when contract, reconstruction, score-transform, or fidelity uncertainty is
  evidence-triggered and blocks the current decision, or when official and local
  behavior disagree.
- This skill owns concrete testlib implementation. Use
  [interactive problem solving](../interactive-problem-solving/SKILL.md) for
  protocol modeling, hidden hypotheses, query design, and adversarial strategy.
- It does not bundle a Python evaluator, a build system, repository tests, or
  CI configuration.
- The simple three-file flow is for non-interactive judging. Interactive
  solutions require a bidirectional process runner supplied by the judge.
- Partial scoring needs a runner that understands testlib points verdicts; do
  not interpret every nonzero checker status as ordinary wrong answer in that
  mode.

## Troubleshooting

- Read [troubleshooting](references/troubleshooting.md) when compilation,
  checker arguments, strict whitespace, exit status, generator reproducibility,
  or interactor flushing causes a failure.
