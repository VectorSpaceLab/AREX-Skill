# Backend Export Reference

Sentence Transformers supports `backend="torch"`, `backend="onnx"`, and `backend="openvino"` on `SentenceTransformer`, `CrossEncoder`, and `SparseEncoder`. The backend is selected at model construction time and controls how the underlying Transformer component is loaded or exported.

## Backend Selection Matrix

| Goal | Backend | Install extra | Primary knobs | Notes |
| --- | --- | --- | --- | --- |
| Maximum compatibility | `torch` | base package | `device`, `model_kwargs={"torch_dtype": "float16"}` or `"bfloat16"` | Default backend; can use GPU dtype and attention options when supported. |
| ONNX Runtime inference | `onnx` | `sentence-transformers[onnx]` or `[onnx-gpu]` | `model_kwargs={"provider": ..., "file_name": ..., "export": ...}` | Uses Optimum ONNX Runtime. CPU installs use `[onnx]`; GPU installs use `[onnx-gpu]`. |
| OpenVINO inference | `openvino` | `sentence-transformers[openvino]` | `model_kwargs={"file_name": ..., "export": ..., "ov_config": ...}` | Good CPU/Intel target; `ov_config` can be a dict or path to a JSON config. |

The same backend argument applies to:

```python
from sentence_transformers import CrossEncoder, SentenceTransformer, SparseEncoder

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", backend="onnx")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2", backend="onnx")
sparse_model = SparseEncoder("naver/splade-v3", backend="openvino")
```

## Loading, Exporting, and File Names

When `backend="onnx"` or `backend="openvino"` is used, Sentence Transformers looks for an existing backend file in the model directory or repository. If no matching file exists, it exports one unless `model_kwargs={"export": False}` is set.

Common `model_kwargs`:

- `export`: Force or forbid export. Use `False` when a file must already exist; use `True` when intentionally converting from the base model.
- `file_name`: Select a specific file, especially optimized or quantized variants such as `onnx/model_O3.onnx` or `openvino/openvino_model_qint8_quantized.xml`.
- `subfolder`: Select a repository subfolder separately from `file_name` when needed.
- `provider`: ONNX Runtime provider such as `CPUExecutionProvider`; if omitted, ONNX Runtime chooses the highest-priority available provider.
- `ov_config`: OpenVINO runtime/config options as a dictionary or a JSON config path.

Examples:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    backend="onnx",
    model_kwargs={"file_name": "onnx/model_O3.onnx", "provider": "CPUExecutionProvider"},
)
```

```python
from sentence_transformers import CrossEncoder

model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L6-v2",
    backend="openvino",
    model_kwargs={"file_name": "openvino/openvino_model_qint8_quantized.xml"},
)
```

Save exported local artifacts so future runs do not export again:

```python
model = SentenceTransformer("path/to/my-model", backend="onnx")
model.save_pretrained("path/to/my-model")
```

For Hub models, create a pull request rather than overwriting upstream files directly:

```python
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", backend="onnx")
model.push_to_hub("sentence-transformers/all-MiniLM-L6-v2", create_pr=True)
```

## ONNX Optimization

Use `export_optimized_onnx_model` only with a model loaded using `backend="onnx"`.

```python
from sentence_transformers import SentenceTransformer, export_optimized_onnx_model

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", backend="onnx")
export_optimized_onnx_model(
    model=model,
    optimization_config="O3",
    model_name_or_path="sentence-transformers/all-MiniLM-L6-v2",
    push_to_hub=True,
    create_pr=True,
)
```

Optimization levels:

- `O1`: basic general optimizations.
- `O2`: basic plus extended general optimizations and Transformer fusions.
- `O3`: `O2` plus GELU approximation.
- `O4`: `O3` plus mixed precision; GPU-oriented.

Default output naming uses the optimization level as the suffix for string configs, such as `onnx/model_O3.onnx`. If a custom config is used and `file_suffix` is omitted, the suffix is `optimized`.

Load a Hub PR before merge with the PR revision and matching file name:

```python
from sentence_transformers import SentenceTransformer

pr_number = 2
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    revision=f"refs/pr/{pr_number}",
    backend="onnx",
    model_kwargs={"file_name": "onnx/model_O3.onnx"},
)
```

## ONNX Dynamic Quantization

Use `export_dynamic_quantized_onnx_model` only with a model loaded using `backend="onnx"`. Dynamic quantization does not require a calibration dataset and is primarily useful for CPU inference.

```python
from sentence_transformers import SentenceTransformer, export_dynamic_quantized_onnx_model

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", backend="onnx")
export_dynamic_quantized_onnx_model(
    model=model,
    quantization_config="avx512_vnni",
    model_name_or_path="sentence-transformers/all-MiniLM-L6-v2",
    push_to_hub=True,
    create_pr=True,
)
```

Supported string configs are `arm64`, `avx2`, `avx512`, and `avx512_vnni`. For string configs, default output names include the weight dtype and config, such as `onnx/model_qint8_avx512_vnni.onnx`. If a custom quantization config is used and `file_suffix` is omitted, the fallback suffix is based on the quantized weight dtype, such as `qint8_quantized`.

Load a quantized variant by matching the file name:

```python
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    backend="onnx",
    model_kwargs={"file_name": "onnx/model_qint8_avx512_vnni.onnx"},
)
```

## OpenVINO Static Quantization

Use `export_static_quantized_openvino_model` only with a model loaded using `backend="openvino"`. Static quantization uses a calibration dataset. If dataset arguments are omitted, the helper uses its default calibration dataset and column. If any dataset override is supplied, supply all of `dataset_name`, `dataset_config_name`, `dataset_split`, and `column_name`.

```python
from sentence_transformers import SentenceTransformer, export_static_quantized_openvino_model

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", backend="openvino")
export_static_quantized_openvino_model(
    model=model,
    quantization_config=None,
    model_name_or_path="sentence-transformers/all-MiniLM-L6-v2",
    dataset_name="nyu-mll/glue",
    dataset_config_name="sst2",
    dataset_split="train",
    column_name="sentence",
    push_to_hub=True,
    create_pr=True,
)
```

The default file suffix is `qint8_quantized`, which creates `openvino/openvino_model_qint8_quantized.xml` plus the paired `.bin` file. Always load the `.xml` file name; the `.bin` is used alongside it.

```python
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    backend="openvino",
    model_kwargs={"file_name": "openvino/openvino_model_qint8_quantized.xml"},
)
```

## Model-Type Specific Caveats

- `SentenceTransformer`: ONNX/OpenVINO export converts the Transformer component. Outside Sentence Transformers, apply the model's pooling and normalization to turn token embeddings into sentence embeddings.
- `CrossEncoder`: Outside Sentence Transformers, reproduce the activation or sigmoid/softmax behavior expected by your scorer.
- `SparseEncoder`: ONNX/OpenVINO export converts the masked-language-model Transformer component. Outside Sentence Transformers, apply SPLADE pooling and any normalization needed for full sparse text vectors.

## Backend Quantization vs Output-Vector Quantization

Backend quantization changes the inference artifact (`model_*.onnx` or `openvino_model_*.xml`) to speed model execution. Output-vector quantization changes computed embeddings after inference, for example binary or scalar vectors used to reduce storage and accelerate retrieval. If the user asks about smaller indexes, binary embeddings, scalar quantized vectors, or Matryoshka truncation, route to retrieval utilities rather than this backend export workflow.
