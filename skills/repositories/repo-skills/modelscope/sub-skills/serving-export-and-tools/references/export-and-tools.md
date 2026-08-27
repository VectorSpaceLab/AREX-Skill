# Exporter APIs and checkpoint utilities

Use this reference to decide whether ModelScope exporter APIs or bundled utility
scripts are appropriate, and to avoid destructive checkpoint operations without
planning and backup.

## Exporter module overview

ModelScope exposes exporter classes through `modelscope.exporters`:

- `Exporter`: abstract base with `Exporter.from_model(model_or_id, **kwargs)`.
  When passed a string, it loads a ModelScope model and reads that model's
  `configuration.json` to select a registered exporter by task/model type.
- `TorchModelExporter`: base implementation for PyTorch ONNX and TorchScript
  export. Model-specific exporters can override input generation, dynamic axes,
  or export behavior.
- `TfModelExporter`: base implementation for TensorFlow ONNX export and a base
  for model-specific SavedModel/frozen-graph exporters.
- Registered domain exporters exist for selected NLP, CV, audio, and
  multi-modal models. Unsupported task/model combinations raise a key error or a
  `NotImplementedError` from the exporter.

Typical ModelScope model export pattern:

```python
from modelscope.exporters import Exporter
from modelscope.models import Model

model = Model.from_pretrained("damo/nlp_structbert_sentence-similarity_chinese-base")
exporter = Exporter.from_model(model)
outputs = exporter.export_onnx(output_dir="./exported", opset=13)
print(outputs)  # commonly {'model': './exported/model.onnx'}
```

Typical direct PyTorch module export pattern when no ModelScope-specific
exporter is registered:

```python
from collections import OrderedDict
from modelscope.exporters import TorchModelExporter

# model and dummy_inputs are supplied by the caller's own code.
dynamic_axis = {0: "batch", 1: "sequence"}
outputs = TorchModelExporter().export_onnx(
    model=model,
    dummy_inputs=dummy_inputs,
    inputs=OrderedDict([
        ("input_ids", dynamic_axis),
        ("attention_mask", dynamic_axis),
    ]),
    outputs=OrderedDict({"logits": {0: "batch"}}),
    output_dir="./exported",
    opset=13,
)
print(outputs)
```

TorchScript pattern:

```python
from modelscope.exporters import TorchModelExporter

outputs = TorchModelExporter().export_torch_script(
    model=model,
    dummy_inputs=dummy_inputs,
    output_dir="./exported",
    strict=False,
)
print(outputs)  # commonly {'model': './exported/model.ts'}
```

TensorFlow ONNX pattern for a caller-supplied Keras/TF2 model:

```python
from modelscope.exporters import TfModelExporter

outputs = TfModelExporter().export_onnx(
    model=tf_model,
    dummy_inputs={"input": input_tensor},
    call_func=lambda inputs: [tf_model.predict(list(inputs.values())[0])],
    output_dir="./exported",
    opset=13,
)
print(outputs)
```

TensorFlow model-specific exporters may also implement `export_saved_model()` or
`export_frozen_graph_def()`. For example, the translation exporter implements
SavedModel/frozen graph outputs and explicitly does not support ONNX. The
cartoon translation exporter implements frozen graph export and explicitly does
not support ONNX or SavedModel.

## Optional dependencies and validation behavior

Exporter dependencies are intentionally optional and vary by model:

- PyTorch export needs `torch`; ONNX export validation additionally needs `onnx`
  and `onnxruntime`.
- TensorFlow export needs `tensorflow`; TF-to-ONNX export also needs `tf2onnx`,
  `onnx`, and usually `onnxruntime` for validation.
- Domain exporters may need `transformers`, CV/audio/multi-modal packages, or
  model-specific framework versions.
- ONNX Runtime validation tries `CUDAExecutionProvider` and
  `CPUExecutionProvider`, but CUDA execution is optional and unverified here.
  Do not claim GPU validation unless the target environment actually ran it.

ModelScope's base exporters commonly validate exported outputs against the
original model. If validation dependencies are missing, ONNX validation can be
skipped with a warning by base paths; model-specific exporters may behave
differently. If exactness matters, install the validation dependencies and keep
`validation=True`.

## Export support triage

Before promising an export workflow:

1. Identify the model framework and task/model type.
2. Check whether `Exporter.from_model(model)` succeeds.
3. Check which methods are implemented: `export_onnx`, `export_torch_script`,
   `export_saved_model`, `export_frozen_graph_def`.
4. Confirm dummy input requirements. Some exporters require shape kwargs such as
   `shape=(2, 256)` or `input_shape=(1, 3, 640, 640)`.
5. Confirm that export output goes to a new/empty directory with enough disk
   space.
6. Run a small validation export before scaling up to large models.

Common output names from base constants are `model.onnx` for ONNX and
`model.ts` for TorchScript, but model-specific exporters can return other paths
or multiple files. Always inspect the returned dict.

## Checkpoint conversion utilities

The repository includes utility scripts for legacy checkpoints, Megatron
checkpoint conversion, and weight diffs. They are useful but not safe to run
blindly on production artifacts.

### Legacy `.pth` split utility (`convert_ckpt`)

Purpose: split old ModelScope `.pth` checkpoint files into state-dict and trainer
state files.

Observed behavior:

1. Iterates over every `*.pth` file directly inside the provided directory.
2. Copies each original file to `<filename>.pth.legacy`.
3. Loads the original `.pth` with `torch.load(..., map_location='cpu', weights_only=True)`.
4. If the object has a top-level `state_dict`, saves that `state_dict` back to
   the original `.pth` path, mutating the original file.
5. Saves remaining trainer metadata to `<stem>_trainer_state.pth`.
6. If there is no top-level `state_dict`, the state object is saved back to the
   original path and a trainer-state file is still written from the checkpoint
   object after the state extraction logic.

Safety requirements:

- Run only on a copied working directory or after making an external backup.
- First run the bundled dry-run planner:

  ```bash
  python scripts/checkpoint_conversion_plan.py --dir /path/to/checkpoint-copy
  ```

- Review every planned original, legacy backup, and trainer-state path.
- Ensure there is enough disk space for at least one full extra copy of each
  `.pth` file plus trainer-state outputs.
- For sharded GPT/Megatron-style checkpoints, expect manual filename review
  after conversion; the original utility notes that some sharded model filenames
  may need manual renaming after conversion.

### Megatron conversion utility (`convert_megatron_ckpt`)

Purpose: split or merge Megatron-based checkpoints by loading a ModelScope model
and calling ModelScope's Megatron conversion helper.

Operational requirements:

- Requires a distributed launch environment. The Python script reads `RANK` and
  `WORLD_SIZE` environment variables; the shell example uses `torchrun` with a
  target tensor parallel size.
- Requires the source model directory/id and a target output directory.
- Requires model-specific Megatron support and enough CPU/GPU memory/disk for
  the model.
- May download the model if a remote id is supplied and the cache is missing.

Pattern, to adapt only after preflight:

```bash
TARGET_TENSOR_MODEL_PARALLEL_SIZE=1
MODEL_DIR="/path/to/local-or-cached-megatron-model"
TARGET_DIR="/path/to/new-output-dir"

torchrun --nproc_per_node "$TARGET_TENSOR_MODEL_PARALLEL_SIZE" \
  -m tools.convert_megatron_ckpt \
  --model_dir "$MODEL_DIR" \
  --target_dir "$TARGET_DIR"
```

Do not run this from the generated skill tree expecting `tools.convert...` to
exist. In a project that needs it, use the installed package/repository utility
from that project's source tree or vendor a separate audited wrapper. This
sub-skill only documents the requirements and safety gates.

### Weight diff and recover utility (`weight_diff`)

Purpose: compute a parameter difference between raw and tuned models, or recover
tuned weights by adding a diff back to a raw model.

Operational behavior and risks:

- Inputs are `make_diff_or_recover` (`diff` or `recover`), `path_raw`,
  `path_convert`, and `path_to_save`.
- If `path_raw` or `path_convert` does not exist locally, the utility tries
  ModelScope `snapshot_download`, which can perform large network downloads.
- It loads both models with `Model.from_pretrained` and tokenizers with
  HuggingFace `AutoTokenizer.from_pretrained`.
- It requires the raw and converted model classes and tensor shapes to match,
  aside from tokenizer special-token resizing handled by the utility.
- It mutates in-memory tensors by adding/subtracting weights and then saves a
  full model/tokenizer to `path_to_save`.
- Large LLMs require large RAM/VRAM/disk. The default device is CPU in the
  utility function, but that does not make the operation small.

Safe pattern:

```bash
python /path/to/weight_diff.py diff \
  /path/to/raw-model \
  /path/to/tuned-model \
  /path/to/new-diff-output

python /path/to/weight_diff.py recover \
  /path/to/raw-model \
  /path/to/diff-model \
  /path/to/new-recovered-output
```

Use local paths when downloads are not explicitly allowed. Write to a new output
directory, not over an input directory.

## Planner script bundled with this sub-skill

`checkpoint_conversion_plan.py` is a deterministic dry-run planner for the
legacy `.pth` split utility. It never imports torch and never writes checkpoint
files. It lists the files a conversion would inspect and the paths it would
create or mutate.

Example:

```bash
python scripts/checkpoint_conversion_plan.py --dir ./checkpoints-copy
python scripts/checkpoint_conversion_plan.py --dir ./checkpoints-copy --json
```

Use the planner as a gate before any destructive checkpoint operation. It does
not prove that `torch.load` will succeed or that each checkpoint contains a
`state_dict`; it only reports path-level side effects and file-size estimates.
