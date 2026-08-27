# CrossEncoder Troubleshooting

## Install And Import Failures

Symptom: `ModuleNotFoundError: No module named 'sentence_transformers'`.

- Install Python 3.10+ and the package with `pip install -U sentence-transformers`.
- Verify with `python -c "from sentence_transformers import CrossEncoder; print(CrossEncoder)"`.
- If working from an editable checkout, ensure the active environment is the one where the package was installed.

Symptom: `ImportError` from `transformers`, `torch`, `huggingface_hub`, `numpy`, `scipy`, or `sklearn`.

- Reinstall the base package so required dependencies resolve together.
- Run `pip check` to catch incompatible dependency versions.
- For CPU-only environments, avoid CUDA-specific torch wheels and backend providers.

## Model Loading And Download Failures

Symptom: loading a remote model fails or hangs.

- Pass a local model directory or use `local_files_only=True` for offline/cache-only operation.
- Check network access, Hugging Face authentication, and model id spelling.
- Pin `revision` for reproducible loads.
- Do not set `trust_remote_code=True` unless the model repository code has been reviewed.

Symptom: private or gated model returns authorization errors.

- Pass `token=True` to use a logged-in Hugging Face token, or pass a token string through secure runtime configuration.
- Avoid embedding tokens in scripts, config files, or skill content.

## Pair Shape And API Misuse

Symptom: outputs have an unexpected scalar/vector shape.

- A single pair is `["query", "document"]` or `(query, document)`.
- A batch is `[["query", "doc1"], ["query", "doc2"]]`.
- A 1D numpy string array is treated as one pair; a 2D array is treated as a batch.
- For multi-class models, each pair returns a vector of length `num_labels`.

Symptom: `CrossEncoder.rank() only works for models with num_labels=1`.

- Use `rank` only for regression/reranking models.
- For NLI or other pair classifiers, use `predict`, then apply `argmax`, class mapping, or `apply_softmax=True` as appropriate.
- If training or initializing a reranker, set `num_labels=1`.

Symptom: `rank` returns correct positions but IDs do not match the original corpus.

- `corpus_id` is the index within the `documents` list passed to `rank`.
- Preserve the retriever hit list and map `ranked_item["corpus_id"]` back to that list.
- Do not assume `corpus_id` is a database primary key.

## Activation And Score Pitfalls

Symptom: MS MARCO scores are negative or above 1.

- Many MS MARCO rerankers expose raw logits by default.
- Use `CrossEncoder(model_id, activation_fn=torch.nn.Sigmoid())` if the application requires 0-1 values.
- For ranking only, raw logits usually sort identically under monotonic activations.

Symptom: class probabilities do not sum to 1.

- Set `apply_softmax=True` when calling `predict` on a `num_labels > 1` classifier.
- Confirm the model's label order from its model card or config before mapping argmax indices.

Symptom: sigmoid applied to a multi-class classifier gives confusing probabilities.

- `activation_fn` and `apply_softmax` are separate. Multi-class classification usually wants identity logits followed by softmax, not sigmoid per class.
- Leave `activation_fn` unset for `num_labels > 1` unless the checkpoint documents a custom head.

## Batch, Device, And Memory Failures

Symptom: out-of-memory during reranking.

- Lower `batch_size` first.
- Reduce candidate count from the first-stage retriever.
- Set `max_length` or per-call processor truncation if long documents dominate memory.
- Avoid `return_documents=True` for large objects or very large candidate lists.

Symptom: device mismatch or accelerator unavailable.

- Pass `device="cpu"` for portable tests.
- Use `device="cuda"` only when CUDA torch is installed and a GPU is visible.
- If `model_kwargs={"device_map": ...}` is provided, it overrides the constructor `device` placement.

Symptom: multiprocessing is slower or unstable.

- Use a single device for small candidate lists.
- Reuse a manual pool for repeated large batches instead of creating one every call.
- Tune `chunk_size` only after `batch_size` and candidate count are reasonable.

## Prompt And Truncation Failures

Symptom: model quality drops unexpectedly after switching checkpoints.

- Check whether the checkpoint saved query/document prompts.
- Supply matching `prompts` and `default_prompt_name`, or override prompts explicitly per call.
- Ensure long passages are not truncating away answer-bearing text; inspect tokenizer max length and set `max_length` deliberately.

Symptom: a custom prompt appears twice.

- Avoid setting both saved/default prompts and manually prefixed query strings unless the model expects both.
- Disable saved prompts with empty values for known prompt keys when manually formatting text.

## Multimodal And Optional Extras

Symptom: image, audio, or video inputs fail in preprocessing.

- Install the relevant extra, such as `sentence-transformers[image]`, `sentence-transformers[audio]`, or `sentence-transformers[video]`.
- Verify the checkpoint supports the modality with `model.modalities` and `model.supports(...)`.
- Prefer local file paths or already-loaded objects for controlled service environments; remote media URLs may fail due to network policies.

Symptom: a text-only reranker receives images or media dictionaries.

- Route to a multimodal reranker checkpoint.
- Fall back to text-only metadata/caption reranking if the environment cannot support multimodal inference.

## Backend And Service Limits

Symptom: ONNX/OpenVINO backend load fails.

- Ensure optional backend dependencies are installed and the backend file exists or export is requested intentionally.
- Route export and quantization decisions to `../backend-export-optimization/SKILL.md`.

Symptom: a web service times out when reranking.

- Limit `top_k` from first-stage retrieval.
- Batch candidates but cap maximum candidates per request.
- Cache first-stage results and model instances, not individual CrossEncoder pair outputs unless the exact query-document pair repeats.
- Consider a smaller reranker for latency-sensitive paths.

## Evaluation And Training Failures

Symptom: `CrossEncoderRerankingEvaluator` raises validation errors.

- Each sample must contain `query` and `positive`.
- Include exactly one of `negative` or `documents`.
- Use `documents` when measuring reranking of an existing candidate list and `negative` when constructing candidates from positives/negatives.

Symptom: reranker training runs but performance degrades.

- Confirm `num_labels=1` for relevance reranking.
- Confirm dataset column order: non-label columns are interpreted as inputs in order, and labels must use a recognized name such as `label`, `labels`, `score`, or `scores`.
- Use the evaluation/training sub-skill for loss and evaluator routing before launching a long training job.
