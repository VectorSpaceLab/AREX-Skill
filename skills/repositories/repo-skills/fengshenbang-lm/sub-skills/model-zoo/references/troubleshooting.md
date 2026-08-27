# Troubleshooting

Use this matrix after selecting the family in [model-overview.md](model-overview.md) and checking API routes in [api-reference.md](api-reference.md). Keep fixes import/config-only unless the user explicitly authorizes model downloads, CUDA runtime, or checkpoint mutation.

## Import and dependency failures

| Symptom | Likely cause | Safe diagnosis | Recovery |
|---|---|---|---|
| `ImportError: cannot import name 'cached_path' from 'transformers'` | Installed Transformers is too new for Fengshen modules that import the legacy symbol. | Run `python scripts/check_model_imports.py --json` and inspect the `transformers.cached_path` check. | Use an isolated compatible stack with Transformers 4.20.x. Avoid upgrading Transformers in place unless the user accepts environment mutation. |
| `ImportError: cannot import name 'softmax_backward_data' from 'transformers.pytorch_utils'` | Installed Transformers is too new for Fengshen DeBERTa-v2. | Run the import check; direct-import only the DeBERTa-v2 family if needed. | Pin Transformers to a compatible 4.20-era release or port the DeBERTa-v2 code intentionally. |
| `ModuleNotFoundError: sentencepiece` | DeltaLM or Transformer-XL denoise tokenizer needs SentencePiece. | Import the model config separately from the tokenizer; inspect local tokenizer files. | Install `sentencepiece` in the inspection/runtime environment, then re-run tokenizer import/local-only checks. |
| `ModuleNotFoundError: deepspeed` or DeepSpeed warnings during model utility imports | Some package utilities import DeepSpeed; optional ops may be absent. | Decide whether the task needs model-zoo imports or training/runtime DeepSpeed. | For model-zoo-only checks, avoid importing training utilities. For required DeepSpeed runtime, route to `../data-training/SKILL.md`. |
| `RuntimeError` or extension build errors from Megatron/fused kernels | Optional CUDA extension path is being imported or tested. | Confirm whether the task truly needs fused kernels. | Treat as optional backend; require CUDA/toolchain verification under `../data-training/SKILL.md` before claiming support. |
| `torchmetrics.Accuracy` or PyTorch Lightning API errors while using pipelines | Newer metrics/training dependencies changed APIs. | Separate model-family import from pipeline/training execution. | Pin TorchMetrics/PyTorch Lightning to compatible older versions for Fengshen pipeline/training workflows, then route CLI/training details to sibling sub-skills. |
| `ModuleNotFoundError: jsonlines` while importing DAVAE/GAVAE/PPVAE | Optional VAE modules import `jsonlines` at module import time. | Run the import checker and confirm whether only VAE optional checks fail. | Install `jsonlines` only if VAE work is selected; otherwise keep the optional failure explicit and proceed with non-VAE families. |

## Auto factory and config-key failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Fengshen `AutoConfig` says the model is unrecognized. | `config.json` lacks standard `model_type`, or `model_type` is not one of the built-in Fengshen custom auto mappings. | For Fengshen auto classes, use `model_type: "longformer"` or `"roformer"` only unless registering local mappings. For other families, use direct imports. |
| `TextClassificationPipeline` chooses a Hugging Face auto model instead of Longformer/RoFormer/ZEN. | `fengshen_model_type` is missing or set to `huggingface-auto`. | Add or inspect `fengshen_model_type` in the local config. Valid Fengshen values are `fengshen-roformer`, `fengshen-longformer`, and `fengshen-zen1`. |
| `TextClassificationPipeline` raises that the model type is not in the model dict. | `fengshen_model_type` is present but misspelled or unsupported. | Replace it with one of the valid values, or remove it and rely on Hugging Face auto selection for standard checkpoints. |
| Custom tokenizer key is ignored. | The pipeline defines `fengshen_tokenizer_type`, but the practical text-classification route commonly falls back to `transformers.AutoTokenizer`. | Use a standard `tokenizer_class` in tokenizer metadata or direct family tokenizer imports. Verify with local files before prediction/training. |
| `AutoModelForSeq2SeqLM` fails for Megatron-T5 even though mapping names mention T5. | Fengshen's default custom config mapping is not a complete T5 auto route. | Import `T5Config`, `T5Model`, `T5EncoderModel`, or `T5ForConditionalGeneration` directly from `fengshen.models.megatron_t5`. |

## Tokenizer and local-file failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `OSError: Can't load tokenizer` | Local checkpoint directory lacks vocabulary/tokenizer files or uses a remote ID with empty cache. | Inspect the directory for `tokenizer_config.json`, `vocab.txt`, SentencePiece model files, merges, or special-token files. Use `local_files_only=True`. |
| Longformer/RoFormer tokenizer behaves like BERT. | In this package, both tokenizers alias Transformers `BertTokenizer`. | Ensure BERT-style vocabulary exists. Do not expect a custom fast tokenizer unless the checkpoint metadata supplies one. |
| Megatron-T5 tokenizer does not accept a standard T5 SentencePiece model. | Fengshen `T5Tokenizer` wraps `BertTokenizer` and adds T5-style special tokens. | Provide a BERT-style vocabulary path, or use a different tokenizer intentionally outside this package route. |
| ZEN n-gram features fail. | Missing n-gram dictionary file or `cached_path` compatibility issue. | Verify local n-gram dictionary files and compatible Transformers version before loading weights. |
| DeltaLM/Transformer-XL tokenizer fails after SentencePiece install. | Local SentencePiece model file path is missing or metadata points to an unavailable remote file. | Ask for the local tokenizer/model-file path and use local-only loading. |

## Download and offline-cache failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `from_pretrained` hangs or attempts network access. | Model ID is remote and cache is absent. | Stop and ask whether downloads are authorized. If not, request a local checkpoint directory and pass `local_files_only=True`. |
| Offline mode says files are missing. | Cache lacks config/tokenizer/weights required by the requested class. | Inspect local cache contents or request explicit local model files. Do not switch off offline mode without user approval. |
| Generation helper imports succeed but example execution fails. | Helper examples require remote model IDs and weights. | Treat helper functions as routes only. For recipe execution, route to `../examples-conversion/SKILL.md` and require model/cache approval. |

## CPU, CUDA, and model-size failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Host runs out of memory when loading Ziya/LLaMA or large T5/BART/DeltaLM. | Checkpoint is too large for CPU RAM or single-device VRAM. | Do not continue by trial-and-error. Ask for model size, quantization plan, device map, and whether conversion/planning should route to `../examples-conversion/SKILL.md`. |
| CUDA is unavailable but user asks for Megatron/deepspeed/fused-kernel training. | Required backend is not verified for that workflow. | Route to `../data-training/SKILL.md`; require backend verification before claiming support. |
| CPU import works but CUDA run fails. | Import success does not prove compiled CUDA ops, memory capacity, device map, or DeepSpeed runtime. | Document CPU/import-only status and run backend-specific checks only under a separate verification plan. |
| FP16/BF16 errors on CPU. | Half precision is generally CUDA/GPU-oriented for these workflows. | Use full precision on CPU or request GPU runtime. |

## Family-specific quick fixes

| Family | Common issue | Fix |
|---|---|---|
| Longformer | Global attention shape or long sequence memory. | Start with config/model import; for actual inputs, consult model docs and keep sequence length/resource constraints explicit. |
| RoFormer | Pair input formatting differs in pipeline collator. | Let the pipeline collator format pairs or reproduce its separator behavior intentionally. CLI/data route: `../pipelines-cli/SKILL.md`. |
| Megatron-T5 | User expects standard T5 tokenizer/model paths. | Use direct Fengshen `T5Tokenizer`/`T5ForConditionalGeneration` and verify local vocab/checkpoint compatibility. |
| ZEN1/ZEN2 | N-gram dictionary missing. | Ask for local n-gram dictionary files and keep tokenizer/model checks local-only. |
| DeBERTa-v2 | `softmax_backward_data` import error. | Pin compatible Transformers; do not assume the checkpoint is corrupt. |
| DeltaLM | SentencePiece or forced BOS behavior confusion. | Install SentencePiece, verify tokenizer model, and inspect config generation fields before loading weights. |
| LLaMA/Ziya | Checkpoint conversion/sharding mismatch. | Route conversion planning to `../examples-conversion/SKILL.md`; do not mutate checkpoint files from model-zoo. |
| Taiyi CLIP | Missing image/text subfolders or vision dependencies. | Check processor/model requirements and local checkpoint layout; route diffusion recipes elsewhere. |
| UniMC/UniEX/TCBert/Ubert | Model import interleaves with data/pipeline classes. | Use model-zoo for class selection only; route data schemas and pipeline usage to `../pipelines-cli/SKILL.md`. |
| VAE families | Helper scripts attempt to load GPT2/BERT by ID, and some modules need optional `jsonlines` even to import. | Do not use helper scripts as smoke tests. Install `jsonlines` only for selected VAE work; otherwise use import-only checks for other families unless weights/cache are explicit. |

## Recovery from the two difficult verification cases

### Case: checkpoint has `fengshen_model_type` and user needs pipeline mapping

1. Inspect local `config.json` only.
2. Read `fengshen_model_type`.
3. Map `fengshen-roformer`, `fengshen-longformer`, or `fengshen-zen1` to the text-classification model class table in [api-reference.md](api-reference.md).
4. If the value is absent, explain that the pipeline uses `huggingface-auto` and `transformers.AutoModelForSequenceClassification`.
5. Route actual CLI command construction and dataset fields to `../pipelines-cli/SKILL.md`.

### Case: `ImportError: cached_path` or `softmax_backward_data`

1. Do not change checkpoint files.
2. Run `python scripts/check_model_imports.py --json` in this sub-skill directory.
3. If the compatibility symbol check fails and Transformers is newer than the verified 4.20-era stack, create or repair an isolated environment with a compatible Transformers pin.
4. Re-run the import check.
5. If only optional families still fail, narrow the task to the target family and keep the optional failure explicit.
