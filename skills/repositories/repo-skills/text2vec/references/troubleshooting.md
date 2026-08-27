# Cross-Cutting Troubleshooting

## Import and dependency failures

| Symptom | Likely cause | What to do |
|---|---|---|
| `ModuleNotFoundError: No module named 'torch'` while importing `text2vec` | Public modules import torch, but `setup.py` does not install it. | Install an appropriate PyTorch build, then rerun `python scripts/check_text2vec_env.py`. |
| `ImportError` for `transformers`, `datasets`, `pandas`, `sklearn`, or `jieba` | Incomplete install or `--no-deps` install without requirements. | Install `text2vec` normally or install `requirements.txt` before a local `--no-deps` install. |
| `gensim` missing when using `Word2Vec` | Word2Vec imports `gensim.models.KeyedVectors` lazily. | Install `gensim` or use a SentenceModel workflow instead. For offline checks, generate a tiny fixture with `sub-skills/embeddings/scripts/make_tiny_word2vec_fixture.py`. |
| `kenlm` missing when using `NGram` | NGram is optional and depends on KenLM. | Install `kenlm` only when you intentionally need language-model scores; expect a large model artifact. |

## Model download and cache failures

| Symptom | Likely cause | What to do |
|---|---|---|
| `from_pretrained` hangs, retries, or fails | Default SentenceModel/base model requires Hugging Face access unless cached. | Prefer a local model directory for offline tasks. Check network/proxy outside the skill before retrying downloads. |
| Word2Vec initialization downloads or fails on `w2v-light-tencent-chinese` | Built-in Tencent vector is a large external artifact. | Provide a local word2vec file path; use the tiny fixture only for smoke tests, not model quality. |
| Service starts slowly or fails at startup | The app initializes a model and triggers a download. | Warm up with a local model path; use `/healthz`-style checks that do not load the model until `/warmup` or `/emb` is called. |

## Backend and hardware issues

| Symptom | Likely cause | What to do |
|---|---|---|
| CUDA requested but `torch.cuda.is_available()` is false | CPU-only PyTorch wheel, missing GPU passthrough, driver mismatch, or unavailable CUDA runtime. | Run `python scripts/check_text2vec_env.py --expect-cuda`; install a compatible CUDA PyTorch build only if CUDA is required. |
| GPU OOM during encode or training | Batch/sequence length too high, too many workers, or multiple services sharing memory. | Reduce `batch_size`, `max_seq_length`, process count, or model size; for training also reduce gradient accumulation or disable bf16 if unsupported. |
| `bf16` training fails | GPU/framework does not support bfloat16 or CPU path was selected. | Disable `bf16` or run on compatible GPU hardware. |
| `--multi_gpu True` with Word2Vec fails | Package CLI explicitly rejects Word2Vec multi-GPU because Word2Vec is CPU/vector-file based. | Use Word2Vec single-process CPU or switch to SentenceModel multi-process/multi-GPU. |

## Data and CLI issues

| Symptom | Likely cause | What to do |
|---|---|---|
| Package CLI output has fewer rows than input | The package CLI loads non-empty input lines into a `set`, removing duplicates and order. | Use `sub-skills/embeddings/scripts/encode_texts.py` when duplicate preservation matters. |
| Training silently sees fewer rows | Loader skips JSONL rows without accepted text field pairs. | Run `sub-skills/training-finetuning/scripts/validate_text_matching_data.py` before training. |
| BGE training crashes on negatives | `neg` is missing, empty, or too short for the requested `train_group_size`. | Run `sub-skills/training-finetuning/scripts/validate_bge_jsonl.py --train-group-size <n>` and inspect warnings. |
| `Similarity.get_scores` shape surprises | `only_aligned=False` produces full cross-product scores. | Use `only_aligned=True` or the `score_pairs.py` helper when you need one score per input row. |

## When to stop and ask for more runtime resources

Stop before claiming success when the requested result requires one of these and it is not available:

- A production model checkpoint that is neither local nor downloadable.
- A real CUDA/MPS multi-GPU run, not just CPU smoke coverage.
- Full fine-tuning or MTEB/C-MTEB benchmarks with large external datasets.
- A live FastAPI/Jina/Gradio service bound to a port in the target deployment environment.
- KenLM/NGram scoring with the large language model artifact.
