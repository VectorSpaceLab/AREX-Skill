# Templates And Processing

LlamaFactory v0 separates row conversion from tokenization. Registry conversion normalizes raw data rows into messages and metadata; templates then turn those messages into token IDs; processors select the training-stage-specific output fields.

## Conversion Pipeline

A typical v0 data path is:

1. Read `dataset:` and `eval_dataset:` names from the training config.
2. Resolve each name through `dataset_info.json` in `dataset_dir`, or through online hub lookup when `dataset_dir: ONLINE`.
3. Load the raw dataset from hub, script, cloud JSON, local file, or local directory.
4. Convert each raw row with the configured dataset converter: `alpaca`, `sharegpt`, or `openai`.
5. Preprocess the aligned fields through a processor chosen by training stage and data flags.
6. Optionally save or load tokenized data from `tokenized_path`.

The aligned conversion output has these fields:

```text
_prompt   list of user/assistant history messages ending with a user-like prompt
_response list of one response for SFT, two responses for ranking/KTO, or empty for unsupervised/pretraining
_system   string system prompt
_tools    string tool schema/description
_images   list or null
_videos   list or null
_audios   list or null
```

## Template Selection

Set `template:` in the training config to an installed LlamaFactory template name matching the model family, such as `llama3`, `qwen`, `qwen3`, `gemma`, `mistral`, or another name available in the template registry. If `template` is omitted and the tokenizer already has a chat template, LlamaFactory can use an `empty` placeholder-style template; otherwise an unknown or missing template is a data/template configuration problem.

A template controls:

- Prefix, system, user, assistant, function-call, observation, and tool slots.
- EOS and stop words, including whether to replace tokenizer EOS or add stop tokens.
- Whether to replace or synthesize a tokenizer Jinja chat template.
- Thinking-token behavior for reasoning templates.
- The multimodal plugin used to expand media placeholders and token IDs.

## Message Roles

Templates consume normalized role names: `user`, `assistant`, `observation`, and `function`. ShareGPT/OpenAI converters map source tags to these roles before preprocessing. Template encoding expects turns to alternate in user-like and assistant-like pairs; malformed role order usually drops examples during conversion or preprocessing.

For one-turn encoding, the prompt is every encoded message except the final response. For multi-turn SFT encoding, the processor creates prompt-response pairs from alternating messages and masks prompt tokens by default.

## Tool Calling

Tool metadata flows through `_tools` and is rendered by the template's `format_tools` behavior. Function calls and observations should be represented as messages, not only as a tool schema:

- ShareGPT: use `function_call` for assistant tool-call content and `observation` for tool results unless custom tags remap those values.
- OpenAI: assistant `tool_calls` are serialized from `tool_calls[*].function`; tool messages are accumulated as observation content.
- `tool_format` can affect function-calling prompt construction, but the dataset must still contain correctly ordered tool-call and observation turns.

Common static mistakes are putting a tool result in an assistant role, forgetting the `tools` column mapping, or using custom tags without matching `tags` in the registry.

## Reasoning And Thinking Flags

Reasoning templates can add or remove thought markers around assistant content. Relevant data arguments:

- `enable_thinking: true` keeps slow-thinking behavior and can add empty thought spans to responses when content lacks CoT.
- `enable_thinking: false` can place empty thought spans in prompts instead of labels for fast-thinking behavior.
- `enable_thinking: null` allows mixed behavior but is harder to reason about.
- `preserve_thinking: true` keeps thinking content in historical turns; otherwise historical thinking may be removed.

Keep the training and inference thinking mode consistent for reasoning models.

## Processor Selection By Stage

The dataset processor is selected from the training stage and generation/packing flags:

- `pt`: pretraining processor; usually uses document text mapped through the prompt column.
- `sft`: supervised processor; expects `_prompt` length to be odd and exactly one `_response`.
- `sft` with `packing: true`: packed supervised processor; drops examples longer than `cutoff_len` and packs shorter examples.
- `rm`: pairwise processor; expects ranking examples with chosen and rejected responses.
- `kto`: feedback processor; expects KTO-style paired real/empty responses and boolean feedback.
- PPO or prediction-generation paths use unsupervised-style processing.

Stage/ranking compatibility is enforced before tokenization: RM expects `ranking: true`, while non-RM stages reject ranking datasets.

## Masking And Length Behavior

Important data arguments:

- `cutoff_len`: maximum tokenized example length; packing internally subtracts one token to avoid padding issues.
- `train_on_prompt`: when false, prompt/source tokens receive ignore labels.
- `mask_history`: trains only on the last turn and is incompatible with `train_on_prompt`.
- `packing`: enables sequence packing for SFT; `neat_packing` forces packing and carries subsequence metadata.
- `preprocessing_batch_size` and `preprocessing_num_workers`: control tokenization map behavior.
- `streaming`: changes loading and cache behavior and is incompatible with `max_samples`.

If preprocessing logs `Cannot find valid samples`, inspect the converted `_prompt`/`_response` shape first: SFT needs odd prompt length plus one response; pairwise/KTO need odd prompt length plus at least two responses.

## Multimodal Template Checks

Multimodal plugins validate both model/template support and row consistency:

- A row with images requires the selected template/plugin to define an image token and the loaded processor to include an image processor.
- A row with videos requires a video-capable template/plugin and video processor or image processor fallback.
- A row with audios requires an audio token and audio feature extractor/processor.
- Placeholder counts must match the lengths of `images`, `videos`, and `audios` lists.

Examples:

```json
{"role": "user", "content": "<image><image>Compare these."}
```

requires two image entries in the mapped `images` column. A mismatch raises a value error during multimodal message processing, not during registry lookup.

## Tokenized Path

`tokenized_path` changes the whole data path:

- If it points to existing tokenized data, LlamaFactory loads it from disk and ignores other data arguments.
- If it does not exist, preprocessing runs and saves tokenized output there after successful processing.
- `streaming` cannot be used when saving tokenized data.

When debugging raw data format issues, remove or change `tokenized_path`; otherwise changes to `dataset_info.json` or row files may appear to have no effect.
