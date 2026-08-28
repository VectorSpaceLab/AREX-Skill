---
name: plateau-escape
description: >-
  Escape a root-verified measured plateau or severe score gap in a scored
  algorithmic, heuristic, or hybrid solver through independent review, method
  research, and an evidence-gated structural prototype. Use only when the root
  router admits a verified legal champion. For an interactive or scored
  heuristic/optimization task, including AHC, first implement and validate its
  mandatory independent local interactor/checker/scorer under
  checker-and-local-evaluation, delegating missing implementation to a separate
  fresh-context evaluator builder when available. Do not use for an isolated
  low score without the root severe-gap evidence, invalid or zero output,
  checker disagreement, crash, TLE/MLE, or interactive protocol failure alone.
---

# Plateau Escape

Protect the verified champion, challenge the current problem representation, and test a structurally different method before resuming scalar tuning.

## Entry contract

Enter only when the root [scored-recovery escalation](../../SKILL.md#escalate-weak-scored-recovery) routes here. Treat that routing decision as authoritative instead of re-deriving plateau thresholds in this sub-skill. The handoff must identify the measured-plateau or severe-score-gap signal and include the champion-legality, resource, and controlled-attempt evidence used by the root; if the escalation signal is absent, return to the root router. For an interactive or scored heuristic/optimization task, missing or unvalidated local-evaluator evidence is not a reason to proceed or return only advice: complete the mandatory evaluator gate below first.

## Freeze the champion and separate facts from conclusions

Do not mutate the champion during diagnosis. Preserve the original problem artifacts rather than replacing them with a summary. Build two records:

```
primary problem packet
  verbatim original statement content/title/URL and exact I/O or protocol
  original constraints, objective, scoring and aggregation rules
  official evaluator/configuration, samples, public instances, benchmark or dataset
  target toolchain, resource limits, submission interface and remaining budget

verified fact ledger
  necessary fact | exact derivation/source/command | reproducing artifact
  champion identity, legality, final score/runtime and evaluator evidence
  local evaluator identity/hash, build/run commands, fixtures and validation evidence
  saved counterexamples, profiles and fixed cases/seeds
```

A derived fact is admissible only when it follows from a checked proof, an official primary artifact, or a reproducible command or test whose artifact is included. Keep prior diagnoses, method preferences, estimated upside, risk labels, and reported results without raw evidence out of the fact ledger. Preserve an unresolved discrepancy as a question with its primary artifacts; never silently turn one interpretation into a fact.

Give every sub-agent the verbatim primary problem packet rather than only a main-agent summary. A summary may index original artifacts but may not replace them. Pass main-agent reasoning, diagnoses, or prior results only when a later role explicitly requires them, and label claims that lack primary or reproducible evidence as unverified.

Keep the prior attempt log separately as claims plus observations:

```
claimed hypothesis -> exact material change -> command/submission -> observed result
```

Stop repeated changes to weights, thresholds, temperatures, tie-breaks, seeds, or runtime allocation. The next hypothesis must concern representation, objective/value model, neighborhood reachability, planning horizon, decomposition, relaxation, or algorithm family.

## Complete the phase-local mandatory evaluator gate

For every interactive task and every scored heuristic or optimization task, including AHC, read and execute [Checker and Local Evaluation](../checker-and-local-evaluation/SKILL.md) in full, then verify that an executable independent local interactor, checker, scorer, simulator, or required combination satisfies it. This is a Plateau Escape phase requirement activated by the verified plateau or severe score gap; it is not a global requirement after the first non-full candidate. An official score or solver-authored validity function alone does not satisfy this prerequisite. Do not start the trajectory critic, method researcher, challenger comparison, another submission, or final delivery until the gate is complete.

If the artifact is missing or insufficient, Plateau Escape owns implementing and validating it. Do not defer it to the main agent as a recommendation or mark the structural search complete without it. When delegation is available, MUST assign implementation to a dedicated fresh-context evaluator-builder sub-agent that is distinct from the solver/challenger owner, trajectory critic, and method researcher. That builder must read the complete Checker and Local Evaluation sub-skill and own the executable artifact and its validation, not merely audit another owner's evaluator. Give that evaluator builder only:

```
complete Checker and Local Evaluation sub-skill as the implementation contract
verbatim primary problem packet and official original files
only necessary verified toolchain, process, resource, and filesystem facts
an isolated writable path and role/output handoff contract only,
  with no main-agent-derived evaluator semantics
```

Initially withhold the champion, solver source, attempt log, current methods, main-agent reasoning, diagnoses, expected results, claimed scores, and unverified summaries. Require the evaluator builder to freeze its evaluator contract, implementation, and initial fixtures before receiving raw candidate outputs, transcripts, or raw official responses for differential validation. Never replace a raw artifact with the main agent's interpretation of it.

Require the evaluator-builder handoff to contain:

```
evaluator source/executable paths and content hashes
exact end-to-end run and applicable build commands
valid, invalid, boundary, mutation, and tiny hand-computed fixtures
coverage table, parameterized generator and validator commands, and seed manifest when generated cases are needed
original and minimized failing cases with full provenance when a failure is found
real-pipe protocol and transcript tests when interactive
independent legality and raw-objective recomputation when scored
official/local comparison evidence and unresolved discrepancies
```

Run those commands and adversarial fixtures before registering the evaluator in the verified fact ledger. If local and official evidence disagree, stop challenger evaluation and minimize that discrepancy first. The solver owner may execute the frozen evaluator but may not alter it to accept a candidate; evaluator changes require official evidence, a hand-computed counterexample, or a failing evaluator test. If delegation is unavailable, perform a sealed evaluator pass with separate files, representations, derivations, and fixtures before resuming the two review roles.

## Run two independent fresh-context reviews

Use two fresh isolated sub-agents when the environment supports delegation. Prefer the least inherited conversation context and give each a distinct writable path that does not yet exist. Do not let either reviewer see the other's preliminary conclusions, and do not select the next route before both results return.

Give both reviewers the complete verbatim primary problem packet and the frozen evaluator interface. Do not substitute a problem summary or solver narrative for original artifacts. Keep the main agent's reasoning and unreliable results out of the initial review packets; reveal only the role-specific verified evidence described below and only in the stated order.

Give each reviewer the primary problem packet, only the role-specific projection of the verified fact ledger described below, and this write and evaluation contract:

```
You may create and edit files only under: <fresh_agent_output_path>
Do not modify, delete, rename, or overwrite any pre-existing file.
Treat every pre-existing artifact, including the champion, as read-only.
You may build, run, evaluate, and, within the delegated quota, submit challengers
created in your isolated path. The quota allocation is the submission authorization;
do not request main-agent approval again for each in-quota submission.
Return the path of every file you create.
```

Do not place either reviewer in a read-only environment or globally forbid file creation. If the user or enclosing workflow authorizes remote submissions and at least one submission remains, reserve an explicit quota for sub-agent evaluation; allocate at least one submission to the method researcher instead of retaining the entire budget for the main agent. When authorization and remaining budget permit multiple submissions, give each selected rank-1 track a multi-submission iteration quota before funding lower-ranked methods or retaining unused budget for the main agent. State the evaluator, final metric, quota, deadline, and whether results are synchronous. A sub-agent may not exceed that quota or infer broader authorization. If only the main agent can access the submission transport, it must relay the sub-agent's exact artifact unchanged for each iteration and return the raw evaluator response; it may not substitute a different candidate or make a method decision at that boundary.

Both reviewers should default to returning a self-authored executable challenger and owning its implementation, compile, local validation, comparison, repair/improvement iterations, and authorized official submissions through the terminal result or quota. Prefer reviewer-owned evaluation over handing code or an unevaluated proposal back to the main agent for subjective screening. If no faithful prototype fits the assigned resources or no submission is authorized, record the exact blocker and return the strongest executable partial artifact; do not silently transfer implementation or method judgment to the main agent.

Require compilable source in the target language, exact build/run commands, and portable C++17 when the target does not specify a language standard. Any new checker, scorer, interactor, simulator, or evaluation harness must follow [Checker and Local Evaluation](../checker-and-local-evaluation/SKILL.md), should be C++ unless the verified interface makes that genuinely impractical, and must remain owned independently from the challenger it evaluates.

For both roles, freeze an ordered remedy ranking before implementation. Rank by the evidence-weighted expected terminal final official aggregate score achievable under the full verified remaining hard time, compute, and submission budget, using source evidence, structural fit, comparable measurements, and uncertainty. *Applicable* means compatible with the verified contract and final judge limits; it does not mean easy to code or likely to fit in one sub-agent turn. Implementation difficulty, patch or code size, rewrite scope, familiarity, prototype speed, and current-turn convenience MUST NOT affect a method's rank. Small or quick tests may order diagnostics within a method, never the methods themselves.

Explore aggressively across high-upside representations, objectives, decompositions, neighborhoods, planning horizons, relaxations, and algorithm families, including routes that require a substantial rewrite. Aggressive exploration means ambitious method choice plus persistent evidence-driven iteration; it never waives legality, evaluator fidelity, final judge limits, or submission authorization. *Assigned/delegated resources* means explicit user scope, hard deadline, compute, filesystem, and authorized submission quota, never the length of one sub-agent turn. When follow-up turns are supported, continue the same isolated rank-1 owner and writable path instead of treating a turn boundary as a blocker.

Phrase each rank-1 assignment as:

```
Implement the rank-1 applicable method by expected terminal official score.
Start with its smallest faithful structural prototype, preserve its defining
mechanism, then iteratively repair and improve it through the delegated
evaluation and submission quota.
```

`Smallest` constrains only the first experiment, never the method ranking. If the rank-1 method cannot be completed within the explicit hard delegated resources after available follow-up turns, preserve its rank, record the exact blocker and minimum additional requirement, and return its strongest faithful partial artifact. Do not silently substitute an easier lower-ranked method; move lower only after the recorded-elimination gate is satisfied.

For either role, use this protected rank-1 loop within the authorized quota:

```
raw local/official result -> diagnose defining weakness from evidence
-> method-faithful repair, completion, or structural refinement
-> local legality/objective validation -> next authorized submission -> repeat
```

If remote submission is not authorized, run the same loop with local evaluation only. Stop the track only when its explicit quota or deadline is exhausted, its predeclared defining hypothesis is falsified, a hard incompatibility or invalidity remains after the required focused repair, or evidence shows that further method-faithful iterations cannot materially improve the official metric. The first compiling prototype, first official score, or one under-tuned or non-improving submission is not terminal rejection evidence.

Return executable code and fixtures plus a completed ordered iteration record, not a recommendation for the main agent to judge. Label each completed official response `EXACT_OFFICIAL` and each reproducible local result under an identified evaluator `EXACT_LOCAL`, while distinguishing an iteration result from the track's terminal status. Otherwise report `NOT_EVALUATED` and the concrete unavailable authorization, quota, interface, or resource; never replace a missing score with an estimate.

The iteration record for each role must include:

```
rank-1 track identity, expected-score rationale, quota and stop conditions
for every iteration: candidate path/hash, diagnosis, and material change
exact build, run, validation and submission commands per iteration
evaluator/version, instance set, seeds and resource budget
submission ids, timestamps and raw responses for every remote iteration
per-iteration validity/verdict, raw objective, final score, runtime and memory
per-case data and comparison with the frozen champion under the same final metric
```

Assign distinct roles:

### Trajectory critic

First reconstruct the objective, bottleneck, and likely failure layer from the primary problem packet and verified fact ledger. Freeze that reconstruction before receiving the separate attempt log. Then audit:

- model and evaluator fidelity;
- representation and invariants;
- neighborhood reachability and proxy alignment;
- assumptions rejected without evidence;
- experiment design, variance, and overfitting.

Return ranked root causes, the strongest competing explanation, and `3-5` structurally different remedies. Rank the remedies under the shared expected-score rule before designing their experiments. For each leading remedy, specify the smallest falsifying experiment, success threshold, and abort condition. Implement the rank-1 applicable remedy in the assigned path, then repair and improve it through its delegated evaluation/submission quota rather than replacing it because the first faithful prototype is difficult or initially weak.

### Method researcher

Research the original problem independently, not the incumbent solver or the main agent's diagnosis. Initially receive the complete primary problem packet and only verified facts necessary to understand the contract, hard budgets, target, and available evaluation interface. Do not receive the champion identity or score, attempt log, current method labels, rejected-method rationales, trajectory critic conclusions, or any unverified summary before freezing an independent research map. After that map is saved, the exact champion interface and score plus reproducible negative results may be revealed only to prevent duplicate implementation and to support a direct comparison.

Search from the problem outward:

- exact title, distinctive statement phrases, source contest, editorials, leaderboards, and strong solution write-ups;
- canonical problem names, aliases, mathematical structure, objective, constraints, and scale;
- primary papers, surveys, references and citation chains, including adjacent fields with the same optimization structure;
- relevant benchmarks, public datasets, instance generators, baselines, winning methods, and evaluation protocols;
- maintained implementations and repositories that clarify a method's defining mechanism.

Do not stop at the current solver family. Continue targeted searches until new queries only repeat already-mapped method families or the explicit research budget ends. Keep a source/evidence index; a concise decision memo may link to that index and must not discard useful sources merely to satisfy an arbitrary link cap.

Map every candidate to the exact contract. Distinguish source-backed facts, independently derived facts, measured results, and unresolved hypotheses. Freeze an ordered ranking under the shared expected-score rule before prototyping. Implement the rank-1 applicable method first: begin with its smallest faithful prototype, then iterate toward the full scoring implementation. Select a lower-ranked method only after every higher-ranked method has one of these recorded in the ordered candidate ledger:

- a minimally faithful prototype that still fails its defining hypothesis after the predeclared repair/iteration budget, with its commands, artifacts, and results;
- a demonstrated incompatibility with the verified contract;
- a measured runtime or memory failure against a hard budget;
- independently verified implementation invalidity that remains after the required focused repair.

Implementation convenience, familiarity, code size, or a main-agent preference is not rejection evidence and does not permit skipping a higher-ranked method. For the current highest-ranked eligible method, own the full track end to end:

```
research -> faithful implementation -> compile -> local legality/objective checks
-> champion comparison -> authorized official submission -> diagnose and iterate
-> terminal evaluator result or exhausted delegated quota
```

If delegation is unavailable, perform the two roles as explicitly separate passes: write and seal the trajectory audit before starting a source-backed method search, and do not rewrite the first report to match the second. Preserve the same role-specific information barrier.

## Apply the independent results

After both reviews return:

1. Register every leading proposal and preserve each reviewer's ranking and evidence; do not rewrite the reports into a main-agent ranking before disposition.
2. Accept an already terminally evaluated sub-agent result as evidence. Do not send it back to the main agent for a second subjective method judgment.
3. Process both frozen rankings in order and give each role's rank-1 applicable unresolved method a protected iterative implementation/evaluation slot. If scope leaves only one slot, choose between the two rank-1 methods by expected terminal official score evidence, not implementation ease. Do not select a lower-ranked method until every higher-ranked method satisfies the recorded-elimination gate above.
4. Give every leading proposal exactly one disposition: `EVALUATED`, `TEST_REQUIRED`, `REJECTED_WITH_EVIDENCE`, or `BLOCKED_BY_SCOPE`. A label without its command, artifact, measurement, proof, primary contract citation, or exact immutable scope boundary is incomplete.
5. Permit at most one or two already-defined cheap same-family scalar experiments to finish before the protected rank-1 structural tracks. Do not begin another tuning sequence.

A renamed version of the current solver is not a structural prototype.

`BLOCKED_BY_SCOPE` may stop the workflow, but it does not eliminate a higher-ranked method or authorize selection of a lower-ranked one.

For this gate, *leading* includes each reviewer's rank-1 method and every challenger already returned as executable code or with a terminal evaluation. The main agent may add candidates but may not remove these mandatory dispositions. When evidence conflicts, prefer a comparable terminal official result, then a reproducible independent local result, then a checked proof or measured resource bound, then source-backed applicability evidence; an opinion never overrides a higher tier.

Use [model and route algorithms](../model-and-route-algorithms/SKILL.md#5-establish-the-operation-and-memory-envelope) to test whether a proposed exact or hybrid class fits the contract and resource envelope, [technique selection](../../references/technique-selection.md) to compare concrete exact or data-structure families, and [heuristic search](../../references/heuristic-search.md) to instantiate and measure scored-search alternatives. The reviews choose hypotheses; the model-and-route sub-skill supplies the feasibility gate, while the shared references supply algorithm-family and search mechanics.

## Bind main-agent discretion to evidence

Reject a researched method only when concrete evidence shows one of these:

- a cited assumption contradicts the verified original contract;
- a minimally faithful prototype still fails its predeclared defining hypothesis after its focused repair/iteration budget;
- a derived bound or measured runtime or memory exceeds a hard budget without credible optimization margin;
- an identified reconstruction, serialization, or hard-validity condition fails after one focused repair cycle;
- after the protected rank-1 loop reaches one of the shared stop conditions above, the track's best exact result is no better than a competing alternative under the same final evaluator and comparable total iteration/submission budgets.

`Risk too high`, unfamiliarity, restructuring cost, implementation size, disagreement with the current trajectory, or an unmeasured pessimistic estimate is not rejection evidence. Quantify any claimed risk as a violated hard constraint, a derived bound, a failed artifact, or a measured result. Repair trivial build or integration defects for one focused cycle before judging the method. If the main agent believes a prototype is unfaithful, it must name the missing defining mechanism and allow one focused repair instead of discarding the family.

When a user-imposed authorization, submission quota, deadline, language, or artifact boundary genuinely makes evaluation impossible, record `BLOCKED_BY_SCOPE` with the exact remaining budget and the measured or derived minimum requirement. This is not evidence that the method is weak and must not be rewritten as `REJECTED_WITH_EVIDENCE`.

When a reviewer returns code, keep it as a separate challenger and run:

```
inspect -> compile -> repair trivial integration defects once
-> legality/objective/runtime validation -> sub-agent-owned authorized submission
-> diagnose -> repair or improve -> repeat within delegated quota
-> record terminal result -> promote or reject with evidence
```

The sub-agent owns the ordered evaluation record and terminal score of its rank-1 track within the delegated quota; the main agent owns only champion-file mutation and mechanical promotion. Under the same established final evaluator, automatically promote a legal iteration whose exact final score is better and whose hard resource/protocol constraints pass, but do not end the protected track merely because an intermediate champion was promoted. Withhold promotion only for a concrete failing artifact or an explicit user-imposed release condition, and record it. Retain the champion when an iteration is invalid, worse, tied without another predeclared benefit, or not evaluated. Opinion cannot override an exact comparable result.

## Exit condition

End this escape cycle only after every selected rank-1 track has reached one of the shared stop conditions above and every other leading structural alternative has a terminal evaluation, concrete rejection evidence, or an immutable user-scope block with quantified requirements. Do not stop a selected rank-1 track after its first legal or improved score while delegated iterations remain and evidence predicts material gain. `Not evaluated`, `risky`, and an unevidenced main-agent veto do not satisfy the exit condition. Resume focused tuning only on the selected final method. Run this workflow again only after that materially new family also reaches a new plateau or new evidence invalidates the reviews.

Return:

```
plateau evidence
role-specific input packets and reviewer rankings
source/evidence index, prototype and exact commands
submission ids and terminal champion-versus-challenger scores
promotion or evidence-backed rejection record
```
