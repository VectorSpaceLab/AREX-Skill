# API Reference: Pipeline Basics

This reference covers the package-usage surface needed for a minimal OpenPrompt pipeline.

Verified against the inspection stack used for this draft:

- OpenPrompt 1.0.1
- Python 3.8.20
- torch 1.13.1+cpu
- transformers 4.19.0
- yacs 0.1.8

## Core imports

```python
from openprompt import PromptDataLoader, PromptForClassification, PromptForGeneration
from openprompt.plms import load_plm
from openprompt.data_utils import InputExample, InputFeatures
```

## Verified signatures

### `InputExample`

```python
(guid=None, text_a='', text_b='', label=None, meta: Union[Dict, NoneType] = None, tgt_text: Union[str, List[str], NoneType] = None)
```

Raw example container. Typical fields:

- `guid`
- `text_a`, `text_b`
- `label`
- `meta`
- `tgt_text`

### `InputFeatures`

```python
(input_ids: Union[List, torch.Tensor, NoneType] = None, inputs_embeds: Union[torch.Tensor, NoneType] = None, attention_mask: Union[List[int], torch.Tensor, NoneType] = None, token_type_ids: Union[List[int], torch.Tensor, NoneType] = None, label: Union[int, torch.Tensor, NoneType] = None, decoder_input_ids: Union[List, torch.Tensor, NoneType] = None, decoder_inputs_embeds: Union[torch.Tensor, NoneType] = None, soft_token_ids: Union[List, torch.Tensor, NoneType] = None, past_key_values: Union[torch.Tensor, NoneType] = None, loss_ids: Union[List, torch.Tensor, NoneType] = None, guid: Union[str, NoneType] = None, tgt_text: Union[str, NoneType] = None, use_cache: Union[bool, NoneType] = None, encoded_tgt_text: Union[str, NoneType] = None, input_ids_len: Union[int, NoneType] = None, **kwargs)
```

Tokenized feature container.

- `InputFeatures.collate_fct(batch)` is the loader collator.
- Keep tokenizer output keys disjoint from metadata keys such as `label` and `guid` when building features by hand.

### `PromptDataLoader`

```python
(dataset: Union[torch.utils.data.dataset.Dataset, List], template: openprompt.prompt_base.Template, tokenizer_wrapper: Union[openprompt.plms.utils.TokenizerWrapper, NoneType] = None, tokenizer: transformers.tokenization_utils.PreTrainedTokenizer = None, tokenizer_wrapper_class=None, verbalizer: Union[openprompt.prompt_base.Verbalizer, NoneType] = None, max_seq_length: Union[str, NoneType] = 512, batch_size: Union[int, NoneType] = 1, shuffle: Union[bool, NoneType] = False, teacher_forcing: Union[bool, NoneType] = False, decoder_max_length: Union[int, NoneType] = -1, predict_eos_token: Union[bool, NoneType] = False, truncate_method: Union[str, NoneType] = 'tail', drop_last: Union[bool, NoneType] = False, **kwargs)
```

Loader contract:

- Dataset must be iterable and sized.
- Pass either `tokenizer_wrapper` or `tokenizer_wrapper_class` plus `tokenizer`.
- The wrapper-class constructor is filtered by parameter name before kwargs are forwarded.
- `template.wrap_one_example(example)` must return `[parts_to_tokenize, metadata_dict]`.
- `verbalizer.wrap_one_example(example)` runs before the template when present.
- Avoid duplicate keys between wrapper output and metadata. `label` is the common collision.

### `PromptForClassification`

```python
(plm: transformers.utils.dummy_pt_objects.PreTrainedModel, template: openprompt.prompt_base.Template, verbalizer: openprompt.prompt_base.Verbalizer, freeze_plm: bool = False, plm_eval_mode: bool = False)
```

Classification wrapper.

- Composes `PromptModel` plus a verbalizer.
- `forward(batch)` returns label logits.

### `PromptForGeneration`

```python
(plm: transformers.utils.dummy_pt_objects.PreTrainedModel, template: openprompt.prompt_base.Template, freeze_plm: bool = False, plm_eval_mode: bool = False, gen_config: Union[yacs.config.CfgNode, NoneType] = None, tokenizer: Union[transformers.tokenization_utils.PreTrainedTokenizer, NoneType] = None)
```

Generation wrapper.

- `forward(batch)` computes generation loss.
- `generate(batch, verbose=False, **kwargs)` delegates to the underlying `GenerationMixin` flow.
- Use a generation-aware template and loader settings such as `teacher_forcing=True` and `predict_eos_token=True`.

### `load_plm`

```python
(model_name, model_path, specials_to_add=None)
```

PLM loader.

- Returns `(plm, tokenizer, model_config, WrapperClass)`.
- Supported model families in this source snapshot: `bert`, `roberta`, `albert`, `electra`, `gpt`, `gpt2`, `opt`, `gptj`, `t5`, `t5-lm`.
- May download from Hugging Face unless `model_path` is already cached locally.
- GPT/OPT families add `<pad>` when needed.

## Companion object

`PromptModel` is the shared container used by both pipeline wrappers. Use it indirectly unless you need custom composition.
