# OpenPrompt template/verbalizer API reference

Source evidence: `openprompt/prompt_base.py`, `openprompt/prompts/*.py`, `openprompt/utils/calibrate.py`, and the docs/tutorial files listed in `../SKILL.md`.

## Template base contract

### `Template(tokenizer, placeholder_mapping={'<text_a>': 'text_a', '<text_b>': 'text_b'})`

Base class in `openprompt/prompt_base.py`.

Important behavior:

- `text` setter calls `on_text_set()` and then `_check_template_format()`.
- `_check_template_format()` raises when no `mask` piece exists.
- `parse_text(text)` splits a template string into a list of dictionaries. It uses `{` and `}` as mixed-token delimiters and supports nested braces in dict fragments.
- `wrap_one_example(InputExample)` fills `placeholder` and `meta` fields, computes `loss_ids` and `shortenable_ids`, and returns `[wrapped_parts_to_tokenize, wrapped_parts_not_tokenize]`.
- `from_file(path, choice=0)` reads line `choice` from a local template file and assigns it to `text`.
- `from_config(config, **kwargs)` forwards config keys that match the template constructor and optionally loads from `file_path` when `text` is absent. `text` and `file_path` together raise a runtime error.

Template grammar keys supported by source code and docs:

| Key | Meaning | Notes |
|---|---|---|
| `{"placeholder": "text_a"}` / `text_b` | Fill from `InputExample.text_a` or `.text_b` | `placeholder_mapping` can remap token names to fields. |
| `{"meta": "field"}` | Fill from `InputExample.meta['field']` | Required for task-specific fields such as entity names, choices, or explanations. |
| `{"mask"}` | Prediction position | Ordinary classification usually uses one mask; PTR and LM-BFF generation can use several. |
| `{"text": "literal"}` | Literal text piece | The `text` key can be omitted by writing literal text outside braces. |
| `{"special": "<sep>"}` | Special token inserted by name | Keep tokenizer/model compatibility in mind. |
| `{"soft"}` / `{"soft": "seed"}` | Learned soft token(s) | Used by `MixedTemplate` and P-tuning templates. |
| `shortenable` | Whether a piece may be truncated | Defaults to true for placeholders and false for template text/special/mask pieces. |
| `post_processing` | Lambda/string hook applied before insertion | Source uses `eval`; validate untrusted templates before running. |
| `soft_id` | Share/reuse soft token ids in `MixedTemplate` | Must be a positive int. |
| `duplicate`, `same` | Expand many soft tokens | `same=True` makes duplicated soft tokens share an id. |

## Template implementations

| Loader key | Class | Constructor highlights | Operational notes |
|---|---|---|---|
| `manual_template` | `ManualTemplate(tokenizer, text=None, placeholder_mapping=...)` | Text-only prompt. | Calls `parse_text` in `on_text_set`; no model required. |
| `mixed_template` | `MixedTemplate(model, tokenizer, text=None, placeholder_mapping=...)` | Text plus `soft` pieces initialized from model embeddings. | Requires PLM model; registers `soft_token_ids`; textual `soft` values are tokenized into soft-token initializers. |
| `soft_template` | `SoftTemplate(model, tokenizer, text=None, soft_embeds=None, num_tokens=20, initialize_from_vocab=True, random_range=0.5, placeholder_mapping=...)` | Prepends learned soft embeddings to the normal wrapped input. | If `text` is omitted, defaults depend on whether the example has `text_b`. Removes prepended-token logits for non-encoder-decoder models. |
| `prefix_tuning_template` | `PrefixTuningTemplate(model, tokenizer, mapping_hook=None, text=None, num_token=5, prefix_dropout=0.0, mid_dim=512, using_encoder_past_key_values=True, using_decoder_past_key_values=True, ...)` | Injects prefix past-key-values. | Source supports T5 and GPT2-style config branches; warns/limits DataParallel usage. |
| `ptuning_template` | `PtuningTemplate(model, tokenizer, text=None, prompt_encoder_type='lstm', placeholder_mapping=...)` | Mixed soft tokens with LSTM or MLP prompt encoder. | `prompt_encoder_type` must be `lstm` or `mlp`. |
| `ptr_template` | `PTRTemplate(model, tokenizer, text=None, placeholder_mapping=...)` | P-tuning template variant for PTR relation extraction. | Uses MLP prompt encoder and is expected to contain multiple masks. |
| not in loader map | `LMBFFTemplateGenerationTemplate(tokenizer, verbalizer, text=None, placeholder_mapping=...)` | Special template for LM-BFF template search. | Injects `example.meta['labelword']` from the manual verbalizer; generated parsed templates may need a no-parse `ManualTemplate` subclass. |

Use `openprompt.prompts.load_template(config, **kwargs)` when a yacs config has `config.template` set to one of the loader keys above. The loader looks up `TEMPLATE_CLASS[config.template]` and calls `.from_config(config[config.template], **kwargs)`.

## Verbalizer base contract

### `Verbalizer(tokenizer=None, classes=None, num_classes=None)`

Base class in `openprompt/prompt_base.py`.

Important behavior:

- `classes` and `num_classes` must agree when both are provided.
- If `label_words` is a dict, `classes` must be set and dict keys must exactly match `classes`; the dict is sorted to class order.
- `from_file(path, choice=0)` accepts:
  - `.txt`/`.csv`: class lines; comma-separated label words per class; blank lines separate alternative verbalizers.
  - `.json`/`.jsonl`: parsed with `json.load`, so OpenPrompt expects a full JSON document even when the extension is `.jsonl`; the document can be a dict or a list of dict/list verbalizers.
- `register_calibrate_logits(logits)` stores detached logits used by calibrating verbalizers.
- `handle_multi_token(..., multi_token_handler)` supports `first`, `max`, or `mean` where implemented.

## Verbalizer implementations

| Loader key | Class | Constructor highlights | Operational notes |
|---|---|---|---|
| `manual_verbalizer` | `ManualVerbalizer(tokenizer, classes=None, num_classes=None, label_words=None, prefix=' ', multi_token_handler='first', post_log_softmax=True)` | Fixed label-word projection. | Adds `prefix` unless a word starts with `<!>`; multiple label words per class are averaged after projection. |
| `one2one_verbalizer` | `One2oneVerbalizer(tokenizer, num_classes=None, classes=None, label_words=None, prefix=' ', multi_token_handler='first', post_log_softmax=True)` | One label word per class. | Raises/asserts if a class has multiple label words; warns if tokenizer splits a word. |
| `knowledgeable_verbalizer` | `KnowledgeableVerbalizer(tokenizer=None, classes=None, prefix=' ', multi_token_handler='first', max_token_split=-1, verbalizer_lr=5e-2, candidate_frac=0.5, pred_temp=1.0, **kwargs)` | Manual-style verbalizer expanded by external label-word lists. | Deletes duplicate words after the first class; with calibration, filters low-prior candidates. |
| `automatic_verbalizer` | `AutomaticVerbalizer(tokenizer=None, num_candidates=1000, label_word_num_per_class=1, num_searches=1, score_fct='llr', balance=True, num_classes=None, classes=None, init_using_split='train', **kwargs)` | Learns/selects label words from accumulated training logits. | Before `optimize_to_initialize()`, predictions are random placeholder logits. `from_file()` is not implemented. |
| `generation_verbalizer` | `GenerationVerbalizer(tokenizer, classes=None, num_classes=None, is_rule=False, label_words=None)` | Fills `InputExample.tgt_text` from label words or rule-like template expressions. | When `is_rule=True`, label words may be template fragments such as `{"meta":"choice1"}`. Does not support `soft`, `mask`, or `special` inside verbalizer rules. |
| `soft_verbalizer` | `SoftVerbalizer(tokenizer, model, classes=None, num_classes=None, label_words=None, prefix=' ', multi_token_handler='first')` | Replaces/copies the PLM output head for trainable class logits. | Exposes `group_parameters_1` and `group_parameters_2` for separate optimizer groups. |
| `proto_verbalizer` | `ProtoVerbalizer(tokenizer, model, classes=None, num_classes=None, label_words=None, prefix=' ', multi_token_handler='first', post_log_softmax=True, lr=1e-3, mid_dim=64, epochs=5, multi_verb='multi')` | Prototype-based few-shot verbalizer. | Needs a model hidden size and a later `train_proto(...)` call for prototype mode. |
| `ptr_verbalizer` | `PTRVerbalizer(tokenizer, classes=None, num_classes=None, label_words=None)` | Combines per-mask one-to-one verbalizers with logic rules. | `label_words[class]` must have one entry per mask and all classes must have equal mask count. |

Use `openprompt.prompts.load_verbalizer(config, **kwargs)` when `config.verbalizer` is set to one of the loader keys above. `load_template_generator(config, **kwargs)` supports `config.template_generator.plm.model_name == 't5'`; `load_verbalizer_generator(config, **kwargs)` supports `config.plm.model_name == 'roberta'`.

## LM-BFF generator APIs

- `T5TemplateGenerator(model, tokenizer, tokenizer_wrapper, verbalizer, max_length=20, target_number=2, beam_width=100, length_limit=None, forbidden_word_ids=[3, 19794, 22354], config=None)` searches template text with a T5 generation model.
- `RobertaVerbalizerGenerator(model, tokenizer, candidate_num=100, label_word_num_per_class=100)` searches label words from masked-LM probabilities and rejects RoBERTa tokens not starting with `Ġ`.
- Both generators accumulate examples/logits in buffers and are heavyweight; prefer static asset design unless the user explicitly requests LM-BFF search and has approved model/data/GPU cost.

## Calibration API

`openprompt.utils.calibrate.calibrate(prompt_model: PromptForClassification, dataloader: PromptDataLoader) -> torch.Tensor`

- Runs `prompt_model.forward_without_verbalize` over a support/context dataloader and returns average logits at mask positions.
- Register with `prompt_model.verbalizer.register_calibrate_logits(cc_logits)`.
- Source examples calibrate `ManualVerbalizer` and `KnowledgeableVerbalizer`; shape must match the verbalizer's projected label-word space.
