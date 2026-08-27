# Inference API and artifact reference

## Model registration and loading

`pointllm/model/pointllm.py` defines the inference classes:

| Symbol | Contract |
|---|---|
| `PointLLMConfig` | Subclass of `LlamaConfig`; `model_type = "pointllm"`. |
| `PointLLMLlamaModel` | Llama model with a PointBERT encoder and point projector. |
| `PointLLMLlamaForCausalLM` | Causal-LM wrapper; `config_class = PointLLMConfig`; accepts `point_clouds` in `forward` and generation. |

At module import, the source registers `PointLLMConfig` with
`AutoConfig.register("pointllm", PointLLMConfig)` and registers
`PointLLMLlamaForCausalLM` with `AutoModelForCausalLM`. The launchers use the
explicit class rather than `AutoModelForCausalLM`, but the registration is
important when a checkpoint config says `model_type: pointllm`.

Canonical load sequence:

```python
from transformers import AutoTokenizer
from pointllm.model import PointLLMLlamaForCausalLM

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = PointLLMLlamaForCausalLM.from_pretrained(
    model_name,
    low_cpu_mem_usage=False,
    use_cache=True,
    torch_dtype=torch.bfloat16,  # chat can choose another dtype
).cuda()
model.initialize_tokenizer_point_backbone_config_wo_embedding(tokenizer)
model.eval()
```

`PointLLMLlamaModel.__init__` reads `config.point_backbone`, constructs
PointBERT, chooses `point_backbone_config_name` (default
`PointTransformer_8192point_2layer`), and derives `point_token_len` from
`num_group + 1` unless the config requests max pooling. The v1.2 YAML has
`num_group: 512`, `point_dims: 3`, and `npoints: 8192`, so its non-max-pooled
feature sequence is normally 513 point tokens. The model sets the projector's
output dimension to the Llama hidden size.

Use the checkpoint's actual `model.config` and
`model.get_model().point_backbone_config`; do not hard-code the token count
when adapting another model version. v1.1 and v1.2 use different PointBERT
configs/checkpoints in the repository documentation.

## Point-token insertion

`initialize_tokenizer_point_backbone_config_wo_embedding` adds the configured
special point patch token and records its tokenizer ID. If
`mm_use_point_start_end` is true, it also adds and records the configured
start/end tokens. The launchers build the first user turn as one of:

```text
<point_start><point_patch> repeated point_token_len times<point_end>\nquestion
```

or, when start/end is disabled:

```text
<point_patch> repeated point_token_len times\nquestion
```

The initial turn must contain the point sequence. Later chat turns do not
insert a second point cloud. The model's forward path replaces those point
patch embeddings with projected PointBERT features. With start/end enabled,
the end token must occur immediately after the feature sequence; without
start/end, patch token IDs must be consecutive and their count must equal the
feature count. A mismatch raises a `ValueError` or yields a malformed prompt.

A point cloud is processed only when `point_clouds` is supplied and the input
sequence is not the one-token cached generation step (or the model is
training). Generation therefore needs the point cloud on the first call and
must preserve it in `prepare_inputs_for_generation`.

## Conversation and stopping

The inference scripts copy `conv_templates["vicuna_v1_1"]`:

- system: `A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.`
- roles: `USER`, `ASSISTANT`
- separator style: `TWO`
- `sep`: one space
- `sep2`: `</s>`
- stop string selected by the scripts: `conv.sep2`, namely `</s>`

`KeywordsStoppingCriteria` watches both one-token keyword IDs and decoded
text. The scripts decode only tokens after the input length, strip whitespace,
and strip a trailing stop string when present.

## Input formats and preprocessing

### Objaverse NPY

`PointLLM_chat.py` loads exactly `<object_id>_8192.npy` under `--data_path`
through `load_objaverse_point_cloud(..., pointnum=8192, use_color=True)`.
The expected array is `(N, 6)` with columns XYZ and RGB. `pc_norm` normalizes
XYZ and preserves RGB. The returned tensor is shaped `(1, N, 6)`, then moved to
CUDA and the selected dtype.

### Gradio PLY and NPY

The Gradio handler supports `.ply` through Open3D and `.npy` through NumPy:

- PLY: vertex positions are XYZ; vertex colors are used if present.
- NPY: columns 0:3 are XYZ; columns 3:6 are RGB when present.
- fewer than 3 NPY columns is rejected.
- absent color receives black RGB.
- a filename containing `no_color` forces black RGB even if the file contains
  colors.
- colors with maximum `<= 1` are treated as `[0, 1]`; colors with maximum
  `<= 255` are treated as `[0, 255]` and divided by 255. Keep the intended
  input in a finite range; the source has no explicit lower-bound check.
- points and normalized colors are concatenated to `(N, 6)`.
- if `N > 8192`, `farthest_point_sample(points, 8192)` samples by XYZ.
- `pc_norm` then centers and unit-sphere-normalizes XYZ.

A PLY/object visualization is rendered separately. The point tensor sent to the
model is float32 on CUDA before generation. The selected model dtype is
applied by the model's generation path; the interactive chat explicitly casts
the tensor to the chosen dtype.

### ModelNet

`ModelNet` reads a processed pickle-like `.dat` file selected by its bundled
config. It normalizes XYZ to a unit sphere, drops normals unless configured,
and with `--use_color` appends zero-valued RGB channels. The inference launcher
moves a batch to CUDA and casts it to `model.dtype`. This is not a PLY/NPY
file-upload API.

## Generation contract

All four inference paths use `model.generate` with:

```python
do_sample=True
 temperature=1.0
top_k=50
max_length=2048
top_p=0.95
stopping_criteria=[KeywordsStoppingCriteria(["</s>"], tokenizer, input_ids)]
```

`max_length=2048` is total sequence length. The Gradio path explicitly rejects
an input prompt with `input_ids.shape[1] >= 2047`, because no useful generated
token would remain. Long multi-round conversations need `Clear`; point tokens
alone consume roughly 513 positions (plus delimiters, system text, question,
and response history).

## Output JSON contracts

### Shared envelope

The batch launchers write a JSON object:

```json
{
  "prompt": "What is this?",
  "results": [
    {
      "object_id": "object-or-index",
      "ground_truth": "reference value or integer label",
      "model_output": "decoded assistant text"
    }
  ]
}
```

Objaverse uses `object_id` strings and `ground_truth` from the annotation's
second conversation value. Its filename is:

```text
<annotation-basename>_Objaverse_<task_type>_prompt<prompt_index>.json
```

and its directory is `<model_name>/evaluation/`.

ModelNet adds the class fields:

```json
{
  "object_id": 0,
  "ground_truth": 12,
  "model_output": "chair",
  "label_name": "chair"
}
```

Its filename is `ModelNet_classification_prompt<prompt_index>.json` under the
same evaluation directory. Existing files are loaded rather than overwritten
by a new generation run.

The interactive chat and Gradio demo do not emit a model-result JSON contract;
they print/stream assistant text and maintain UI state. Gradio also writes a
log file and may use its temporary upload directory.
