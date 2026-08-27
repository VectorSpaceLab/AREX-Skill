# Troubleshooting converters and datasets

Use this matrix when PyRIT converter, normalizer, seed, or dataset work fails. For target credentials/capabilities route to `../targets-scorers/SKILL.md`; for attack execution route to `../attacks-scenarios/SKILL.md`; for memory/session initialization route to `../setup-memory-core/SKILL.md`.

## Quick diagnosis checklist

1. Identify the current value's `PromptDataType` (`text`, `image_path`, `audio_path`, etc.).
2. Check each converter's `SUPPORTED_INPUT_TYPES` and `SUPPORTED_OUTPUT_TYPES`.
3. If a stack is involved, trace output type from one converter into the next converter.
4. If a target send is involved, verify target capabilities before blaming the converter.
5. If a dataset is involved, distinguish local YAML validation from remote provider download/cache behavior.
6. If a template is involved, check both declared `parameters` and runtime render kwargs.

## Converter failures

| Symptom/error | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: Input type not supported` | The converter was called with a data type outside `SUPPORTED_INPUT_TYPES`. Common example: text-only converters called with `image_path`. | Inspect `converter.supported_input_types`; set `input_type="text"` for text values; insert a converter that changes modality only when its output is accepted by the next converter/target. |
| Converted output reaches target but target rejects it | Final `output_type` is incompatible with the target's input modalities. | Route to `../targets-scorers/SKILL.md` for target capability selection. For no-secret dry runs, keep final output `text` and use `TextTarget` only in the target/scorer workflow. |
| Stack silently skips a message piece | `ConverterConfiguration.indexes_to_apply` or `prompt_data_types_to_apply` filtered it out based on piece index or *current* converted data type. | Print/inspect each `MessagePiece` index and `converted_value_data_type` before the stack. Remove filters or update them to match the current state. |
| Only part of a prompt was converted unexpectedly | `convert_tokens_async()` found `⟪...⟫` spans and converted only those spans. | Remove token delimiters or call `convert_async()` for whole-value conversion. |
| `Uneven number of start tokens and end tokens` | Token-delimited selective conversion has mismatched delimiters. | Balance `⟪` and `⟫`, or pass custom `start_token`/`end_token` consistently to the normalizer and converter calls. |
| `Input type must be text when start or end tokens are present` | Token markers were used with a non-text input type. | Token-based selective conversion is text-only; use a modality-specific converter for media. |
| `NoOpConverter` import fails | `NoOpConverter` is not exported from `pyrit.converter` in this checkout. | Use an empty converter list (`[]`) or omit converter configuration when no conversion is needed. |

## Optional media/audio/speech dependencies

| Converter family | Common failure | Action |
| --- | --- | --- |
| Audio-to-audio converters (`AudioEchoConverter`, `AudioFrequencyConverter`, `AudioSpeedConverter`, `AudioVolumeConverter`, `AudioWhiteNoiseConverter`) | Missing or incompatible audio processing dependency, invalid input file, unsupported audio encoding, or output format mismatch. | Keep no-network smoke tests text-only. For real audio, verify local file exists, use supported formats, and check that the selected environment includes PyRIT's base audio dependencies. |
| Azure speech converters (`AzureSpeechTextToAudioConverter`, `AzureSpeechAudioToTextConverter`) | `ModuleNotFoundError` for `azure.cognitiveservices.speech`, missing Azure Speech region/key/resource ID, unsupported compressed audio. | Install the `speech` optional extra only when this capability is in scope; configure credentials through the setup/target workflow; use `.wav` where required. Do not run in no-secret smoke tests. |
| Image/video converters | Missing `opencv` for video/image-to-video paths, missing/invalid local image file, unsupported image format, target cannot accept final modality. | Install optional `opencv` only when needed; verify local files; route target acceptance to `../targets-scorers/SKILL.md`. |
| LLM/image prompt converters | Converter calls a model target or image target under the hood. | Treat as service-backed. Configure/authorize the target first; do not run in offline smoke. |
| HuggingFace/tokenizer normalizer | Model/tokenizer download, gated model token, or missing `transformers` stack. | Avoid `TokenizerTemplateNormalizer.from_model()` in no-network checks. Use only after model/cache/token constraints are approved. |

## LLM-backed converter target failures

| Symptom/error | Likely cause | Fix |
| --- | --- | --- |
| Constructor complains that `converter_target` is required | LLM-backed converters require a chat-capable `PromptTarget` unless a default target has been configured. | Configure a target in `../targets-scorers/SKILL.md` and pass it as `converter_target=...`, or initialize PyRIT defaults through `../setup-memory-core/SKILL.md` when appropriate. |
| Target validation fails when constructing a converter | The target does not satisfy chat/multi-turn requirements expected by `CHAT_TARGET_REQUIREMENTS`. | Use a proper chat target for rewriting/translation/variation. Do not use write-only or non-chat targets as converter LLMs. |
| Converter returns invalid JSON or retries | Some converters, such as variation-style converters, parse model output and retry on invalid JSON. | Lower temperature or adjust the converter prompt/template. Keep retry limits bounded. For repeated invalid output, test the converter target separately. |
| Credential, rate-limit, or network errors | Service-backed converter calls an external target. | Treat as target troubleshooting; route to `../targets-scorers/SKILL.md`. Do not hide this under dataset/converter validation. |

## Regex and search/replace failures

| Symptom/error | Likely cause | Fix |
| --- | --- | --- |
| `re.error` from `SearchReplaceConverter` | `pattern` is an invalid Python regular expression. | Test `re.compile(pattern, flags=regex_flags)` first. Use `re.escape(literal_text)` for literal search. |
| Too much text replaced | Regex pattern is too broad, greedy, or missing word boundaries. | Add anchors or word boundaries, e.g. `r"\btoken\b"`; test on representative benign strings before running a larger workflow. |
| Replacement result changes between runs | `replace` was a list and PyRIT chooses with `random.choice()`. | Use a single string or a one-item list for deterministic runs. |
| Case-insensitive replacement not working | Missing `regex_flags`. | Pass `regex_flags=re.IGNORECASE` (or combined integer flags) and import `re` in your calling code. |
| Replacement uses backslashes unexpectedly | Python regex replacement strings interpret escape sequences/backreferences. | Use raw strings and explicit escaping; prefer simple replacement strings unless backreferences are intended. |

## Message normalizer failures

| Symptom/error | Likely cause | Fix |
| --- | --- | --- |
| `Messages list cannot be empty` | A message normalizer was called with `[]`. | Pass at least one `Message`. |
| `Data type '...' is not yet supported for chat message content` | `ChatMessageNormalizer` supports text, image path, audio path, and URL content for chat formatting; other types need custom handling. | Convert unsupported data to a supported type first or choose a target-specific normalizer. |
| `Unsupported audio format` | Chat normalization for audio accepts `.wav` and `.mp3`. | Convert audio to `.wav` or `.mp3` before normalization. |
| `Audio file not found` / image path errors | Message piece points to a missing local file. | Make paths relative to the current working context or use a managed data path; verify existence before normalization. |
| `schema_instructions_template must contain '{schema_json}'` | Custom `JsonSchemaNormalizer` template omitted the required placeholder. | Include `{schema_json}` exactly once where the schema should be rendered. |
| System messages rejected by a model | Target/model does not support system role. | Use `GenericSystemSquashNormalizer`, `ChatMessageNormalizer(system_message_behavior="squash"|"ignore")`, or `use_developer_role=True` when the target expects developer-role instructions. |

## Seed YAML and dataset validation failures

| Symptom/error | Likely cause | Fix |
| --- | --- | --- |
| YAML file is empty or top level is not a mapping | `safe_load()` returned `None` or a list/scalar. | Make the file a mapping with keys such as `dataset_name`, `data_type`, and `seeds`. |
| `SeedDataset cannot be empty` | `seeds` is missing, empty, or `None`. | Add at least one seed entry under `seeds:`. |
| Extra/unknown field validation error | Seed models use `extra="forbid"`; the field name is not part of the versioned schema. | Check field spelling. In this version, use `seeds:` for datasets. Do not use pre-set `prompt_group_id` in seed dicts. |
| `prompt_group_id should not be set in seed data` | YAML/dict input tried to assign IDs directly. | Use `prompt_group_alias` to group related seeds; let `SeedDataset.from_dict()` generate IDs. |
| `Unable to infer data_type from file extension` | `SeedPrompt` saw an existing file path with an unknown extension and no explicit `data_type`. | Set `data_type` explicitly or use a supported media extension. |
| Programmatic scalar list validation error | Programmatic construction passed a string to a list field such as `authors` or `parameters`. | Pass `authors=["name"]`, `parameters=["param"]`, etc. YAML loaders wrap some scalars, but model constructors stay strict. |
| Inline schema + schema name raises | Both `response_json_schema` and `response_json_schema_name` were set. | Set only one. Prefer `response_json_schema_name` for a bundled schema, inline only for custom shapes. |
| Unknown `response_json_schema_name` | Name is not registered in PyRIT's common schema registry. | Use one of the bundled names (`true_false_with_rationale`, `scale_with_rationale`, `adversarial_chat`) or register a schema in application code before constructing seeds. |

## Template parameter failures

| Symptom/error | Likely cause | Fix |
| --- | --- | --- |
| `Template must have these parameters: ...` | `SeedPrompt.from_yaml_with_required_parameters()` found missing names in the `parameters` field. | Add every required placeholder name to `parameters:` in YAML. |
| `Error rendering template ... UndefinedError` | `render_template_value()` was called without all variables used by the Jinja template. | Supply all kwargs (`template.render_template_value(name="...")`) or validate earlier with `from_yaml_with_required_parameters()`. |
| Template loads but still contains `{{ name }}` | YAML loading uses silent rendering and preserves unresolved simple placeholders. | This is expected until runtime render. Before execution, call strict `render_template_value()` with concrete values. |
| Jinja control structure preserved unexpectedly | Silent render avoids evaluating loops/conditionals when required collection variables are missing. | Provide loop variables at strict render time or avoid control structures in simple seed templates. |
| Remote/untrusted text behaves like a template | Text was loaded through a trusted YAML path or `is_jinja_template=True`. | Treat only reviewed local YAML as trusted templates. For untrusted text, construct `SeedPrompt(value=..., is_jinja_template=False)` or escape with `Seed.escape_for_jinja()`. |

## Remote dataset and cache failures

| Symptom/error | Likely cause | Fix |
| --- | --- | --- |
| `Dataset(s) not found: ... Available datasets: ...` | Requested `dataset_names` do not match provider `dataset_name` values. | Discover names first or use CLI listing via `../cli-backend-scanner/SKILL.md`; pass exact names. |
| Fetch hangs or downloads too much | `fetch_datasets_async()` was called with `dataset_names=None`, so every registered provider is fetched with concurrency. | Always pass explicit `dataset_names` for bounded work. Set `max_concurrency=1` for brittle networks. |
| Public URL status error | Remote source URL failed or changed. | Retry later, switch to cached data if available, or use a local dataset. Keep the failure explicit in handoff. |
| HuggingFace load error | Dataset name/config/split changed, network unavailable, cache missing/corrupt, or gated dataset requires a token. | Verify dataset name/config/split; use `cache=True` when cached data is acceptable; provide a token only through approved secret handling; avoid gated downloads in no-secret runs. |
| Invalid file type | Remote loader supports `json`, `jsonl`, `csv`, and `txt` for simple file handlers. | Convert the file or implement a provider-specific parser. |
| ZIP inner file not found | Requested member path is not present in archive. | Inspect archive member names in a bounded diagnostic or update provider configuration. |
| Cache seems stale | `cache=True` reused an existing cached dataset. | Use `cache=False` only when a fresh network fetch is approved; document that it can redownload. |
| Cache write/read permission failure | PyRIT data cache directory is not writable in the current environment. | Initialize/configure PyRIT data paths through `../setup-memory-core/SKILL.md` or run with a writable user data location. Do not hardcode machine-specific cache paths in reusable skill content. |

## Safe minimal recovery actions

- For converter stack problems, reduce to one offline text converter at a time and verify `output_text`/`output_type` after each step.
- For normalizer problems, build a tiny `Message.from_prompt(..., role="user")` and verify the normalizer without a target send.
- For YAML problems, load a one-seed local `SeedDataset` first, then add metadata, grouping, schema, and templates incrementally.
- For remote dataset problems, do not fetch all providers as a diagnostic. Discover names, choose one exact dataset, and decide whether cache reuse or fresh download is allowed.
- For target/credential failures, stop converter/dataset debugging and route to the target/scorer or setup sub-skill.
