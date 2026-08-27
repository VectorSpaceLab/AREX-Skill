# Prompting troubleshooting

Use this reference when OpenChat prompts tokenize differently from expected, fail before tokenization, or behave differently between direct Python, serving, and evaluation.

## Quick diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError: 'openchat_3.5'` when indexing `MODEL_CONFIG_MAP` | `openchat_3.5` is a serving alias, not the canonical config key | Use `openchat_v3.2_mistral` for direct config/evaluation/training. Use `openchat_3.5` only as a request model name after serving advertises it. |
| Prompt uses `GPT4` when you expected `GPT4 Correct` | Wrong model type or explicit condition override | Check [model-overview](model-overview.md). `openchat_v3.2` defaults to `GPT4`; OpenChat 3.5/3.6-style configs default to `GPT4 Correct`. |
| Math prompt behaves like default chat | `Math Correct` was not passed as `Conversation.condition` or request `condition` | Set `condition="Math Correct"`. Do not change `model_type` for math mode. |
| Training tokenization raises `AssertionError` | At least one `Message.weight` is missing while `inference=False` | Add numeric weights to every message. Typical SFT uses user `0.0`, assistant `1.0`. |
| Loss is applied to user text | User message weight is nonzero | Set user weights to `0.0` when only assistant responses should be supervised. |
| Final inference prompt contains EOT after empty assistant | Manual prompt concatenation, or `inference=False` used for generation | Use `inference=True` and end with an empty assistant turn. OpenChat deliberately omits EOT on the final inference turn. |
| Generation never stops or includes EOT text | Generation stop token does not match template EOT | Use the selected template's `eot_tokens_` as stop token IDs. For manual Transformers generation, set the model's end/stop behavior to the template EOT. |
| Serving asserts EOT has multiple tokens | Tokenizer does not contain the EOT as one special token | Use model/tokenizer weights prepared for the OpenChat template or rebuild special tokens before constructing the template. |
| System prompt is ignored through the API server | Serving skips `system` messages unless system prompts are enabled | Enable serving system prompts, or use direct Python and set `Conversation.system`. See [serving](../../serving/SKILL.md) for server options. |
| System text appears without a `System` role | Selected template has `system_as_role=False` | This is expected for non-OpenChat-3.6 templates. `openchat_3.6` emits a real system role header. |
| `gemma_it` fails on role `system` | Gemma role mapping only covers `user` and `assistant` | Put system text in `Conversation.system`, and keep message roles to user/assistant. |
| Token IDs differ from repo tests | Different tokenizer repo, old cache, missing special tokens, wrong condition, or wrong `use_fast` setting | Match the canonical model type to the tokenizer weights, refresh stale cache if needed, and recreate `ConversationTemplate` after tokenizer changes. |
| HF `apply_chat_template` differs from OpenChat direct tokenization | Config has no `hf_chat_template`, or `add_generation_prompt`/system-turn handling differs | Prefer `ConversationTemplate` for OpenChat. Use HF chat templates only for configs that define one and with `add_generation_prompt=True`. |

## Mismatch triage order

1. **Confirm model names.** Identify weight repository/path, canonical model type, and serving request model separately.
2. **Confirm condition.** Empty inference may insert a default condition. Non-inference does not.
3. **Confirm the final turn.** Inference generation prompts should end with an assistant role prefix and no EOT after it.
4. **Confirm EOT.** The template's `eot` string and cached `eot_tokens_` must match the tokenizer.
5. **Confirm weights.** Missing or incorrect weights affect only non-inference tokenization.
6. **Confirm system handling.** Direct `Conversation.system` and OpenAI-style `system` messages are not identical in serving.
7. **Confirm cache/special tokens.** If tokenizer files changed, rebuild the tokenizer and recreate the `ConversationTemplate` so BOS/EOT caches are refreshed.

## Tokenizer and cache caveats

`ConversationTemplate` caches `bos_tokens_` from `tokenizer("")` and `eot_tokens_` from the template EOT at construction time. If you add special tokens, change tokenizer files, or switch model directories, create a new template object.

Auto-detection in serving/evaluation uses the model repository's cached `openchat.json` when no `model_type` is supplied. If that file is absent, stale, or inaccessible offline, use an explicit canonical model type.

Fast tokenizer behavior is modified briefly inside `_tokenize` through the tokenizer's internal special-token setting. Avoid sharing one mutable tokenizer object across unrelated concurrent formatting tasks unless you control synchronization.

## Manual prompt pitfalls

Manual prompt strings are useful for quick inspection, but they bypass several safeguards:

- message text may accidentally become a real special token;
- final assistant EOT may be added by mistake;
- system prompts may use the wrong shape for the selected template;
- aliases may hide the canonical template family.

When exact tokens matter, construct `Conversation` objects and call `ConversationTemplate.tokenize_conversations` rather than concatenating strings.

## Boundary reminders

- For API server startup, request validation, `--enable-sys-prompt`, Ray/vLLM, Docker, and streaming behavior, use [serving](../../serving/SKILL.md).
- For benchmark conditions, `--condition`, `--system-msg`, answer matching, and result viewing, use [evaluation](../../evaluation/SKILL.md).
- Training/data/model-surgery details are outside this prompting sub-skill; this reference only explains the prompt/tokenization pieces needed to avoid mismatches.
