# EasyR1 checkpoint export

This reference distills EasyR1 checkpoint and model-merger behavior for exporting a saved **actor** checkpoint to Hugging Face format. It is for post-training export only; creating checkpoints by launching training is owned by the training workflow guidance.

## Expected input directory

Export starts from an actor checkpoint directory, usually selected from a save tree like this:

```text
<save_checkpoint_path>/
  checkpoint_tracker.json
  global_step_<step>/
    actor/
      model_world_size_<world_size>_rank_0.pt
      model_world_size_<world_size>_rank_1.pt
      ...
      huggingface/
        config.json
        generation_config.json          # optional but should be preserved if present
        tokenizer/processor files       # model-family dependent
      lora_adapter/                     # present only for LoRA runs
        adapter_config.json
        adapter_model.safetensors       # commonly saved for adapter reuse
    critic/                             # present only when a critic is used
    dataloader.pt                       # training resume state, not needed for actor export
```

Point export tools at the `actor/` directory. Do not pass the parent `global_step_<step>/` directory and do not pass the `actor/huggingface/` child.

### Tracker helper semantics

EasyR1 writes `checkpoint_tracker.json` in the save root. The useful fields are:

- `last_global_step`: latest saved step; the corresponding actor directory is `global_step_<last_global_step>/actor`.
- `best_global_step` and `best_val_reward_score`: used by retention/resume logic; they can identify the best checkpoint when validation is enabled.
- `last_actor_path`: an absolute path recorded when training saved the checkpoint; after copying or moving checkpoints, prefer reconstructing the actor path from `last_global_step` instead of trusting this value.

Checkpoint retention removes older `global_step_<N>` directories according to `save_limit`, while preserving the best step when possible. Missing older checkpoints may be expected if retention was enabled.

## Safe preflight

Run the bundled inspector before loading any checkpoint shards:

```bash
python scripts/easyr1_checkpoint_inspector.py <actor_checkpoint_dir>
python scripts/easyr1_checkpoint_inspector.py --json <actor_checkpoint_dir>
```

The inspector checks only filenames and metadata JSON. It does not import PyTorch and does not load `.pt` model weights. It verifies:

- `model_world_size_<N>_rank_<R>.pt` naming.
- exactly one model `world_size` group.
- rank `0` exists and ranks are contiguous within the advertised world size.
- `huggingface/config.json` exists and has an architecture family supported by the merger.
- optional `huggingface/generation_config.json` is valid JSON.
- optional `lora_adapter/adapter_config.json` is valid and includes `base_model_name_or_path`.

Use JSON output when another script or verification case needs machine-readable errors and warnings.

## Export command shape

EasyR1's merger interface has this shape:

```bash
python3 model_merger.py --local_dir <actor_checkpoint_dir>
python3 model_merger.py --local_dir <actor_checkpoint_dir> --hf_upload_path <namespace>/<model-name>
```

If the merger utility is exposed under a different path or wrapper in the active project, keep the same arguments: `--local_dir` must be the actor directory and `--hf_upload_path` is optional. The output is written into `<actor_checkpoint_dir>/huggingface/`.

Important preconditions:

- `--local_dir` must not be the `huggingface/` output directory itself.
- CPU RAM must be large enough to load and merge all required shards; the merger uses CPU loading and bf16 tensors, but large checkpoints are still memory-intensive.
- The EasyR1 training runtime is not proven by this export check. Full training requires CUDA plus the EasyR1 flash-attn/vLLM/Ray stack.

## Distilled model-merger logic

The merger performs these steps:

1. Resolve `--local_dir` to an absolute actor directory and reject paths ending in `huggingface`.
2. Find `model_world_size_<W>_rank_0.pt` and load rank 0 on CPU.
3. Inspect rank 0 values:
   - If values are PyTorch `DTensor`, read the `device_mesh` and `mesh_dim_names`.
   - Supported mesh names are `("fsdp",)` and `("ddp", "fsdp")`.
   - `tp`/FSDP+TP layouts are not supported by the merger.
   - Partial DTensor placements are not supported.
4. Load the required rank shards on CPU.
   - For DTensor shard placement, concatenate local tensors on the shard dimension.
   - For replicated placement, keep rank 0.
   - For non-DTensor state dicts, concatenate tensors along dimension 0.
5. Read `huggingface/config.json` and choose an auto model class from `architectures[0]`:
   - contains `ForTokenClassification` -> token classification model.
   - contains `ForConditionalGeneration` -> image-text-to-text model.
   - contains `ForCausalLM` -> causal language model.
   - any other architecture family is unsupported by the merger.
6. If `huggingface/generation_config.json` exists, load and preserve it while saving. The preservation behavior is covered by EasyR1's native unit tests: saving with a checkpoint generation config must keep values such as list-valued `eos_token_id`, `max_new_tokens`, and `pad_token_id` instead of replacing them with defaults from the model config.
7. If `lora_adapter/adapter_config.json` exists, merge LoRA into the base model:
   - read `base_model_name_or_path` from the adapter config;
   - load the base model on CPU in bf16 with low-memory loading;
   - build the PEFT LoRA model, load the checkpoint state dict, call `merge_and_unload()`, and save dense Hugging Face weights with safe serialization.
8. If no LoRA adapter config exists, instantiate the target model from config on a meta device, materialize an empty CPU model, and save the merged state dict with `save_pretrained()`.
9. If `--hf_upload_path` is supplied, create or reuse that Hub repository and upload the contents of the `huggingface/` output folder.

## LoRA-specific requirements

A LoRA actor checkpoint must include `lora_adapter/adapter_config.json`. The key `base_model_name_or_path` is required because the merger needs the original base model to materialize full dense weights before applying and unloading the adapter. If it is missing, the merger raises an error before it can produce a dense Hugging Face checkpoint.

Before merging LoRA checkpoints, confirm:

- the base model path or Hub id in `base_model_name_or_path` is reachable from the active environment;
- any required Hugging Face token or mirror endpoint is configured;
- enough CPU memory is available to load the base model plus merged adapter state;
- the output is intended to be dense weights, not a standalone adapter-only export.

## Generation config preservation

EasyR1's saver stores model config and generation config under `actor/huggingface/`. The export path intentionally preserves an existing `generation_config.json` by assigning it to the model before `save_pretrained()`. This matters when decoding settings differ from defaults in `config.json`, especially list-valued EOS ids and custom max-generation settings.

After export, check that `actor/huggingface/generation_config.json` still contains the expected values. A metadata-only check is cheap:

```bash
python - <<'PY'
from transformers import GenerationConfig
cfg = GenerationConfig.from_pretrained("<actor_checkpoint_dir>/huggingface")
print(cfg.to_dict())
PY
```

Avoid loading a large model just to validate metadata unless the environment has enough memory.

## Upload caveats

The optional upload path uses Hugging Face Hub APIs to create the repo if needed and upload the whole `huggingface/` folder. Treat upload as a separate, explicit decision because it may require network access, credentials, and repository visibility review. The distilled EasyR1 behavior creates the repository with `private=False`; use a separate Hub workflow if a private upload is required.

## Minimal validation after export

After a successful merge, verify the output directory without full model loading:

```bash
python - <<'PY'
from transformers import AutoConfig
cfg = AutoConfig.from_pretrained("<actor_checkpoint_dir>/huggingface")
print(cfg.architectures)
PY
```

Then check file presence:

- `config.json` must exist.
- `generation_config.json` should exist if it existed before export.
- one or more model weight files should exist, for example `.safetensors` shards, a `.bin`, or an index JSON.
- tokenizer or processor files should be present for the model family if inference will load from the exported folder.

For full inference validation, use the relevant Transformers auto class for the architecture and only load the model when CPU/GPU memory is adequate.
