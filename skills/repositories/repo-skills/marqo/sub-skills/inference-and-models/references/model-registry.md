# Model registry reference

This reference covers Marqo embedding model names and `modelProperties` shapes used by the inference service and higher-level Marqo API clients.

## Lookup contract

- A registry lookup returns a JSON-compatible `dict` of model properties.
- Unknown registry names surface as an unsupported-model error from Marqo's inference layer.
- `MARQO_DEFAULT_MODELS_S3_BUCKET` supplies the bucket prefix for default ONNX sources. The default is `s3://marqo-default-models-os`; empty values are rejected, a missing `s3://` prefix is added, and trailing slashes are removed.
- Shallow validation only checks that `modelProperties` has `dimensions` and `type`; detailed validation happens when `/vectorise` loads the family-specific model class.
- Direct inference-orchestrator requests should include full `modelProperties`. Supplying only `modelName` is not enough for the direct `/vectorise` path.

## Shared model-property fields

| Field | Meaning | Notes |
| --- | --- | --- |
| `name` | Backend model identifier | May be a registry key, `hf-hub:*`, `open_clip/*`, or a preserved legacy name. |
| `tritonModelName` | Optional runtime override | If set, loaders use it as the effective backend name while preserving `name` for stored metadata/cache stability. |
| `dimensions` | Embedding width | Must be a positive integer. |
| `type` | Loader family | Valid values are `random`, `hf`, and `open_clip`. |
| `tritonTextEncoderProperties` | Text encoder loaded into Triton | Required for `hf`; required for `open_clip`. |
| `tritonImageEncoderProperties` | Image encoder loaded into Triton | Required for `open_clip`. |

## Default registry families

### Random models

Random models are deterministic hash-seeded embedding generators. They do not download models, do not call model-management, and do not call Triton. Use them to isolate request-shape, preprocessing, cache, and route issues from backend-model issues.

| Model | Dimensions | Tokens | Best use |
| --- | ---: | ---: | --- |
| `random/small` | 32 | 128 | Fastest no-download smoke check. |
| `random/medium` | 128 | 128 | Shape closer to small semantic models. |
| `random` | 384 | 128 | Default random model. |
| `random/large` | 768 | 128 | Shape closer to large text/multimodal models. |

Minimal random `modelProperties`:

```json
{
  "name": "random/small",
  "dimensions": 32,
  "tokens": 128,
  "type": "random",
  "notes": ""
}
```

### Hugging Face text models

HF models are text encoders. They use a tokenizer, a Triton text encoder, and either mean or CLS pooling over `last_hidden_state`.

| Model | Dimensions | Tokens | Notes |
| --- | ---: | ---: | --- |
| `hf/e5-base-v2` | 768 | 512 | Mean pooling; E5-style query/passage prefixes are present in registry metadata. |
| `hf/e5-small-v2` | 384 | 512 | Mean pooling; smaller E5 variant. |
| `hf/all-MiniLM-L6-v2` | 384 | 256 | Mean pooling; small general text embedding model. |

HF custom-property requirements:

- `type` must be `hf`.
- `poolingMethod` must be `mean` or `cls`.
- `tritonTextEncoderProperties.input` must be exactly `input_ids`, `attention_mask`, `token_type_ids` in that order.
- `tritonTextEncoderProperties.output` must be exactly `last_hidden_state`.
- `tokens` controls tokenizer truncation length.

Skeleton HF `modelProperties`:

```json
{
  "name": "sentence-transformers/all-MiniLM-L6-v2",
  "type": "hf",
  "dimensions": 384,
  "tokens": 256,
  "poolingMethod": "mean",
  "tritonTextEncoderProperties": {
    "name": "all-MiniLM-L6-v2-text-encoder",
    "maxBatchSize": 32,
    "sources": ["s3://example-bucket/all-MiniLM-L6-v2/model.onnx"],
    "input": [
      {"name": "input_ids", "dims": [-1], "dataType": "TYPE_INT64"},
      {"name": "attention_mask", "dims": [-1], "dataType": "TYPE_INT64"},
      {"name": "token_type_ids", "dims": [-1], "dataType": "TYPE_INT64"}
    ],
    "output": [
      {"name": "last_hidden_state", "dims": [-1, 384], "dataType": "TYPE_FP32"}
    ]
  }
}
```

### OpenCLIP multimodal models

OpenCLIP models support text and image inference. They load a tokenizer and image preprocessor locally, then use separate Triton text and image encoders.

Default OpenCLIP registry entries:

| Model | Dimensions |
| --- | ---: |
| `Marqo/marqo-fashionCLIP` | 512 |
| `Marqo/marqo-fashionSigLIP` | 768 |
| `Marqo/marqo-ecommerce-embeddings-L` | 1024 |
| `Marqo/marqo-ecommerce-embeddings-B` | 768 |
| `timm/ViT-L-16-SigLIP2-256` | 1024 |
| `open_clip/ViT-L-16-SigLIP-256/webli` | 1024 |
| `open_clip/ViT-L-14/laion2b_s32b_b82k` | 768 |
| `timm/ViT-B-16-SigLIP2-256` | 768 |
| `open_clip/ViT-B-32/laion2b_s34b_b79k` | 512 |
| `open_clip/ViT-B-16-SigLIP/webli` | 768 |
| `open_clip/ViT-L-14/laion400m_e32` | 768 |
| `laion/CLIP-ViT-B-32-xlm-roberta-base-laion5B-s13B-b90k` | 512 |

OpenCLIP custom-property requirements:

- `type` must be `open_clip`.
- Effective backend name must start with `hf-hub:` or `open_clip/`.
- `imagePreprocessor` accepts `SigLIP`, `OpenAI`, `OpenCLIP`, or `CLIPA`.
- Optional fields include `tokenizer`, `mean`, `std`, `size`, and `note`.
- Text and image encoder properties are both required.
- OpenCLIP Triton text/image encoder inputs should be named `input`; outputs should be named `output`.

Skeleton OpenCLIP `modelProperties`:

```json
{
  "name": "open_clip/ViT-B-32/laion2b_s34b_b79k",
  "type": "open_clip",
  "dimensions": 512,
  "imagePreprocessor": "OpenCLIP",
  "tritonTextEncoderProperties": {
    "name": "clip-text-encoder",
    "maxBatchSize": 16,
    "sources": ["s3://example-bucket/text-encoder/model.onnx"],
    "input": [{"name": "input", "dims": [77], "dataType": "TYPE_INT32"}],
    "output": [{"name": "output", "dims": [512], "dataType": "TYPE_FP32"}]
  },
  "tritonImageEncoderProperties": {
    "name": "clip-image-encoder",
    "maxBatchSize": 8,
    "sources": ["s3://example-bucket/image-encoder/model.onnx"],
    "input": [{"name": "input", "dims": [3, 224, 224], "dataType": "TYPE_FP32"}],
    "output": [{"name": "output", "dims": [512], "dataType": "TYPE_FP32"}]
  }
}
```

## Choosing between families

- Use `random/small` when the task is to debug `/vectorise`, cache behavior, or CUDA availability without external side effects.
- Use `hf/*` when inputs are text-only and the expected output is a semantic text embedding.
- Use `open_clip/*` when image embeddings or cross-modal text/image embeddings are needed.
- Use `tritonModelName` only when backend loading should use a different identifier than the persisted `name`.
