# Auto factories and tokenizers

Use this reference before relying on Fengshen auto classes, custom config keys, or tokenizer files. For family imports, see [api-reference.md](api-reference.md). For version constraints, see [compatibility.md](compatibility.md).

## Three different dispatch mechanisms

Fengshenbang-LM has three related but different ways to select a model/tokenizer:

| Mechanism | Reads | Owners | Best use |
|---|---|---|---|
| Standard Transformers auto classes | `model_type`, `architectures`, `tokenizer_class`, `auto_map`, local/remote config files. | `transformers.AutoConfig`, `transformers.AutoModel*`, `transformers.AutoTokenizer`. | Most Hugging Face checkpoints and package families that already use standard Transformers mappings. |
| Fengshen custom auto classes | `model_type` in a config file, plus Fengshen's internal mapping. | `fengshen.models.auto.AutoConfig`, `AutoModel*`, `AutoTokenizer`. | Fengshen Longformer and RoFormer custom classes; manually registered extensions. |
| Fengshen pipeline custom keys | `fengshen_model_type` and intended `fengshen_tokenizer_type` in checkpoint config/tokenizer metadata. | Fengshen pipeline classes, especially text classification. | Choosing the model class behind `TextClassificationPipeline`; routing pipeline troubleshooting to `../pipelines-cli/SKILL.md`. |

Do not assume that a value working in one mechanism works in the other. For example, `model_type: "longformer"` is an auto-factory key, while `fengshen_model_type: "fengshen-longformer"` is a text-classification pipeline key.

## Fengshen custom auto factories

Import surface:

```python
from fengshen.models.auto import AutoConfig, AutoTokenizer
from fengshen.models.auto import AutoModel, AutoModelForSequenceClassification
from fengshen.models.auto import AutoModelForMaskedLM, AutoModelForTokenClassification
from fengshen.models.auto import AutoModelForQuestionAnswering, AutoModelForMultipleChoice
```

Built-in custom config mapping:

| `model_type` | Config class | Model family |
|---|---|---|
| `roformer` | `RoFormerConfig` | RoFormer |
| `longformer` | `LongformerConfig` | Longformer |

Built-in model head mappings are primarily Longformer/RoFormer:

| Auto class | Built-in Fengshen routes |
|---|---|
| `AutoModel` | `roformer`, `longformer` |
| `AutoModelForMaskedLM` | `roformer`, `longformer` |
| `AutoModelForSequenceClassification` | `roformer`, `longformer` |
| `AutoModelForTokenClassification` | `roformer`, `longformer` |
| `AutoModelForQuestionAnswering` | `roformer`, `longformer` |
| `AutoModelForMultipleChoice` | `roformer`, `longformer` |
| `AutoModelForPreTraining` | `longformer` |
| `AutoModelForCausalLM` | intended `roformer` route in mapping, but prefer direct import when diagnosing. |
| `AutoModelForSeq2SeqLM` | contains a `t5` mapping name, but the default Fengshen config mapping is not a complete Megatron-T5 route. Prefer direct Megatron-T5 imports. |

### When to avoid custom auto

Prefer direct imports when:

- The family is Megatron-T5, ZEN1/ZEN2, DeBERTa-v2, DeltaLM, LLaMA, Taiyi CLIP, Transformer-XL, BART, ALBERT, UniMC/UniEX/TCBert/Ubert, or VAE.
- The checkpoint config has a non-standard `model_type` not registered in Fengshen's custom mapping.
- The task is diagnosing an import error. Direct imports show the failing family more clearly.
- The user is offline and you can inspect a local config without invoking `from_pretrained` on a remote ID.

## Config snippets

### Fengshen auto factory: Longformer

A local config intended for Fengshen's custom `AutoConfig`/`AutoModel` route needs the standard `model_type` key:

```json
{
  "model_type": "longformer",
  "hidden_size": 768,
  "num_attention_heads": 12,
  "num_hidden_layers": 12
}
```

Then use local-only loading when possible:

```python
from fengshen.models.auto import AutoConfig, AutoModel

config = AutoConfig.from_pretrained("./local-longformer", local_files_only=True)
model_class = AutoModel.from_config(config).__class__.__name__
```

### TextClassificationPipeline: custom Fengshen model route

For text classification, `fengshen_model_type` controls the Fengshen-specific model class:

```json
{
  "model_type": "bert",
  "fengshen_model_type": "fengshen-roformer"
}
```

Valid values are:

| `fengshen_model_type` | Pipeline model class |
|---|---|
| `fengshen-roformer` | `RoFormerForSequenceClassification` |
| `fengshen-longformer` | `LongformerForSequenceClassification` |
| `fengshen-zen1` | `ZenForSequenceClassification` |
| `huggingface-auto` | `transformers.AutoModelForSequenceClassification` |

If a user has a custom checkpoint and asks how to make `TextClassificationPipeline` select a Fengshen family, ask for the local config JSON and look for this key before touching weights.

### Tokenizer route key

The package defines a companion key name:

```json
{
  "fengshen_tokenizer_type": "some-custom-tokenizer-key"
}
```

However, the text-classification implementation falls back to `transformers.AutoTokenizer` in common paths, and the built-in `_tokenizer_dict` for that pipeline is empty. For checkpoints that require a custom tokenizer, use one of these safer routes:

1. Directly import the family tokenizer (`LongformerTokenizer`, `RoFormerTokenizer`, `T5Tokenizer`, `DeltalmTokenizer`, `TransfoXLDenoiseTokenizer`, ZEN `BertTokenizer`).
2. Ensure the local tokenizer metadata contains a standard `tokenizer_class` that `transformers.AutoTokenizer` can resolve.
3. Run an import/config-only check before prediction or training.

## Tokenizer family notes

| Family | Tokenizer route | Required files/dependencies | Common failure |
|---|---|---|---|
| Longformer | `LongformerTokenizer` aliasing `BertTokenizer`. | BERT-style vocabulary such as `vocab.txt`. | Missing vocab file or wrong local checkpoint directory. |
| RoFormer | `RoFormerTokenizer` aliasing `BertTokenizer`. | BERT-style vocabulary such as `vocab.txt`. | Pair classification may require RoFormer-specific text-pair formatting in the pipeline collator. |
| Megatron-T5 | `T5Tokenizer.from_pretrained(vocab_path)` wraps `BertTokenizer` and adds `[BOS]`, `[EOS]`, and `<extra_id_*>` tokens. | BERT-style vocabulary directory/file accepted by `BertTokenizer`. | User expects a standard SentencePiece T5 tokenizer; this implementation is BERT-tokenizer based. |
| ZEN1/ZEN2 | ZEN `BertTokenizer` plus `ZenNgramDict`. | `vocab.txt` plus n-gram dictionary file for n-gram features. | `cached_path` missing in too-new Transformers; missing n-gram dictionary file. |
| DeltaLM | `DeltalmTokenizer`. | SentencePiece package and a SentencePiece model file. | `ModuleNotFoundError: sentencepiece` or missing `.spm`/model file. |
| Transformer-XL denoise | `TransfoXLDenoiseTokenizer`. | SentencePiece package and model file. | Same SentencePiece/local-file failures. |
| Taiyi CLIP | `TaiyiCLIPProcessor` and model/embedder helper paths. | Image preprocessing dependencies and text tokenizer/model subfolders for full execution. | Import succeeds but runtime fails due missing checkpoint subfolders or vision dependencies. |
| UniMC/UniEX/TCBert/Ubert | Mostly use Transformers `AutoConfig`, `AutoTokenizer`, or `BertTokenizer` internally. | Local or cached Hugging Face-compatible tokenizer files. | Hidden download attempt when model path is a remote ID and offline cache is empty. |

## Offline and local-only rules

- To inspect a local checkpoint, read `config.json`, `tokenizer_config.json`, and vocabulary files directly before calling any `from_pretrained` method.
- If using Transformers/Fengshen APIs, pass `local_files_only=True` where supported.
- Set Hugging Face offline environment variables only if you want failures to be immediate instead of download attempts.
- Do not run generation helper examples just to test a tokenizer; many examples contain model IDs and will attempt downloads.

## Registering extra mappings

Fengshen auto classes support registration APIs similar to Transformers:

```python
from fengshen.models.auto import AutoConfig, AutoModel
from some_module import MyConfig, MyModel

AutoConfig.register("my-model-type", MyConfig)
AutoModel.register(MyConfig, MyModel)
```

Use registration only in local task code or experiments. Do not edit the installed package mapping as a troubleshooting shortcut. If the checkpoint already has an `auto_map` that requires remote custom code, require an explicit trust decision before using `trust_remote_code=True`.

## Decision checklist

Before selecting an auto/tokenizer route, answer:

1. Is there a local checkpoint directory, or would `from_pretrained` need network access?
2. Does `config.json` contain standard `model_type`, custom `fengshen_model_type`, or both?
3. Is the family one of Fengshen's built-in custom auto mappings (`longformer`, `roformer`)?
4. Does tokenizer metadata name a standard `tokenizer_class`, or does the family require SentencePiece/n-gram files?
5. Is the task only import/config diagnosis, or does it explicitly require loading weights and running inference/training?

If any answer is unknown, keep the check import-only and ask for the missing local config/tokenizer evidence before loading weights.
