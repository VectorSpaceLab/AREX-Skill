# Data And Template Troubleshooting

Use this checklist before running a full training job. Most data issues are detectable from `dataset_info.json`, one or two sample rows, and the training config.

## Undefined Dataset

Symptom: `Undefined dataset NAME in dataset_info.json`.

Checks:

- `dataset:` and `eval_dataset:` names must exactly match top-level keys in `dataset_info.json`.
- Comma-separated names are split and trimmed, so accidental spaces inside the name can matter only if they are part of the file's key.
- If using `dataset_dir: ONLINE`, local `dataset_info.json` is bypassed and names are treated as hub dataset identifiers.

Fix: add a top-level entry for the exact name or update the config to use an existing key.

## Missing Dataset Info

Symptom: cannot open `dataset_info.json`, or no local custom dataset is found.

Checks:

- `dataset_info.json` must be inside `dataset_dir`; default `dataset_dir` is `data`.
- A missing registry may be tolerated only when no dataset names are supplied; with `dataset:` set, it is an error.
- If `dataset_dir` starts with `REMOTE:`, LlamaFactory downloads the registry from a dataset repository.

Fix: place the registry file in the configured `dataset_dir`, or explicitly use a remote/online mode.

## Wrong File Name Or File Type

Symptoms: `File ... not found`, `Allowed file types`, or `File types should be identical`.

Checks:

- Local `file_name` is resolved under `dataset_dir`.
- A directory entry loads all files in that directory; their extensions must map to the same dataset loader type.
- Supported local file types include JSON, JSONL, CSV, Parquet, and Arrow.

Fix: correct `file_name`, avoid mixed-extension directories, or point to a single file.

## Wrong Columns Or Tags

Symptoms: key errors, dropped abnormal examples, invalid role tag warnings, or empty valid sample count.

Checks:

- Registry `columns` values must be real keys in row objects.
- Alpaca defaults are `instruction`, `input`, and `output`; remap if your rows use names like `question`, `answer`, or `messages`.
- ShareGPT defaults are `conversations`, `from`, and `value`; OpenAI-style rows need tags such as `role_tag: role` and `content_tag: content`.
- For ShareGPT, role order after an optional system message must alternate user-like then assistant-like.

Fix: update `columns`/`tags`, or transform rows to the expected shape.

## Ranking Chosen/Rejected Mismatch

Symptoms: `The dataset is not applicable in the current training stage`, invalid examples in RM/DPO/ORPO/SimPO, or chosen/rejected role warnings.

Checks:

- Reward modeling stage expects `ranking: true`; non-RM stages reject `ranking: true` datasets.
- Alpaca ranking requires string `chosen` and `rejected` columns.
- ShareGPT/OpenAI ranking requires object `chosen` and `rejected` messages, and both must be assistant-like according to the configured tags.
- Prompt messages in ranking rows should not already include the final assistant answer.

Fix: set `ranking` to match the stage, map both chosen/rejected columns, and ensure the chosen/rejected values have assistant-like roles.

## KTO Feedback Problems

Symptoms: KTO preprocessing drops rows or warns that the dataset only has one preference type.

Checks:

- `kto_tag` must map to a boolean field, not strings like `"true"` unless transformed first.
- The row still needs a normal response message/content.
- Healthy KTO data should contain both desirable and undesirable examples.

Fix: convert feedback to booleans and balance representative positive/negative rows.

## Malformed Tool Calling

Symptoms: invalid role tag, missing tool responses, or the assistant learns tool results as normal text.

Checks:

- ShareGPT tool calls should use the function-call role and tool results should use the observation role.
- OpenAI assistant `tool_calls` should contain function objects; tool-result messages should use the configured observation tag.
- The `tools` column maps only the tool schema/description; it does not replace function-call/observation turns.
- If `tools` is a dict/list in OpenAI rows, the converter stringifies it; in other formats, keep it as a string unless a template expects otherwise.

Fix: align roles and tags, and include both tool-call messages and tool-result messages in the conversation.

## Media Path And Placeholder Issues

Symptoms: media missing warnings, placeholder-count value errors, or template says the model does not support image/video/audio input.

Checks:

- Count `<image>`, `<video>`, and `<audio>` placeholders across message content.
- The mapped `images`, `videos`, and `audios` columns must contain the same number of entries as placeholders.
- Local media paths are looked up under `media_dir`, defaulting to `dataset_dir`; if not found, LlamaFactory warns and keeps the original path.
- The selected `template:` and loaded processor must support the modality.

Fix: align placeholder counts, set `media_dir`, and choose a multimodal-capable model/template pair.

## Remote Hub Selection

Symptoms: unexpected dataset source, hub authentication errors, or local file ignored.

Checks:

- Hub URL keys have priority over `file_name`; a registry entry with `hf_hub_url` will not load the local file unless the hub key is removed.
- ModelScope/OpenMind can be selected by environment helper behavior when their URLs exist and Hugging Face is absent or not preferred.
- `subset`, `split`, and `folder` are passed to remote loaders.

Fix: keep only the intended source key in custom entries, or make remote/local entries separate names.

## Tokenized Path Confusion

Symptoms: edits to `dataset_info.json` or raw rows do nothing.

Checks:

- Existing `tokenized_path` makes LlamaFactory load preprocessed data and ignore other data arguments.
- Non-existing `tokenized_path` makes LlamaFactory save tokenized output after preprocessing.
- `streaming` is incompatible with saving tokenized data.

Fix: remove `tokenized_path` during raw data debugging, delete stale tokenized output, or use a new path after changing raw data.

## Template Mismatch

Symptoms: unknown template, wrong prompt formatting, missing pad/eos warnings, or multimodal unsupported errors.

Checks:

- `template:` must be a registered template name or a tokenizer-provided chat template must be usable.
- Reasoning model data should match `enable_thinking` and `preserve_thinking` expectations.
- Tool-calling datasets need a template/tool format that actually renders tools and function messages.
- Multimodal rows need a template whose multimodal plugin accepts their placeholders.

Fix: select the model-family template, keep thinking mode consistent between train and inference, and verify one rendered training example before scaling up.
