# Algorithmic Problem-Solving Recovery

`algorithmic-problem-solving` is an evidence-driven recovery system for algorithmic, competitive-programming, interactive, online, and scored optimization tasks. It is not a template collection or a replacement for the first focused solution attempt. Once that attempt fails to achieve a verified full result, the skill preserves trusted work, identifies the failing layer, and selects the narrowest justified recovery route.

```text
reproduce the failure -> recover the operational contract
-> classify the failing layer -> run the selected recovery route
-> validate a challenger independently -> promote the best legal champion
-> escalate structurally when local improvement has stalled
```

## Activation and routing

The root `SKILL.md` is the recovery entry point. It activates after few non-full submissions, after the first non-full candidate for an interactive or scored heuristic/optimization task, before a non-full final delivery, or when evidence shows a correctness, resource, evaluator, protocol, or policy failure. It does not apply before a fresh problem's first focused attempt, and it stops after a verified full pass or maximum score.

Sub-skills are targeted internal routes. The root selects them from the observed failure rather than loading every branch at once. Mandatory or paired routes remain additive when the task requires them.

## Codex adaptation

The repository does not ship product-specific `agents/openai.yaml` files, but a Codex adapter should allow implicit invocation only for the root router. Add or merge this policy into `algorithmic-problem-solving/agents/openai.yaml`:

```yaml
policy:
  allow_implicit_invocation: true
```

Every sub-skill should disable implicit invocation so Codex cannot bypass the root diagnosis and routing logic. For example, `algorithmic-problem-solving/sub-skills/interactive-problem-solving/agents/openai.yaml` should contain:

```yaml
policy:
  allow_implicit_invocation: false
```

Apply the same `false` policy to every other sub-skill. The snippets show only the invocation policy; no `default_prompt` is required for this routing design. These optional adapter files are intentionally omitted from the runtime structure below.

## Structure

```text
algorithmic-problem-solving/
├── SKILL.md                          # Recovery router, escalation gates, artifact discipline, and final release rules
├── references/
│   ├── heuristic-search.md           # Quantified search budgets, representations, incremental evaluation, neighborhoods, and optimizers
│   └── technique-selection.md        # Algorithm-family selection after the model and resource envelope are trusted
└── sub-skills/
    ├── checker-and-local-evaluation/
    │   └── SKILL.md                  # Independent checkers, scorers, interactors, simulators, generators, and local evaluation
    ├── contest-solver-engineering/
    │   └── SKILL.md                  # Toolchain, numeric, memory, runtime, I/O, randomness, and implementation recovery
    ├── interactive-problem-solving/
    │   └── SKILL.md                  # Protocol modeling, hidden hypotheses, information-gaining queries, and transcript validation
    ├── model-and-route-algorithms/
    │   └── SKILL.md                  # Contract/model repair, proof obligations, feasibility analysis, and solution-class selection
    ├── plateau-escape/
    │   └── SKILL.md                  # Independent structural review, method research, executable challengers, and evidence-gated promotion
    ├── reactive-online-decision-problem-solving/
    │   └── SKILL.md                  # Estimation, planning, exploration, feedback updates, and risk-aware sequential decisions
    ├── testlib-cpp-judging/
    │   ├── SKILL.md                  # C++ checkers, validators, deterministic generators, interactors, and local judging flow
    │   ├── references/
    │   │   ├── testlib-usage.md       # Testlib roles, APIs, verdicts, templates, and command-line contracts
    │   │   └── troubleshooting.md     # Compilation, arguments, strict input, status, reproducibility, and protocol diagnostics
    │   └── scripts/
    │       └── testlib.h              # Bundled single-header Testlib dependency
    └── validation-and-experiments/
        └── SKILL.md                  # Falsifying tests, independent oracles, paired comparisons, holdouts, and release gates
```

## Operating principles

- **Recover the real contract first.** Read the statement and relevant executable artifacts, separate legality from objective and displayed score, and test any dependency on conflicting interpretations.
- **Classify before editing.** Distinguish model/proof errors, route-selection errors, implementation failures, evaluator uncertainty, weak experimental evidence, search-mechanics problems, information-acquisition failures, and reward-bearing sequential decisions.
- **Select methods from proven premises.** Use the technique catalog only after the model and feasibility envelope are trusted. Every reduction, optimized recurrence, advanced structure, or incomplete route needs an explicit proof or falsification target.
- **Quantify scored search.** Design the representation, invariants, incremental evaluator, reachable neighborhoods, and useful-event rate before choosing an optimizer. Keep `current_state` separate from `best_valid_state`.
- **Build local evaluation only when it is diagnostic.** A missing evaluator or a first non-full candidate is not sufficient by itself. Construct one when concrete legality, score, protocol, replay, or official/local disagreement makes it useful. Structural plateau recovery has its own stricter evaluator gate.
- **Separate interactive and reactive work.** Interactive routing asks what information to acquire; reactive routing chooses reward-bearing actions whose live feedback changes later decisions. Offline repeated evaluation is neither by itself.
- **Preserve artifact roles.** A `fallback` is the simplest guaranteed-valid emergency output, a `challenger` is experimental, a `champion` is the best independently validated legal artifact, and a `baseline` is an external evaluation reference.
- **Promote mechanically from evidence.** A challenger replaces the champion only when it remains legal, respects resource and protocol limits, and improves comparable correctness or scoring evidence.
- **Escalate structure instead of tuning indefinitely.** Once the root's plateau or severe-gap gate is met, freeze the champion, run isolated trajectory review and method research, implement the leading structural routes, and bind adoption or rejection to reproducible results.

Validation starts from the smallest faithful reproducer and expands only as needed through boundary cases, tiny brute-force oracles, differential and metamorphic tests, evaluator self-tests, paired seeds, holdouts, resource probes, and clean release runs. Only experiments that were actually executed count as evidence.
