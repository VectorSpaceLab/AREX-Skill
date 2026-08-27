# Attacks and Scenarios API Reference

Use this reference to map high-level red-team requests to PyRIT orchestration APIs. It intentionally omits target/scorer constructor detail; route that to `targets-scorers`.

## Core attack APIs

| API | Use | Verified signature notes |
|---|---|---|
| `PromptSendingAttack` | Single-turn prompt sending with optional converters/scoring. | `PromptSendingAttack(objective_target=REQUIRED_VALUE, attack_converter_config=None, attack_scoring_config=None, prompt_normalizer=None, max_attempts_on_failure=0, params_type=AttackParameters, prepended_conversation_config=None)` |
| `AttackConverterConfig` | Attach converter stacks to attacks. | Configure converters here; construct converter objects in `converters-datasets`. |
| `AttackScoringConfig` | Attach scorers and score handling to attacks. | Use scorers from `targets-scorers`. |
| `AttackAdversarialConfig` | Configure adversarial target/system prompt/schema for adaptive attacks. | Do not confuse adversarial target with objective target. |
| `SequentialAttack` | Try child attacks in sequence/fallback patterns. | Use completion policy to decide when to stop. |
| `CrescendoAttack`, `RedTeamingAttack`, `PAIRAttack`, `TreeOfAttacksWithPruningAttack` | Multi-turn/adaptive strategies. | Require adversarial/scorer/target planning and stronger rate-limit controls. |

## Scenario APIs

`Scenario` groups many atomic attacks, techniques, datasets, and scoring into a campaign. Verified constructor shape: `Scenario(name='', version, technique_class, default_dataset_config, objective_scorer, scenario_result_id=None)`.

Key related concepts:

- `AttackTechniqueFactory` packages an executor class with converters, datasets, scorers, and strategy metadata.
- `DatasetAttackConfiguration` and compound variants control objective datasets and constraints.
- Scenario initializers register target/scorer/technique/dataset defaults before a run.
- Scenario results and attack results are persisted through memory and rendered through output helpers.

## Choosing the owner of behavior

| Behavior | Owning layer |
|---|---|
| What endpoint/model/browser receives the prompt | Target |
| How prompt text/media is transformed | Converter / normalizer |
| Whether an answer succeeded/violated policy | Scorer |
| Next-turn branching inside one objective | Attack/executor |
| Packaging datasets and techniques across a campaign | Scenario |
| CLI flags and backend service lifecycle | `cli-backend-scanner` |

When in doubt, keep components swappable: attacks should use scorers for decisions, targets should only send prepared messages, and scenarios should package rather than implement conversation algorithms.

## Optional heavy paths

Prompt generators such as GCG and some benchmark/model paths may need torch, model/tokenizer downloads, GPUs, or long runtimes. Treat these as optional until the user explicitly asks for them and approves environment/network/compute use.
