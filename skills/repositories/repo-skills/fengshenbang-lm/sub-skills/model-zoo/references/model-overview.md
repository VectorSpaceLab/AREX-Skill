# Model overview

This reference helps choose a Fengshen model family without opening the source repository. Use it with [api-reference.md](api-reference.md) for imports, [auto-and-tokenizers.md](auto-and-tokenizers.md) for factory/config details, and [compatibility.md](compatibility.md) before installing or repairing dependencies.

## High-level catalog orientation

Fengshenbang-LM combines a package named `fengshen` with a public model catalog. The model catalog is broader than the classes implemented in the package, so first decide whether the task needs a package class, a Hugging Face model ID, a pipeline, or a heavy example recipe.

| Catalog series | Main use | Package/model-zoo route | When to route elsewhere |
|---|---|---|---|
| Ziya | General large language models and instruction/reward models, mostly LLaMA-derived. | Use `fengshen.models.llama` for Fengshen LLaMA config/model classes when working with compatible local checkpoints. | Ziya inference modes, quantization, tensor-parallel conversion, and fine-tuning recipes belong to `../examples-conversion/SKILL.md`. |
| Erlangshen | NLU encoders and classification/extraction checkpoints: Megatron-BERT, RoBERTa/BERT-style, DeBERTa-v2, ZEN, RoFormer, ALBERT. | Use direct family imports or pipeline model mapping. | CLI prediction/training and data schema questions belong to `../pipelines-cli/SKILL.md`; training arguments belong to `../data-training/SKILL.md`. |
| Wenzhong / Randeng | NLG and natural-language transformation: GPT-like, BART, T5, DeltaLM, Transformer-XL variants. | Use BART, Megatron-T5, DeltaLM, Transformer-XL, or VAE references here for class selection. | Task recipe adaptation, checkpoint conversion, and example commands belong to `../examples-conversion/SKILL.md`. |
| Taiyi | Multimodal models: CLIP and diffusion-style image generation families. | Use `fengshen.models.clip` for Taiyi CLIP classes. | Stable Diffusion inference/finetune/DreamBooth recipes are heavy optional examples and belong to `../examples-conversion/SKILL.md`. |
| Yuyuan and domain variants | Domain-specialized text generation or understanding checkpoints. | Choose the package class by checkpoint config (`model_type` and any Fengshen custom keys). | Domain data preparation and training recipes route to `../data-training/SKILL.md` or `../examples-conversion/SKILL.md`. |

## Model-family selection table

| Family | Best fit | Primary package imports | Tokenizer/config notes | Verification stance |
|---|---|---|---|---|
| Longformer | Long-context encoder tasks, sequence classification, token classification, QA, multiple choice, masked LM. | Top-level `LongformerConfig`, `LongformerModel`; direct `LongformerForSequenceClassification`, `LongformerForTokenClassification`, `LongformerForQuestionAnswering`, `LongformerForMultipleChoice`, `LongformerForMaskedLM`. | `LongformerTokenizer` is an alias of Transformers `BertTokenizer`. Custom auto mapping recognizes `model_type: "longformer"`. | Import-only checks are safe; pretrained checkpoint execution may download weights. |
| RoFormer | Rotary-position BERT-style encoder tasks: sequence classification, token classification, QA, multiple choice, masked LM, causal LM. | Top-level `RoFormerConfig`, `RoFormerModel`; direct `RoFormerForSequenceClassification`, `RoFormerForTokenClassification`, `RoFormerForQuestionAnswering`, `RoFormerForMultipleChoice`, `RoFormerForMaskedLM`, `RoFormerForCausalLM`. | `RoFormerTokenizer` is an alias of Transformers `BertTokenizer`. Custom auto mapping recognizes `model_type: "roformer"`. | Import-only checks are safe; use direct imports if auto factory mapping is insufficient. |
| Megatron-T5 | Encoder/encoder-decoder NLT and generation-style tasks using the Fengshen T5 implementation. | Top-level `T5Config`, `T5EncoderModel`; direct `T5Model`, `T5ForConditionalGeneration`, `T5Tokenizer`. | Config class uses `model_type = "T5"`. `T5Tokenizer.from_pretrained` wraps a BERT tokenizer and adds `[BOS]`, `[EOS]`, and `<extra_id_N>` tokens. | Import/config checks are safe; full generation needs model weights. |
| ZEN1 / ZEN2 | Chinese n-gram enhanced BERT-style encoders for pretraining, sequence classification, token classification, QA (ZEN2), and masked LM. | `ZenConfig`, `ZenModel`, `ZenForPreTraining`, `ZenForSequenceClassification`, `ZenForTokenClassification`, `ZenForMaskedLM`, `ZenForQuestionAnswering` where available; `ZenNgramDict`. | Tokenizers are BERT-style; n-gram dictionaries are separate files loaded by `ZenNgramDict.from_pretrained`. | Import checks require a Transformers version that still exposes `cached_path`. N-gram file checks should be local-only. |
| DeBERTa-v2 | Erlangshen DeBERTa-style encoder checkpoints and masked LM/classification/QA heads. | `DebertaV2Model`, `DebertaV2ForMaskedLM`, `DebertaV2ForSequenceClassification`, `DebertaV2ForTokenClassification`, `DebertaV2ForQuestionAnswering`, `DebertaV2ForMultipleChoice`. | Config is a Transformers `DebertaV2Config` import path in the modeling file rather than a Fengshen package config file. | Requires a Transformers version exposing `transformers.pytorch_utils.softmax_backward_data`. |
| DeltaLM | Seq2seq generation/translation/summarization-style tasks. | `DeltalmConfig`, `DeltalmModel`, `DeltalmForConditionalGeneration`, `DeltalmForCausalLM`, `DeltalmTokenizer`. | Tokenizer is SentencePiece-based and needs an `.spm`/model file plus the `sentencepiece` package. | Importing tokenizer may fail without SentencePiece; loading checkpoints may download or need local files. |
| LLaMA / Ziya | Fengshen LLaMA-style causal language models for large local checkpoints. | `LlamaConfig`, `LlamaModel`, `LlamaForCausalLM`. | Checkpoint layouts and tensor-parallel conversion are recipe/conversion concerns, not basic model-zoo imports. | Class imports are safe; real models are large and usually require GPU or large CPU RAM. |
| Taiyi CLIP | Text-image representation and CLIP-style embedding. | `TaiyiCLIPConfig`, `TaiyiCLIPModel`, `TaiyiCLIPProcessor`, `TaiyiCLIPEmbedder`. | Processor combines image and text preprocessing. Some use paths call `BertTokenizer`/`BertModel` from a model version or subfolder. | Import checks are safe; image model execution may download weights and needs vision dependencies. |
| Transformer-XL variants | Denoising, paraphrase, and reasoning generation helpers. | `TransfoXLDenoiseConfig`, `TransfoXLDenoiseModel`, `TransfoXLDenoiseTokenizer`; helper functions `denoise_generate`, `paraphrase_generate`, `deduction_generate`, `abduction_generate`. | Denoise tokenizer is SentencePiece-based; paraphrase/reasoning helpers may use T5/Transformer-XL checkpoint IDs in examples. | Do not run helper examples unless model weights and cache policy are explicit. |
| BART | Text infilling and BART-based generation/finetuning. | `BartForTextInfill`, `CBartLightning`. | Uses standard Transformers BART pieces plus Fengshen wrappers. | Direct class import may require training dependencies; generation needs model weights. |
| ALBERT | ALBERT encoder and classification/QA/token heads. | `AlbertModel`, `AlbertForPreTraining`, `AlbertForMaskedLM`, `AlbertForSequenceClassification`, `AlbertForTokenClassification`, `AlbertForQuestionAnswering`, `AlbertForMultipleChoice`. | Mostly mirrors Transformers ALBERT implementation. | Import-only safe; checkpoint execution may download weights. |
| UniMC / UniEX / TCBert / Ubert | Unified classification, extraction, prompt classification, and unified NLU pipelines/models. | `UniMCPipelines`, `UniMCModel`; `UniEXPipelines`; `TCBertModel` family; top-level `UbertPipelines`, `UbertModel`, `UbertDataset`. | These families often couple model classes with data/pipeline logic and Hugging Face `AutoConfig`/`AutoTokenizer`. | Use this sub-skill for class selection; data schemas and CLI usage route to `../pipelines-cli/SKILL.md`. |
| VAE variants | Latent generation and VAE experiments: DAVAE, GAVAE, PPVAE, deepVAE/Della. | `DAVAEModel`, `EncDecAAE`, `GAVAEModel`, `PPVAEModel`, `DellaModelConfig`, `Della`, `DeepVAE`. | Some examples load GPT2/BERT by ID; DAVAE/GAVAE/PPVAE imports may need optional `jsonlines`. | Treat as research/experimental; import classes only unless optional deps, weights, and runtime are explicit. |

## Selection workflow

1. **Start from the checkpoint config if the user has one.** Inspect local `config.json` without loading weights. Use `model_type` for Transformers/Fengshen auto classes and `fengshen_model_type` for Fengshen pipeline dispatch.
2. **If `fengshen_model_type` is present for text classification**, map it as described in [api-reference.md](api-reference.md): `fengshen-roformer`, `fengshen-longformer`, `fengshen-zen1`, or `huggingface-auto`.
3. **If the family is one of Longformer or RoFormer**, Fengshen auto factories can be convenient. For all other custom families, prefer direct imports.
4. **If the task is pipeline prediction/training**, stop model-zoo extraction after choosing the model family and route invocation/data schemas to `../pipelines-cli/SKILL.md`.
5. **If the task is finetuning, distributed training, metrics, or dataloaders**, route to `../data-training/SKILL.md`.
6. **If the task is an example recipe, checkpoint conversion, Ziya conversion, or Taiyi diffusion**, route to `../examples-conversion/SKILL.md`.

## Safe checks

From this sub-skill directory:

```bash
python scripts/check_model_imports.py
python scripts/check_model_imports.py --json
python scripts/check_model_imports.py --strict
```

The script imports package modules and compatibility symbols only. It does not call `from_pretrained`, download model files, run training, compile CUDA kernels, or mutate checkpoints.
