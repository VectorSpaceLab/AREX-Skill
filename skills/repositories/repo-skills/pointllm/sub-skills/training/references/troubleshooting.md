# PointLLM training troubleshooting

Use the validator first. Treat the first failing layer as the root cause; do
not mask it by changing stages, disabling FSDP, or deleting checkpoints.

## Installation and import failures

| Symptom | Likely cause | Safe action |
|---|---|---|
| `No module named pointllm` | The package is not installed or the project root is absent from `PYTHONPATH`. | Install the package in the intended environment or set `PYTHONPATH` to the project root for a controlled check. Do not edit `sys.path` in the skill. |
| `No module named flash_attn` from `train_mem.py` | The memory-efficient entry point imports the compiled FlashAttention extension before training. | Stop. Verify a build compatible with the supplied torch/CUDA/Transformers baseline, or test the unpatched `train.py` path separately. Do not claim equivalent throughput or memory. |
| `No module named cv2` from `train_mem.py` | The checked-in monkey patch imports `cv2.exp` before it reaches FlashAttention. | Treat OpenCV as an additional precondition for this optional optimized path; do not infer that FlashAttention is installed or remove the import silently. |
| `ImportError` in `flash_attn_interface` | FlashAttention API mismatch: the patch tries `flash_attn_unpadded_qkvpacked_func` and only then the renamed varlen symbol. | Inspect the installed extension's API and pin/build a compatible version outside this skill. Never patch the runtime file during a run. |
| `No module named easydict`, `easydict`, `timm`, `open3d`, or similar | A package listed by the project metadata is missing from the inspection/runtime environment. | Stop and repair the environment through the approved environment workflow. The validator can still check paths and flags without importing torch. |
| Transformers registration/config errors | Transformers is not the tested `cae78c46` development snapshot or a compatible fork. | Record the exact version/commit, compare against the baseline, and do not mix an arbitrary current Transformers release with the old monkey patch. |

`train_mem.py` is not a no-op wrapper: it monkey-patches Llama attention before
`train.py` imports the model. It asserts that attention outputs, cache use, and
past-key-value use are disabled. `train.py` avoids the explicit FlashAttention
import and is the only source-provided unpatched entry point; its results and
resource needs still require a separate smoke test.

## Dependencies and backends

- **bf16:** `bf16=True` is used in both shell profiles. An A100 compute
  capability 8.0 is suitable in principle, but a CUDA 11.7/PyTorch 2.0.1
  installation still needs a real tensor-operation smoke test. A CPU-only
  fallback is not an equivalent training run.
- **FSDP:** Stage 2 requests `full_shard auto_wrap` around
  `LlamaDecoderLayer`. The code detects frozen parameters and monkey-patches
  FSDP construction to pass `use_orig_params=True`, while warning that this
  is experimental and historically needed a PyTorch nightly build. A failure
  here is a required-backend block, not a reason to silently run an altered
  recipe.
- **deepspeed:** It is listed in project dependencies but the shipped Stage-2
  shell selects FSDP, not a DeepSpeed config. Do not infer that DeepSpeed is
  required for this exact command or that installing it fixes FSDP.
- **gradient checkpointing:** The profiles enable it, and the code disables
  `model.config.use_cache` before training. If a custom profile re-enables
  cache, stop rather than accepting the contradictory memory setting.
- **W&B:** `report_to=wandb` and a run name are explicit. An unavailable or
  unauthorized logger can fail before useful batches; use an approved logging
  configuration change and record it rather than declaring the model trained.

## Data and configuration failures

| Symptom | Check |
|---|---|
| Annotation open/JSON error | `anno_path` must be a readable JSON file containing the expected list of records. The dataclass default `None` is not a usable training path. |
| `FileNotFoundError` for a point cloud | The expected name is `<object_id>_<pointnum>.npy`; with the default, use `_8192.npy`. Check the annotation object ID and `data_path` before changing `pointnum`. |
| Shape/channel error in PointBERT | `use_color=True` expects six columns and configures `point_dims=6`; `False` slices to XYZ. Match data, model config, and checkpoint. |
| Empty dataset | Check `conversation_types`, the two color-filtered IDs, `data_debug_num`, and the train/validation split. Stage 1 uses simple descriptions; Stage 2 explicitly filters the three complex types. |
| Point-token mismatch or non-consecutive patch tokens | The model expands `<point>` into `point_token_len` patch tokens. Check the model's PointBERT YAML, tokenizer special tokens, and annotations; do not hand-edit token IDs in a JSON file. |
| Tokenization mismatch warning and all labels ignored | The conversation parser found a prompt/token count mismatch, often due to unsupported formatting or truncation. Inspect the offending annotation and keep the original Vicuna v1.1 template. |
| Unexpected validation behavior | `split_train_val=False` and `evaluation_strategy=no` are both set in the profiles. `eval_steps=100` in Stage 2 has no effect while evaluation is disabled. |
| v1.1/v1.2 load failure or bad dimensions | Pair `PointTransformer_8192point_2layer` with `point_bert_v1.2.pt`, or pair `PointTransformer_base_8192point` with `point_bert_v1.1.pt`; do not mix families. |

## API and CLI failures

- Use the exact snake_case dataclass flag names shown in the references. The
  Hugging Face parser converts them into dataclass fields; a misspelled flag
  can fail parsing before any model is loaded.
- `train_mem.py --help` is still an import-time check because its monkey patch
  imports FlashAttention first. A help failure due to a missing extension is an
  environment fact, not evidence that the argument schema is wrong.
- `train.py --help` also imports the package/model registration before parsing;
  missing package dependencies can therefore prevent help output. Use the
  bundled validator for dependency-free flag and path checks.
- `model_debug=True` builds a model from config rather than loading weights. It
  is not a safe way to bypass missing data or a missing point-backbone file.
- `pretrained_mm_mlp_adapter` and `force_fsdp` are declared fields but have no
  direct branch in the visible training body. Do not report that either flag
  loaded an adapter or forced FSDP without additional evidence.

## Workflow, checkpoint, and resume failures

1. **Stage 1 starts from the wrong model:** The source calls
   `from_pretrained(model_name_or_path)` and then separately loads
   `point_backbone_ckpt`. Confirm both paths before launch.
2. **Stage 2 cannot find point modules:** Stage 2 does not load a separate
   `point_backbone_ckpt`; it assumes the Stage-1 directory contains the model
   config and learned point modules. Restore the complete output or rerun Stage
   1 rather than pointing Stage 2 at an adapter-only artifact.
3. **Unexpected resume:** Any `output_dir/checkpoint-*` directory triggers
   `resume_from_checkpoint=True`, regardless of whether it is the intended
   run. Inspect trainer state and checkpoint provenance. Do not delete it as a
   first response.
4. **No checkpoint after interruption:** The profiles set `save_strategy=no`.
   A killed job may have only logs or a final partial directory; this is not a
   resumable checkpoint unless a valid `checkpoint-*` state exists.
5. **Missing `point_proj.bin`:** It is written by the custom trainer only when
   `tune_mm_mlp_adapter=True` and the final save path is reached. Check whether
   the run stopped before final save or explicitly froze the adapter.
6. **No loss/optimizer updates:** Check the freeze truth table. Stage 1 with
   both fix flags true intentionally does not update the backbone; Stage 2's
   fixed point backbone executes without gradient. A custom combination that
   freezes LLM, backbone, and projector has no meaningful trainable path.
7. **Out-of-memory on the first batch:** Do not immediately increase process
   count or remove gradient checkpointing. First reduce a planned batch size,
   verify point-token expansion and bf16, and record that the source profile's
   eight-process sizing was not reproduced.
8. **FSDP hangs or wrapper errors:** Stop at the first distributed error; check
   process count, `LlamaDecoderLayer` spelling, `use_orig_params` support, and
   PyTorch/Transformers compatibility. Running without FSDP is a new profile,
   not a successful Stage-2 reproduction.

## Safe stop conditions

Stop and hand off an unverified run when any of these is true: required local
inputs are absent; the compiled FlashAttention or FSDP backend is incompatible;
model/config and point-backbone families disagree; the data loader returns an
empty or malformed batch; a checkpoint's provenance is unclear; the first
forward pass raises a point-token or dtype error; or final model/adapter state
was not saved. Report the exact command/profile, last observed log line, and
which artifact is missing. Never convert a configuration check into a claim of
training success.
