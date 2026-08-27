---
name: attacks-scenarios
description: "Choose, configure, and interpret PyRIT attack executors,
  techniques, scenarios, benchmarks, workflows, and prompt generators safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyRIT attacks and scenarios

Use this sub-skill when the task is to plan or implement a PyRIT attack run, scenario campaign, benchmark, prompt-generation workflow, or attack-technique selection. This skill owns **orchestration semantics**: which executor or scenario should drive the run, what pieces must be wired together, how retries/concurrency affect execution, and how to interpret attack/scenario results.

Safety boundary: examples and helper scripts here are no-secret and no-network by default. Do not send prompts to a live model or service unless the caller explicitly supplies an approved target configuration, credentials, scope, and data handling rules.

## Route first

| User need | Use this sub-skill for | Route elsewhere for |
|---|---|---|
| Pick an attack algorithm | Single-turn, multi-turn, compound, streaming, benchmark, workflow, prompt generator, scenario vs atomic attack decisions | Target/scorer constructor details in [targets-scorers](../targets-scorers/SKILL.md) |
| Configure attack components | `AttackConverterConfig`, `AttackScoringConfig`, `AttackAdversarialConfig`, `AttackParameters`, `memory_labels`, retry and concurrency placement | Converter/dataset construction in [converters-datasets](../converters-datasets/SKILL.md) |
| Run a scenario campaign | Technique selection, baseline policy, `DatasetAttackConfiguration`, `initialize_async`, `run_async`, scenario result interpretation | Initialization/memory backend setup in [setup-memory-core](../setup-memory-core/SKILL.md) |
| Use `pyrit_scan` or backend | Scenario semantics and what techniques/datasets mean | CLI invocation, backend process, and scanner flags in [cli-backend-scanner](../cli-backend-scanner/SKILL.md) |
| Debug attack/scenario failures | Ownership of branching, async/concurrency, missing defaults, optional heavy paths, memory/result lookup | Credential, target, and scorer failures in [targets-scorers](../targets-scorers/SKILL.md) |

## Required first checks

1. Confirm PyRIT is initialized for the intended memory backend before executing anything that writes prompts, scores, attack results, or scenario results. Route setup details to [setup-memory-core](../setup-memory-core/SKILL.md).
2. Identify the **objective target**: the system under test. Do not confuse it with an **adversarial target**, which PyRIT controls to generate attack prompts for adaptive attacks.
3. Decide whether the run is a one-objective attack, many-objective atomic attack, scenario campaign, benchmark, workflow, or prompt generator.
4. Decide whether scoring is needed. Without an objective scorer, many attacks can execute but report `UNDETERMINED` rather than success/failure.
5. Check modality compatibility: converters and `next_message` data types must produce inputs accepted by the objective target; multimodal scorers must be able to evaluate the returned modality.
6. Bound concurrency and retries before running against rate-limited targets or expensive adversarial/scorer models.

## Fast workflow selection

- **Need one direct prompt or a simple dry run:** use `PromptSendingAttack` with a target and optional `AttackScoringConfig`.
- **Need a fixed conversation script:** use `MultiPromptSendingAttack` or `prepended_conversation`/`next_message` on a single-turn attack.
- **Need adaptive back-and-forth:** use `RedTeamingAttack`, `CrescendoAttack`, `TreeOfAttacksWithPruningAttack`/`TAPAttack`, or `PAIRAttack` with `AttackAdversarialConfig`.
- **Need fallbacks under one objective:** use `SequentialAttack` with `SequentialChildAttack` and a `SequenceCompletionPolicy`.
- **Need a campaign across objectives and techniques:** use a `Scenario`; configure datasets, techniques, baseline policy, concurrency, retries, and labels before `initialize_async()`.
- **Need systematic measurement:** use benchmark executors such as question-answering or fairness/bias benchmarks.
- **Need generated prompts for later attacks:** use prompt generators; treat GCG and HuggingFace-backed paths as optional heavy dependencies.
- **Need scanner commands:** keep semantics here, then route command construction to [cli-backend-scanner](../cli-backend-scanner/SKILL.md).

## Bundled operating references

- [references/attacks-scenarios-reference.md](references/attacks-scenarios-reference.md) — orchestration model, executor/scenario selection, attack/scenario workflows, composition patterns, concurrency and result interpretation.
- [references/api-reference.md](references/api-reference.md) — distilled import/signature tables and practical constructor notes for attacks, scenarios, techniques, benchmarks, prompt generators, and results.
- [references/troubleshooting.md](references/troubleshooting.md) — diagnosis matrices for ownership mistakes, missing components/defaults, modality mismatches, async issues, rate limits, optional GCG/benchmark paths, and memory/result lookup.
- [scripts/attack_scenario_smoke.py](scripts/attack_scenario_smoke.py) — no-secret/no-network smoke helper that imports core PyRIT attack/scenario classes and prints signature metadata without sending prompts.
