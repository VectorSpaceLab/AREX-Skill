# Troubleshooting

Use this guide when ms-swift dataset customization, registry plugins, model selection, or template checks behave unexpectedly. For full training, RLHF, deployment, export, or evaluation failures, route to the owning workflow after confirming data/model metadata is valid.

## Malformed Messages

Symptoms:

- Rows disappear during preprocessing.
- Errors mention `messages`, invalid `role`, or `content`.
- Encoded prompts are missing turns.

Checks:

- `messages` is a non-empty list after `--columns` mapping.
- Every message has `role` and non-null `content`.
- Roles are one of `system`, `user`, `assistant`, `tool_call`, `tool_response`, or `tool`.
- ShareGPT rows use recognizable keys such as `human`/`assistant`, or configure `MessagesPreprocessor` with explicit role/content keys.
- CSV cells containing `messages` are valid JSON strings, not Python repr fragments.

Use:

```bash
python scripts/validate_dataset_rows.py data.jsonl --max-errors 20
```

## Auto Column Mapping Surprises

Symptoms:

- `input` is treated as query when it should be media or auxiliary text.
- `content` becomes response unexpectedly.
- A useful field is removed before training.

Cause:

`AutoPreprocessor` maps common aliases for system/query/response and removes columns not in ms-swift standard keys unless they are retained by a specific flow. Direct `--columns` mappings have higher priority.

Fixes:

- Map source columns explicitly: `--columns prompt=query answer=response`.
- Preserve a correctly named column with identity mapping when needed: `query=query`.
- For GRPO custom reward fields, keep extra fields intentional and document them for the RLHF workflow.
- Move complex mapping logic into a custom `ResponsePreprocessor` or `MessagesPreprocessor` plugin.

## Strict Row Drops

Symptoms:

- Logs show dataset rows deleted.
- Dataset length after preprocessing is smaller than the source.
- `strict=False` hides problems until a later template step.

Common causes:

- Empty `messages`.
- Invalid role names.
- `rejected_response` equal to the chosen final answer.
- Bad `objects.bbox` shape.
- Max-length errors when truncation is set to raise.
- JSON strings that were not parsed into lists/objects.

Debug with a small sample, turn on strict behavior in the ms-swift command when appropriate, and use the bundled validator to find row numbers before launching a long job.

## Missing Media Paths or URLs

Symptoms:

- File-not-found errors during preprocessing or template encoding.
- Placeholder/media count mismatch.
- Multimodal model receives no images/videos/audios.

Checks:

- `<image>`, `<video>`, and `<audio>` counts match media list lengths for the target template.
- Media fields are lists, strings, URLs, base64 data URIs, or supported frame-list structures.
- Local paths exist in the job runtime, not only on the machine that wrote the dataset.
- Rejected multimodal branches provide `rejected_images`, `rejected_videos`, or `rejected_audios` when they differ from chosen media.

Use:

```bash
python scripts/validate_dataset_rows.py data.jsonl --check-media exists
```

Use `--check-media syntax` when remote workers cannot access the same local paths yet.

## RLHF Preference Fields

Symptoms:

- DPO/RM rows fail during template encoding.
- Chosen and rejected labels are identical.
- Multimodal or agent rejected branches use chosen-side context accidentally.

Rules:

- DPO/ORPO/CPO/SimPO/RM need a chosen side in `messages` plus a rejected side.
- Use `rejected_response` for simple rejected assistant content.
- Use `rejected_messages` for full alternative branches.
- When `rejected_messages` differs in media or tools, also provide rejected media/tool fields.
- `label` is for KTO/classification/regression, not a substitute for DPO rejected content.

Check final formatting with a template in `rlhf` mode before long RLHF execution.

## Loss and Loss Scale Semantics

Symptoms:

- Loss is computed on tool responses or thinking spans unexpectedly.
- Values above `1` cause binary loss-scale assumptions to fail.
- Consecutive tool calls do not respect every `loss` field.

Rules:

- Message-level `loss` and `loss_scale` apply to assistant spans.
- Message-level fields override basic command strategies such as default/last-round/all for that span.
- Higher-level strategy components can still apply around the override.
- If `loss_scale` contains values greater than `1`, configure non-binary loss-scale behavior for training.
- For consecutive `tool_call` messages, only the first call's loss configuration may take effect.

Use the template encoding helper with a local/cached processor to inspect decoded labels and loss-scale arrays.

## Template Mismatch for Base-to-Chat

Symptoms:

- Encoded text has wrong role markers.
- Assistant labels are empty or include user text.
- The model behaves like completion when chat was expected, or vice versa.

Fixes:

- Inspect model registry defaults before overriding.
- Use chat/instruct templates for chat-tuned checkpoints.
- Use generation-style templates or `use_chat_template=False` for base completion models.
- Pair `--model_type` and `--template` when using custom plugins or ambiguous local directories.
- Verify tokenizer special tokens exist for template separators.

## External Plugin Import Side Effects

Symptoms:

- CLI hangs before argument validation.
- Plugin downloads a model or starts a job during import.
- Re-running a command mutates global mappings unexpectedly.

Fixes:

- Keep plugins import-only: class definitions plus registry calls.
- Put demos and smoke tests under `if __name__ == "__main__":`.
- Avoid network, subprocess, training, inference, and large reads at import time.
- Use unique names instead of overwriting built-ins.
- Validate with `inspect_registries.py --external-plugin plugin.py` before training.

## Model Type or Template Override Mistakes

Symptoms:

- `model_type not in MODEL_MAPPING`.
- `template_type not in TEMPLATE_MAPPING`.
- Automatic template matching reports multiple or no candidates.
- A custom architecture does not auto-match.

Checks:

- The plugin is passed with `--external_plugins` on every command that needs it.
- `register_model` and `register_template` execute at import time.
- `architectures` matches the model's `config.json` value when relying on auto-detection.
- `ModelGroup.template` or `ModelMeta.template` points to an existing registered template.
- The model path suffix and ID are not misleading ms-swift into a different built-in type.

## Offline or Local Repo Model Loading

Symptoms:

- Registry inspection succeeds but `get_processor` fails.
- Offline jobs try to access a hub.
- Local model directories lack processor/tokenizer files.

Fixes:

- Use a local model directory with tokenizer/processor config files.
- Pass `download_model=False` when probing with `get_processor`.
- Install optional packages required by the model family only when the chosen workflow needs them.
- Separate registry validation from processor/template encoding validation.
- Do not use eval or Megatron extras as a prerequisite for data/model customization unless the target workflow explicitly needs them.

## Custom Dataset Info Path Problems

Symptoms:

- Dataset metadata loads but files are not found.
- A local alias works from one directory but not another.

Rules:

- Relative `dataset_path` values in dataset info are resolved relative to the metadata file.
- Direct `--dataset ./file.jsonl` is resolved by the current process working directory.
- Keep metadata and data files together for portability.
- Avoid absolute local paths in reusable config snippets.

## Triage Order

1. Validate raw rows with `validate_dataset_rows.py`.
2. Inspect registries and plugin effects with `inspect_registries.py`.
3. Check a local/cached processor and template with `inspect_template_encoding.py --attempt --no-download`.
4. Only then route to full training, inference, RLHF, export, or eval workflows.
