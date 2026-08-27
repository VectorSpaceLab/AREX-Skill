# API reference

Use this reference for import paths, public exports, family-specific classes, and generation helper routes. It intentionally avoids model downloads and checkpoint execution.

## Top-level package exports

The public `fengshen` package top level exports only a small subset of the model zoo.

| Import | Meaning | Typical use |
|---|---|---|
| `from fengshen import LongformerConfig` | Fengshen Longformer config. | Read/create Longformer configs; pair with direct Longformer model classes. |
| `from fengshen import LongformerModel` | Base Longformer model. | Encoder feature extraction or custom heads. |
| `from fengshen import RoFormerConfig` | Fengshen RoFormer config. | Read/create RoFormer configs; pair with direct RoFormer heads. |
| `from fengshen import RoFormerModel` | Base RoFormer model. | Encoder feature extraction or custom heads. |
| `from fengshen import T5Config` | Fengshen Megatron-T5 config. | T5-style config work. |
| `from fengshen import T5EncoderModel` | Fengshen T5 encoder model. | Encoder-only use of Megatron-T5. |
| `from fengshen import UbertPipelines` | Ubert public pipeline wrapper. | Ubert unified NLU route; data schemas are in `../pipelines-cli/SKILL.md`. |
| `from fengshen import UbertModel` | Ubert model class. | Ubert class selection/debugging. |

Top-level imports are useful as a smoke check, but many supported families are only available through direct submodule imports.

## Direct family imports

| Family | Import path | Notable classes/functions |
|---|---|---|
| Longformer | `fengshen.models.longformer` | `LongformerConfig`, `LongformerTokenizer`, `LongformerModel`, `LongformerForMaskedLM`, `LongformerForSequenceClassification`, `LongformerForTokenClassification`, `LongformerForQuestionAnswering`, `LongformerForMultipleChoice` |
| RoFormer | `fengshen.models.roformer` | `RoFormerConfig`, `RoFormerTokenizer`, `RoFormerModel`, `RoFormerForPreTraining`, `RoFormerForCausalLM`, `RoFormerForMaskedLM`, `RoFormerForSequenceClassification`, `RoFormerForTokenClassification`, `RoFormerForQuestionAnswering`, `RoFormerForMultipleChoice` |
| Megatron-T5 | `fengshen.models.megatron_t5` | `T5Config`, `T5Tokenizer`, `T5Model`, `T5EncoderModel`, `T5ForConditionalGeneration` |
| ZEN1 | `fengshen.models.zen1` | `ZenConfig`, `ZenModel`, `ZenForPreTraining`, `ZenForMaskedLM`, `ZenForSequenceClassification`, `ZenForTokenClassification`, `BertTokenizer`, `ZenNgramDict` |
| ZEN2 | `fengshen.models.zen2` | `ZenConfig`, `ZenModel`, `ZenForPreTraining`, `ZenForMaskedLM`, `ZenForSequenceClassification`, `ZenForTokenClassification`, `ZenForQuestionAnswering`, `BertTokenizer`, `ZenNgramDict`, `extract_ngram_feature`, `construct_ngram_matrix` |
| DeBERTa-v2 | `fengshen.models.deberta_v2.modeling_deberta_v2` | `DebertaV2Model`, `DebertaV2ForMaskedLM`, `DebertaV2ForSequenceClassification`, `DebertaV2ForTokenClassification`, `DebertaV2ForQuestionAnswering`, `DebertaV2ForMultipleChoice` |
| DeltaLM | `fengshen.models.deltalm` submodules | `DeltalmConfig`, `DeltalmTokenizer`, `DeltalmModel`, `DeltalmForConditionalGeneration`, `DeltalmForCausalLM` |
| LLaMA / Ziya | `fengshen.models.llama` submodules | `LlamaConfig`, `LlamaModel`, `LlamaForCausalLM` |
| Taiyi CLIP | `fengshen.models.clip` | `TaiyiCLIPConfig`, `TaiyiCLIPModel`, `TaiyiCLIPProcessor`, `TaiyiCLIPEmbedder` |
| Transformer-XL denoise | `fengshen.models.transfo_xl_denoise` submodules | `TransfoXLDenoiseConfig`, `TransfoXLDenoiseTokenizer`, `TransfoXLDenoiseModel`, `denoise_generate` |
| Transformer-XL paraphrase | `fengshen.models.transfo_xl_paraphrase.generate` | `paraphrase_generate` |
| Transformer-XL reasoning | `fengshen.models.transfo_xl_reasoning.generate` | `deduction_generate`, `abduction_generate` |
| BART | `fengshen.models.bart.modeling_bart` | `BartForTextInfill`, `CBartLightning` |
| ALBERT | `fengshen.models.albert.modeling_albert` | `AlbertModel`, `AlbertForPreTraining`, `AlbertForMaskedLM`, `AlbertForSequenceClassification`, `AlbertForTokenClassification`, `AlbertForQuestionAnswering`, `AlbertForMultipleChoice` |
| UniMC | `fengshen.models.unimc` | `UniMCPipelines`; direct module also contains `UniMCDataset`, `UniMCDataModel`, `UniMCModel`, `UniMCLitModel`, `UniMCPredict` |
| UniEX | `fengshen.models.uniex` | `UniEXPipelines`; direct module also contains extraction data/model/lit/predict helpers |
| TCBert | `fengshen.models.tcbert.modeling_tcbert` | `TCBertDataset`, `TCBertDataModel`, `TCBertModel`, `TCBertLitModel`, `TCBertPredict` |
| Ubert | `fengshen.models.ubert` | `UbertPipelines`, `UbertModel`, `UbertDataset`; direct module also contains data/lit/checkpoint/extract helpers |
| DAVAE | `fengshen.models.DAVAE` submodules | `DAVAEModel`, `VAEPretrainedModel`, `EncDecAAE`, latent generation helpers in the package family |
| GAVAE | `fengshen.models.GAVAE.GAVAEModel` | `GAVAEPretrainedModel`, `GAVAEModel` |
| PPVAE | `fengshen.models.PPVAE` submodules | `PluginVAE`, `PPVAEPretrainedModel`, `PPVAEModel` |
| deepVAE / Della | `fengshen.models.deepVAE` submodules | `DellaModelConfig`, `Della`, `DeepVAE` |
| Megatron internals | `fengshen.models.megatron` subpackages | Tensor/model parallel utilities, fused kernels, layers, sparse attention helpers. These are optional heavy/backend paths; route training/runtime details to `../data-training/SKILL.md`. |

## Minimal import patterns

Use import-only patterns first:

```python
from fengshen import LongformerConfig, RoFormerConfig, T5Config
from fengshen.models.longformer import LongformerForSequenceClassification
from fengshen.models.roformer import RoFormerForTokenClassification
from fengshen.models.megatron_t5 import T5ForConditionalGeneration
```

Avoid this until model cache/download policy is explicit:

```python
# May download model files if the ID is remote.
# model = LongformerForSequenceClassification.from_pretrained("some/model-id")
```

For local checkpoint diagnosis, inspect the config JSON first and use local-only loading when calling Transformers/Fengshen APIs.

## Text classification `fengshen_model_type` mapping

`TextClassificationPipeline` reads a checkpoint config with a Transformers `BertConfig.from_pretrained(model)` call, then checks a custom config key named `fengshen_model_type`. The mapping in the package is:

| `fengshen_model_type` value | Model class route |
|---|---|
| `fengshen-roformer` | `RoFormerForSequenceClassification` |
| `fengshen-longformer` | `LongformerForSequenceClassification` |
| `fengshen-zen1` | `ZenForSequenceClassification` |
| `huggingface-auto` or absent key | `transformers.AutoModelForSequenceClassification` |

Use this mapping when a user asks, "Which model class will the pipeline choose for this checkpoint?" If the value is missing, misspelled, or outside the table, the pipeline either falls back to Hugging Face auto selection or raises a pipeline exception.

The tokenizer side has a matching key name, `fengshen_tokenizer_type`, but the text-classification implementation primarily falls back to `transformers.AutoTokenizer`. If a checkpoint needs a Fengshen-specific tokenizer, prefer explicit direct tokenizer imports or verify the pipeline route in a safe environment before running prediction/training.

## Sequence tagging model route

Sequence tagging is not dispatched by `fengshen_model_type`. The sequence-tagging pipeline chooses model/collator families from command arguments:

| Argument | Values | Route |
|---|---|---|
| `--model_type` | Usually BERT-compatible values. | Chooses the tagging base model wrapper. |
| `--decode_type` | `linear`, `crf`, `span`, `biaffine` | Chooses collator and validation path. |

For sequence-tagging data schemas and CLI flags, use `../pipelines-cli/SKILL.md`. For metrics and BIO/BIOES label validation, use `../data-training/SKILL.md`.

## Fengshen auto factory imports

`fengshen.models.auto` exposes:

```python
from fengshen.models.auto import AutoConfig, AutoTokenizer
from fengshen.models.auto import AutoModel, AutoModelForSequenceClassification
from fengshen.models.auto import AutoModelForMaskedLM, AutoModelForTokenClassification
from fengshen.models.auto import AutoModelForQuestionAnswering, AutoModelForMultipleChoice
```

The built-in custom auto mappings are narrow. They are most useful for `model_type: "longformer"` and `model_type: "roformer"`. For Megatron-T5, ZEN, DeBERTa-v2, DeltaLM, LLaMA, Taiyi CLIP, Transformer-XL, BART, ALBERT, UniMC/UniEX/TCBert/Ubert, and VAE classes, use direct imports unless you have registered extra mappings yourself.

See [auto-and-tokenizers.md](auto-and-tokenizers.md) for factory behavior and config examples.

## Generation helper routes

| Generation need | Safe model-zoo route | Notes |
|---|---|---|
| Megatron-T5 seq2seq generation | `T5ForConditionalGeneration.generate` | Requires loaded weights; import/config checks are safe. |
| DeltaLM generation | `DeltalmForConditionalGeneration.generate` | Tokenizer is SentencePiece-based; loading remote IDs may download. |
| LLaMA/Ziya causal generation | `LlamaForCausalLM` | Large models require memory/GPU planning; conversion recipes route to `../examples-conversion/SKILL.md`. |
| Transformer-XL denoising | `denoise_generate` | Helper examples embed checkpoint IDs; do not run without explicit model-cache approval. |
| Transformer-XL paraphrase | `paraphrase_generate` | Heavy checkpoint route; example recipe details belong to `../examples-conversion/SKILL.md`. |
| Transformer-XL reasoning | `deduction_generate`, `abduction_generate` | Same cache/runtime caution. |
| VAE latent generation | DAVAE/GAVAE/PPVAE/deepVAE class methods or latent-generation helpers | Experimental; some helpers load GPT2/BERT by ID. Use local-only checks unless downloads are authorized. |
| BART text infilling | `BartForTextInfill` | Recipe and data guidance route to `../examples-conversion/SKILL.md` / `../data-training/SKILL.md`. |

## Import smoke script

From this sub-skill directory, run:

```bash
python scripts/check_model_imports.py
```

It checks top-level exports, core family modules, selected optional modules, and compatibility symbols. Use `--strict` to fail on optional-family import failures, or `--json` for machine-readable output.
