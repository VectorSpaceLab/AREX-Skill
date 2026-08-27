# Troubleshooting Training And Checkpoints

Use this matrix to triage TurboDiffusion rCM/SLA training setup, checkpoint conversion, merge, safetensors conversion, and quantized export failures.

## Failure matrix

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `model.config.teacher_ckpt` points to a `.pth` file and training fails to load it | FSDP training expects a DCP directory | Convert teacher `.pth` to DCP with PyTorch DCP `torch_to_dcp`, then update the override to the DCP directory. |
| DCP-to-PTH conversion cannot find metadata or state | Passed a parent output directory or `.pth` file instead of the specific DCP checkpoint directory | Point `--dcp_checkpoint_dir` at the saved DCP model directory for one iteration. Inspect directory contents before converting. |
| Converted `.pth` has no expected keys | DCP checkpoint did not use `net_ema.` keys or the wrong checkpoint component was selected | Inspect the DCP key list. The public converter only keeps `net_ema.*` and rewrites it to `net.*`. |
| `No files found with pattern '<...>/shard*.tar'` | Dataset root or glob is wrong; shell expanded or did not quote the glob; shards are missing | Quote the glob in shell commands, validate with `glob.glob`, and check for tar files under the dataset root. |
| Tar shards exist but dataloader keys are missing | Shards do not contain `.latent.pt`, `.embed.pt`, and `.prompt.txt` members grouped by sample prefix | Inspect tar member names. Regenerate/repair shards only after expensive dataset-generation approval. |
| `No module named hydra`, `megatron`, `webdataset`, `transformer_engine`, or `wandb` | Training extras are not installed in the active environment | Install the training extras in the user's prepared environment, then rerun only help/dry-run first. |
| `No module named rcm`, `imaginaire`, `SLA`, `ops`, `scripts`, or `modify_model` | Source-layout top-level imports are not on `PYTHONPATH` | Prefix source-layout commands with `PYTHONPATH=<package-source-dir>` and rerun a help or dry-run command. |
| WANDB login/API error at training start | Wandb callback enabled without credentials or offline policy | Decide one of: authenticated online logging, `WANDB_MODE=offline`, or config/callback override. Do not write API keys into generated commands. |
| Training debug request still asks for data/checkpoints | `_debug` experiments reduce iteration counts but do not remove model/data dependencies for real training | Use `--dryrun` for config composition only. For real debug training, require DCP teacher, VAE, text encoder, negative embedding, data shards, GPU, extras, and WANDB/offline policy. |
| `Unknown model name` in export | Invalid `--model` value | Use one of `Wan2.1-1.3B`, `Wan2.1-14B`, or `Wan2.2-A14B`. |
| Export state-dict shape mismatches | Model name does not match checkpoint family/scale, high/low I2V branch swapped, or checkpoint is not in rCM/SLA format | Re-check checkpoint provenance, model scale, T2V/I2V family, and `state_dict`/`net.` prefix expectations. |
| `attention_type=sagesla` import/assertion failure | SageSLA requires the optional SpargeAttn/SageSLA backend | Route backend installation/check to `acceleration-backends` or use `attention_type=sla` if plain SLA is acceptable. |
| Quantized export fails in CUDA/custom op code | `--quant_linear` requires CUDA, compiled custom ops, and compatible PyTorch/CUDA stack | Route to `acceleration-backends` after verifying input paths and model name. |
| Later inference fails after quantized export | Inference/serving command omitted `--quant_linear` or used an unquantized checkpoint with `--quant_linear` | Align the inference flag with the checkpoint export type. Route command construction to `video-inference` or `interactive-serving`. |
| Merge prints shape/key warnings but saves output | Source merge utility treats mismatches as warnings and keeps base tensors or target-only keys | Do not accept the merge blindly. Inspect key coverage and decide whether mismatches are expected before using output. |
| Safetensors converter reports missing index or `weight_map` | Model directory is not a sharded diffusers-style checkpoint directory | Point `--model_dir` at the directory containing `diffusion_pytorch_model.safetensors.index.json` and all referenced shards. |
| Safetensors converter fails on shard/tensor lookup | Index references missing files or parameter names absent from shard | Validate every shard listed in `weight_map` exists and can be opened before conversion. |
| Output save fails for conversion/export | Output parent directory does not exist or file permissions are wrong | Create a new output directory explicitly; avoid overwriting source checkpoints. |

## DCP versus PTH decision tree

1. User wants to **train** with a pretrained Wan teacher: ensure teacher is DCP. If only `.pth` exists, render a `.pth` to DCP conversion command.
2. User has **training output** and wants to merge/export/infer: convert the saved DCP model directory back to `.pth` first.
3. User has **sharded safetensors**: convert to `.pth`, choose whether to prefix keys with `net.`, then continue with merge/export validation.
4. User has an **inference checkpoint** already modified/quantized: do not run training utilities; route generation/serving to the inference sub-skills.

## Difficult case: mismatched merge keys

When a merge has mismatched keys or shapes:

1. Preserve all original checkpoint files; write the merge to a new output path only.
2. Count keys in `base`, `diff_base`, `diff_target`, and `merged`.
3. Count keys that used the formula, keys kept from base due to missing/mismatch, and target-only keys.
4. Treat mismatches in architecture-specific projection or patch-embedding keys as a model-family warning, not a routine success.
5. If mismatch coverage is substantial or unexplained, stop and ask which checkpoint should be considered authoritative.

The tiny helper only proves arithmetic semantics; it does not validate real checkpoint compatibility.

## Difficult case: SLA debug training request with missing prerequisites

If the user asks for an SLA debug training run but has not supplied DCP conversion, WANDB/offline policy, or data shards:

- Provide a `--dryrun` command only.
- Explain that `_debug` changes iterations/logging but real training still instantiates model/data/logging components.
- Ask for or list these missing items: teacher DCP path, VAE path, text encoder path, negative embedding path, dataset shard glob, output root, GPU/process count, training extras, and WANDB policy.
- Do not silently switch to real training or dataset synthesis.

## `--default_norm` naming pitfall

The export script flag is named `--default_norm`. In the implementation, passing it keeps default LayerNorm/RMSNorm modules; omitting it allows FastNorm replacement. When a user says "use default norms," include `--default_norm`. When a user wants the faster default TurboDiffusion export path, omit it.

## WANDB and credentials policy

- Never put `WANDB_API_KEY` values in generated commands, logs, or runtime skill text.
- If credentials are already configured in the user's shell, a real training command can rely on the environment.
- For debug/local experiments, `WANDB_MODE=offline` may be appropriate if the training stack supports it in the user's setup.
- If WANDB callbacks should be disabled, use an explicit config override only after confirming the desired logging behavior.

## Preflight snippets

Check a dataset glob without loading tensors:

```bash
python - <<'PY'
import glob
pattern = '<dataset-root>/shard*.tar'
paths = sorted(glob.glob(pattern))
print('matched_shards', len(paths))
print('\n'.join(paths[:5]))
PY
```

Check a `.pth` state-dict key prefix summary on CPU:

```bash
python - <<'PY'
import torch
path = '<checkpoint.pth>'
try:
    obj = torch.load(path, map_location='cpu', weights_only=False)
except TypeError:
    obj = torch.load(path, map_location='cpu')
sd = obj.get('state_dict', obj) if isinstance(obj, dict) else obj
keys = list(sd.keys()) if isinstance(sd, dict) else []
print('num_keys', len(keys))
print('first_keys', keys[:10])
print('net_prefix', sum(k.startswith('net.') for k in keys))
print('net_ema_prefix', sum(k.startswith('net_ema.') for k in keys))
PY
```

Run the safe merge arithmetic fixture:

```bash
python <skill-root>/sub-skills/training-and-checkpoints/scripts/tiny_merge_models_check.py --verbose
```
