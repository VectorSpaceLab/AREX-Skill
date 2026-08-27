# Neuron View Troubleshooting

## Purpose

Use this reference when `bertviz.neuron_view.show` or `get_attention` fails,
loads too slowly, or returns data that does not match the visualization task.

## Common failures

| Symptom or error | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError("Invalid model type:", ...)` | `model_type` is not one of `"bert"`, `"gpt2"`, `"xlnet"`, `"roberta"`. | Choose a supported value that matches the modified BertViz model class, or route to `attention-views` with standard attention tensors. |
| `ValueError("Sentence A is required")` | Empty or `None` `sentence_a`. | Provide a non-empty first sentence. |
| `Model gpt2 does not support sentence pairs` | GPT-2 path is causal single-text only. | Remove `sentence_b`; for pair comparisons use BERT/RoBERTa or head/model views. |
| `NotImplementedError` for XLNet sentence pairs | XLNet pair handling is explicitly not implemented in BertViz neuron view. | Use XLNet single sentence, switch to BERT/RoBERTa for pairs, or use head/model views with externally computed tensors. |
| Pretrained model load downloads or stalls | `from_pretrained(...)` is fetching weights/config/tokenizer files. | Use a local model path/cache, verify network approval, or run `scripts/validate_toy_bert_attention.py` to separate BertViz issues from download issues. |
| Missing `sentencepiece` | XLNet tokenizer path needs SentencePiece. | Install BertViz's documented runtime dependencies or avoid XLNet tokenizer workflows. |
| TensorFlow import error during checkpoint conversion | User called a TF checkpoint conversion helper. | Install TensorFlow only if conversion is truly required; normal PyTorch neuron view does not need it. |
| Apex warning | Optional fused LayerNorm is absent. | Usually ignore; BertViz falls back to a pure PyTorch LayerNorm. |
| `show` fails with ordinary Hugging Face model outputs | Normal `AutoModel` does not expose BertViz neuron-view query/key dictionaries. | Use modified classes from `bertviz.transformers_neuron_view`, or route to `attention-views` if standard attentions are enough. |
| Blank widget or JavaScript not rendering | Notebook frontend lacks required display support or blocked scripts. | In notebooks ensure IPython/Jupyter display support is active; in scripts use `html_action="return"` and write `.data` to HTML. |
| Browser/notebook disconnects or is slow | Input is long or model has many layers/heads. | Use shorter text, select a specific `layer`/`head`, or use head/model views with filtered layers/heads. |

## Debug sequence

1. Run the offline validator:

   ```bash
   python scripts/validate_toy_bert_attention.py --include-query-key-schema
   ```

2. If the validator passes, inspect your model/tokenizer choice and whether
   `model_type` matches the class family.
3. If a pretrained load fails, retry with a local model directory or a known
   populated cache rather than changing BertViz code first.
4. If the task does not need query/key vectors, route to `attention-views` and
   provide standard attention tensors to `head_view` or `model_view`.

## Stop conditions

Stop and ask for user approval before running workflows that require large
model downloads, remote access, credentials, or long GPU-backed model execution.
The toy validator and saved synthetic HTML workflows are the safe default
checks.
