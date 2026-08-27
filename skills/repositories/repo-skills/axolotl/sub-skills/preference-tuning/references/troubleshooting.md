# Preference-Tuning Troubleshooting

## Purpose

Read this when an Axolotl preference-tuning or reward-model config fails validation, preprocessing, tokenization, or early training sanity checks. Prefer the least expensive check first: bundled dataset checker, `axolotl preprocess`, then a bounded training smoke plan if the user explicitly wants runtime validation.

## First Triage

1. Confirm the task is in scope: DPO, IPO, KTO, ORPO, SimPO, outcome reward model, or process reward model. Route online GRPO/GDPO/EBFT/vLLM reward loops elsewhere.
2. Run the bundled local checker on a tiny fixture when using JSON/JSONL data: `python scripts/check_preference_dataset.py --mode dpo --input sample.jsonl` or `--mode kto`.
3. Run `axolotl preprocess config.yaml`; add `--debug` to inspect prompt formatting and label masking.
4. If preprocessing succeeds but training fails, inspect memory, sequence length, reference-model behavior, and trainer-specific fields before changing data semantics.

## Missing Chosen Or Rejected Keys

Symptoms:

- `KeyError: 'chosen'`, `KeyError: 'rejected'`, or a transform complains about missing configured fields.
- The bundled checker reports a missing `chosen`/`rejected` field.

Likely causes:

- The dataset uses nonstandard names such as `better`/`worse`, `chosen_response`/`rejected_response`, or nested messages but the YAML still uses defaults.
- The chosen or rejected value is empty, null, or only whitespace.

Recovery:

- For `chat_template.default`, set `field_messages`, `field_chosen`, `field_rejected`, `message_property_mappings`, and `roles` to match the records.
- For custom text data, use a dictionary `type` with `field_prompt`, `field_chosen`, `field_rejected`, and formatting keys.
- Check a representative fixture with `--chosen-field` and `--rejected-field` before preprocessing.

## Swapped Preference Labels

Symptoms:

- DPO metrics show `rewards/margins` negative or `rewards/accuracies` below random after the user expects signal.
- The rejected response is visibly better than chosen in samples.
- The checker warns that chosen and rejected are identical or suspiciously empty, but it cannot prove semantic order.

Likely causes:

- Data exporter named the worse answer `chosen` or sorted ranked responses in the wrong direction.
- A ranked-answer dataset was flattened without preserving rank meaning.

Recovery:

- Manually inspect several rows with domain knowledge before training.
- For ranked data, confirm whether lower rank means better before assigning `chosen` and `rejected`.
- Do not fix poor metrics by changing loss type first; fix preference polarity first.

## Unpaired Thumbs-Up Data Requested As DPO

Symptoms:

- User has rows like `prompt`, `completion`, `label` but asks for DPO.
- DPO checker reports missing `chosen` and `rejected`.

Likely causes:

- The data is KTO-style unpaired feedback, not pairwise preference data.

Recovery:

- Use `rl: kto`, `remove_unused_columns: false`, and a KTO `type` mapping with `field_label`.
- Only build DPO pairs if the user has a reliable pairing strategy and explicitly asks for pair construction.

## KTO Label Errors

Symptoms:

- `KeyError: 'label'`.
- Axolotl validation asks to set `remove_unused_columns: False` for KTO.
- The bundled checker reports non-binary labels.

Likely causes:

- Missing `field_label` mapping for custom data.
- Labels are free-form text or scores instead of binary desirable/undesirable values.
- `remove_unused_columns` is omitted or true.

Recovery:

- Set `rl: kto`, `remove_unused_columns: false`, `sample_packing: false`, and map `field_label` to the correct column.
- Normalize labels to booleans or clear binary values before preprocessing.
- Do not use KTO for pair-only data unless converting pairs into labeled independent completions is part of the task.

## Sample Packing And Sequence Length

Symptoms:

- Config validation raises ``sample_packing: true` does not work with RLHF training`.
- KTO validation raises `sample_packing is not supported with kto`.
- Preprocess or training truncates preference text unexpectedly.

Likely causes:

- SFT defaults or copied configs kept `sample_packing: true`.
- `sequence_len` is too short for prompt plus chosen/rejected or completion text.

Recovery:

- Set `sample_packing: false` for preference RL methods; set `eval_sample_packing: false` for reward-model examples when applicable.
- Increase `sequence_len` only after checking memory impact.
- Use preprocessing debug output to see whether prompts or answers are being truncated.

## Reference Model Memory

Symptoms:

- DPO/IPO/KTO runs out of GPU memory earlier than comparable SFT.
- The user expects ORPO or SimPO memory behavior but config uses `rl: dpo`.

Likely causes:

- Reference-model log-probabilities are needed for DPO/IPO/KTO unless adapter unwrapping avoids loading a separate model.
- Full fine-tuning without LoRA/QLoRA leaves little memory for reference computation.

Recovery:

- For adapter training, leave Axolotl's default adapter reference behavior unless the user explicitly needs `rl_adapter_ref_model: true`.
- Consider `precompute_ref_log_probs: true` when DPO reference computation is a repeated bottleneck and storage trade-offs are acceptable.
- If the user's priority is no reference model, consider ORPO or SimPO instead of DPO/IPO.
- Route hardware placement, FSDP, DeepSpeed, and GPU topology changes to `distributed-and-performance`.

## IPO And Loss-Type Confusion

Symptoms:

- Config includes `rl: ipo` and warnings mention deprecation.
- Config sets `dpo_loss_type` while `rl` is not `dpo`.
- Config sets `dpo_loss_weights` without matching `dpo_loss_type` length.
- IPO config includes `dpo_label_smoothing`.

Likely causes:

- Older config examples or mixed TRL loss recipes.

Recovery:

- Prefer `rl: dpo` plus `dpo_loss_type: ["ipo"]` for IPO.
- Use `dpo_loss_type` and `dpo_loss_weights` only with `rl: dpo`.
- Keep `dpo_loss_type` and `dpo_loss_weights` lists the same length.
- Do not combine IPO with DPO label smoothing.

## ORPO Single-Stage Assumptions

Symptoms:

- User expects a frozen reference model in ORPO.
- Tokenization errors arise from malformed `chosen`/`rejected` conversations.
- ORPO template output looks wrong.

Likely causes:

- ORPO is a no-reference single-stage method, not DPO with a different beta.
- `chat_template` is missing or does not match model/data roles.
- Chosen and rejected histories do not share a prompt/history before final answer.

Recovery:

- Set `rl: orpo`, `orpo_alpha`, `remove_unused_columns: false`, and an explicit `chat_template`.
- Validate that each pair differs at the final assistant response rather than at the user prompt.
- If the data is simple text pairs, use DPO/SimPO or adapt the data to ORPO's chat-template pair shape deliberately.

## Outcome Reward Model Head Mismatch

Symptoms:

- Model head shape errors or sequence-classification errors.
- Reward model loss is high and padding warnings appear.

Likely causes:

- Missing or incorrect `model_type`/`num_labels`.
- `pad_to_sequence_len` not set with reward model data.
- Dataset type is a DPO trainer strategy instead of Bradley-Terry reward-model strategy.

Recovery:

- Use `reward_model: true`, `model_type: AutoModelForSequenceClassification`, `num_labels: 1`, `pad_to_sequence_len: true`, and `remove_unused_columns: false`.
- Use a Bradley-Terry pair dataset type such as `bradley_terry.chat_template`.
- Do not set `rl` for a plain outcome reward model unless the user is doing a separate RL workflow.

## Process Reward Model Head Or Data Mismatch

Symptoms:

- Token-classification errors, missing step labels, or labels misaligned with reasoning steps.
- User asks for a reward model but describes per-step supervision.

Likely causes:

- Outcome reward model and process reward model configs were mixed.
- `stepwise_supervised` fields such as `step_separator` or `max_completion_length` do not match the data.

Recovery:

- Use `process_reward_model: true`, `model_type: AutoModelForTokenClassification`, and `num_labels: 2`.
- Use `type: stepwise_supervised` and configure the step separator to match the fixture.
- Use outcome reward model guidance only for whole-response scoring.

## When To Stop

Stop and ask for user input instead of guessing when:

- The data semantics do not identify which response is better.
- Labels are continuous scores and the user has not chosen binarization or ranking rules.
- The requested validation requires downloading a model, using credentials, launching training, or reserving specific GPU hardware.
- The task actually needs online reward functions, vLLM rollout generation, GRPO/GDPO/EBFT, or distributed launch tuning owned by sibling sub-skills.
