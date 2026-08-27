# Preference-Tuning Workflows

## Purpose

Read this when choosing among Axolotl DPO, IPO, KTO, ORPO, SimPO, outcome reward model, and process reward model workflows or when turning a user request into a concrete Axolotl config YAML.

## Method Selection

| User data or goal | Axolotl workflow | Core fields | Notes |
|---|---|---|---|
| Paired preference rows with a better and worse response | DPO | `rl: dpo` | Default offline preference-tuning choice. Requires chosen/rejected examples and a reference-model path internally unless adapter unwrapping avoids a separate load. |
| DPO overfits or the user explicitly asks for IPO | IPO loss under DPO | `rl: dpo`, `dpo_loss_type: ["ipo"]` | Prefer this over `rl: ipo`; direct `rl: ipo` is still present but documented as moving toward deprecation. Do not combine IPO with `dpo_label_smoothing`. |
| Only thumbs-up/thumbs-down or desirable/undesirable completions are available | KTO | `rl: kto`, `remove_unused_columns: false` | Requires unpaired `prompt`, `completion`, and binary `label` after transformation. Do not try to synthesize rejected responses unless the task explicitly asks for pair construction. |
| Paired data but the user wants single-stage alignment with no reference model | ORPO | `rl: orpo`, `orpo_alpha`, `remove_unused_columns: false`, `chat_template` | Uses paired chosen/rejected data but combines supervised and preference objectives in one trainer. |
| Paired data and a length-robust no-reference alternative is desired | SimPO | `rl: simpo`, `rl_beta`, `cpo_alpha`, `simpo_gamma` | Axolotl routes SimPO through a CPO trainer with SimPO loss. It uses DPO-style paired data. |
| Score complete responses for later ranking or RL | Outcome reward model | `reward_model: true`, `model_type: AutoModelForSequenceClassification`, `num_labels: 1` | Uses Bradley-Terry-style chosen/rejected data. Axolotl defaults the model type and labels when omitted, but explicit config is clearer. |
| Score reasoning or solution steps | Process reward model | `process_reward_model: true`, `model_type: AutoModelForTokenClassification`, `num_labels: 2` | Uses `stepwise_supervised` datasets with optional `step_separator` and `max_completion_length`. |

## Shared Offline Preference Rules

- Set `sample_packing: false` for all `rl` preference methods. Axolotl config validation rejects `sample_packing: true` with RLHF training.
- Run `axolotl preprocess config.yaml` before `axolotl train config.yaml`; add `--debug` when checking prompt/chosen/rejected formatting or labels.
- Use `axolotl config-schema` when a field name is uncertain, then keep the final YAML in Axolotl's config-driven style.
- Keep `datasets[].type` aligned with the selected method. DPO/IPO/SimPO use DPO-style strategies, KTO uses KTO strategies, and ORPO has its own `chat_template.argilla` strategy.
- Do not start or require a vLLM server for DPO, IPO, KTO, ORPO, SimPO, reward model, or process reward model workflows. vLLM belongs to online GRPO/GDPO/EBFT routing.

## DPO And IPO Config Pattern

Minimal paired-data pattern:

```yaml
base_model: Qwen/Qwen2.5-0.5B
chat_template: qwen_25
rl: dpo
datasets:
  - path: my-preference-data
    split: train
    type: chat_template.default
    field_messages: conversation
    field_chosen: chosen
    field_rejected: rejected
    message_property_mappings:
      role: role
      content: content
    roles:
      user: [user]
      assistant: [assistant]
      system: [system]
sequence_len: 2048
sample_packing: false
output_dir: ./outputs/dpo-out
```

IPO variant:

```yaml
rl: dpo
dpo_loss_type: ["ipo"]
```

Weighted multi-loss DPO is allowed only when both lists are present and have the same length:

```yaml
rl: dpo
dpo_loss_type: ["sigmoid", "sft"]
dpo_loss_weights: [1.0, 1.0]
```

Useful DPO-specific fields from Axolotl's schema and trainer strategy include `dpo_label_smoothing`, `dpo_use_weighting`, `dpo_padding_free`, `dpo_use_liger_kernel`, `dpo_loss_type`, `dpo_loss_weights`, and `precompute_ref_log_probs`. Use them only when the underlying TRL behavior is understood; first validate with `axolotl preprocess` and a short run plan.

## KTO Config Pattern

KTO is for unpaired examples with a binary desirability label:

```yaml
base_model: Qwen/Qwen2.5-0.5B
rl: kto
rl_beta: 0.1
kto_desirable_weight: 1.0
kto_undesirable_weight: 1.0
remove_unused_columns: false
sample_packing: false
datasets:
  - path: my-kto-data
    split: train
    type:
      field_prompt: prompt
      field_completion: completion
      field_label: label
      prompt_format: "{prompt}"
      completion_format: "{completion}"
sequence_len: 2048
output_dir: ./outputs/kto-out
```

Axolotl validation requires `remove_unused_columns: false` for KTO. If the user's data is paired chosen/rejected, prefer DPO/ORPO/SimPO unless the task explicitly asks to convert pairs into independent labeled completions.

## ORPO Config Pattern

ORPO uses paired preference data but does not use a reference model:

```yaml
base_model: mistralai/Mistral-7B-v0.1
chat_template: chatml
rl: orpo
orpo_alpha: 0.1
remove_unused_columns: false
sample_packing: false
datasets:
  - path: my-orpo-data
    split: train
    type: chat_template.argilla
sequence_len: 2048
output_dir: ./outputs/orpo-out
```

ORPO prompt data expects chosen and rejected conversations that share the prompt/history and differ at the final assistant response. If a row has an odd number of chosen turns or inconsistent histories, fix the data before training.

## SimPO Config Pattern

SimPO uses DPO-style paired data with a no-reference CPO trainer path:

```yaml
base_model: Qwen/Qwen2.5-0.5B
rl: simpo
rl_beta: 0.1
cpo_alpha: 1.0
simpo_gamma: 0.5
sample_packing: false
datasets:
  - path: my-preference-data
    split: train
    type: chat_template.default
    field_messages: messages
    field_chosen: chosen
    field_rejected: rejected
sequence_len: 2048
output_dir: ./outputs/simpo-out
```

Use SimPO when the user needs paired-data preference learning without reference-model memory cost and specifically wants length-normalized reward separation.

## Outcome Reward Model Pattern

Reward models use a sequence-classification head and Bradley-Terry-style pair data:

```yaml
base_model: google/gemma-2-2b
model_type: AutoModelForSequenceClassification
num_labels: 1
reward_model: true
chat_template: gemma
datasets:
  - path: my-pairwise-rm-data
    split: train
    type: bradley_terry.chat_template
sequence_len: 2048
sample_packing: false
eval_sample_packing: false
remove_unused_columns: false
pad_to_sequence_len: true
output_dir: ./outputs/reward-model-out
```

Axolotl can default `model_type` to `AutoModelForSequenceClassification` and `num_labels` to `1` for reward models. Keep them explicit when drafting configs for users.

## Process Reward Model Pattern

Process reward models use a token-classification head and stepwise supervision:

```yaml
base_model: Qwen/Qwen2.5-3B
model_type: AutoModelForTokenClassification
num_labels: 2
process_reward_model: true
datasets:
  - path: my-stepwise-data
    split: train
    type: stepwise_supervised
    step_separator: "\n"
    max_completion_length: 512
sequence_len: 512
sample_packing: false
output_dir: ./outputs/process-reward-model-out
```

Use PRM when labels apply to reasoning steps or intermediate process tokens, not only to complete responses.

## Validation Checklist

- `rl` is one of `dpo`, `kto`, `orpo`, or `simpo` for this sub-skill's offline preference methods.
- `dpo_loss_type` and `dpo_loss_weights` are absent unless `rl: dpo`; if both are present, their lengths match.
- `sample_packing: false` is set for preference RL configs.
- KTO config includes `remove_unused_columns: false` and data has a boolean-like `label`.
- ORPO config includes a concrete `chat_template` and paired chosen/rejected conversations.
- Reward model config uses sequence classification and `num_labels: 1`; process reward model config uses token classification and `num_labels: 2`.
- The dataset checker in `scripts/check_preference_dataset.py` passes on a representative local fixture before expensive preprocessing or training.
