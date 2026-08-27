# Donut API Reference

This reference captures the Donut package surfaces verified during skill construction. Use it for API shape, object relationships, and data contracts; route workflow commands to the relevant sub-skill.

## Public package exports

Import from the package root:

```python
from donut import DonutConfig, DonutModel, DonutDataset, JSONParseEvaluator, load_json, save_json
```

The installed distribution name is `donut-python`; the import module is `donut`.

## Core signatures

| API | Verified signature | Use |
| --- | --- | --- |
| `DonutConfig` | `DonutConfig(input_size=[2560, 1920], align_long_axis=False, window_size=10, encoder_layer=[2, 2, 14, 2], decoder_layer=4, max_position_embeddings=None, max_length=1536, name_or_path='', **kwargs)` | Configure the Swin encoder, BART-style decoder, canvas size, and max sequence length. |
| `DonutModel` | `DonutModel(config)` | Instantiate a Donut model from a `DonutConfig`; this can initialize large encoder/decoder backbones. |
| `DonutModel.from_pretrained` | `DonutModel.from_pretrained(pretrained_model_name_or_path, *model_args, **kwargs)` | Load local or Hugging Face Donut checkpoints. The implementation passes `revision="official"` to Hugging Face model loading. |
| `DonutModel.inference` | `DonutModel.inference(image=None, prompt=None, image_tensors=None, prompt_tensors=None, return_json=True, return_attentions=False)` | Run autoregressive prediction from a PIL image or prepared tensors and a prompt string or prompt tensor. |
| `DonutDataset` | `DonutDataset(dataset_name_or_path, donut_model, max_length, split='train', ignore_id=-100, task_start_token='<s>', prompt_end_token=None, sort_json_key=True)` | Load Hugging Face-style datasets with `metadata.jsonl` rows and convert them into image tensors plus decoder labels/prompts. |
| `JSONParseEvaluator` | `JSONParseEvaluator()` | Compute normalized tree-edit-distance accuracy and global field-level F1 for JSON predictions. |

## Model object behavior

- `DonutModel` contains `encoder` and `decoder` members.
- The encoder is a Swin Transformer configured by `input_size`, `window_size`, and `encoder_layer`.
- `SwinEncoder.prepare_input(image, random_padding=False)` converts a PIL image to a normalized tensor by RGB conversion, optional long-axis rotation, resize, thumbnail fit, padding, and ImageNet normalization.
- The decoder wraps an XLM-Roberta tokenizer and MBart-style causal LM. `<sep/>` is the built-in list separator token.
- In CUDA mode, inference casts image tensors to half precision before generation. On CPU, encoder hidden states are kept in float32.

## Loading checkpoints

Use the inference sub-skill for full commands. Programmatically:

```python
from donut import DonutModel

model = DonutModel.from_pretrained("naver-clova-ix/donut-base-finetuned-cord-v2")
model.eval()
```

Operational notes:

- Local paths avoid Hub download and authentication/network issues.
- Donut's loader requests the `official` branch/revision of NAVER model repositories.
- For GPU inference, call `model.half(); model.to("cuda")` only when `torch.cuda.is_available()` is true.
- For CPU inference, use `model.to("cpu")`; do not call `half()` for CPU execution.

## Inference output contract

`DonutModel.inference(...)` returns a dictionary:

```python
{
    "predictions": [parsed_json_or_raw_string],
    # optional when return_attentions=True:
    "attentions": {"self_attentions": ..., "cross_attentions": ...}
}
```

With `return_json=True`, the first prediction is parsed by `token2json`. With `return_json=False`, it is the decoded token string after the first task token, EOS token, and pad token are removed.

Common prompts:

| Task | Prompt form |
| --- | --- |
| CORD or receipt parsing | `<s_cord>` |
| RVL-CDIP document classification | `<s_rvlcdip>` |
| TrainTicket parsing | `<s_zhtrainticket>` |
| DocVQA | `<s_docvqa><s_question>{question}</s_question><s_answer>` |
| Generic custom task | `<s_{task_name}>` plus matching special tokens/checkpoint training |

## JSON token helpers

`DonutModel.json2token(obj, update_special_tokens_for_json_key=True, sort_json_key=True)` converts structured JSON into the decoder token sequence:

- dictionaries become `<s_key>...</s_key>` spans;
- lists are joined with `<sep/>`;
- `{"text_sequence": "..."}` returns the raw text value for SynthDoG/text-reading tasks;
- when `update_special_tokens_for_json_key=True`, new JSON field tokens are registered with the decoder tokenizer.

`DonutModel.token2json(tokens, is_inner_value=False)` reverses generated spans into dictionaries/lists and falls back to `{"text_sequence": tokens}` when no structured tags are found.

Use [`../scripts/runtime_smoke.py`](../scripts/runtime_smoke.py) to exercise this token round-trip without loading a real checkpoint.

## Dataset contract

A local dataset should expose `train/`, `validation/`, and/or `test/` split directories with `metadata.jsonl` files and image files. Each row is a JSON object:

```json
{"file_name": "image_0.jpg", "ground_truth": "{\"gt_parse\": {\"class\": \"scientific_report\"}}"}
```

Ground truth is itself a JSON-encoded string:

- classification and extraction tasks use `gt_parse` with a dictionary;
- DocVQA uses `gt_parses`, a non-empty list of `{question, answer}` dictionaries;
- text-reading/SynthDoG data uses `gt_parse: {"text_sequence": "..."}`.

`DonutDataset` reads datasets with `datasets.load_dataset(dataset_name_or_path, split=...)`, so local directories must be compatible with Hugging Face Datasets image-folder/metadata loading.

## Evaluation behavior

`JSONParseEvaluator.cal_acc(pred, answer)` computes normalized tree edit distance (n-TED) based accuracy. It normalizes dictionaries, builds tree nodes, computes edit distance, and returns `max(1 - nTED, 0)`.

`JSONParseEvaluator.cal_f1(preds, answers)` computes micro-averaged field-level F1 over flattened key/value pairs.

Use the training sub-skill for command-level evaluation and score interpretation.

## Bundled script ownership

The original repository shipped `app.py`, `train.py`, `test.py`, and `synthdog/` helpers. This skill does not depend on those source files at runtime:

- inference wraps demo and single-image prediction in [`../sub-skills/inference/scripts/`](../sub-skills/inference/scripts/);
- training copies/adapts the trainer, Lightning module, validation, and evaluation helpers in [`../sub-skills/training/scripts/`](../sub-skills/training/scripts/);
- SynthDoG copies/adapts the template and elements/layouts under [`../sub-skills/synthdog/scripts/`](../sub-skills/synthdog/scripts/).
