# Architecture and Loading Troubleshooting

Use this reference for failures while loading Baichuan-7B model/tokenizer code, constructing local source classes, running tiny synthetic forward checks, or using generation/cache behavior. For environment-wide dependency selection or install recovery, also consult the parent skill's shared troubleshooting reference.

## Quick diagnosis table

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ValueError: Loading ... requires you to execute the configuration file` or custom code is ignored | Missing `trust_remote_code=True` while using Hugging Face `AutoTokenizer` / `AutoModelForCausalLM` | Re-run tokenizer and model loading with `trust_remote_code=True`. Only do this for trusted model sources such as the official Baichuan repo/cache or a vetted local mirror. |
| `OSError` / `Repository Not Found` / missing `tokenizer.model` / missing weight shards | Official weights or tokenizer assets are not local and cannot be downloaded from the current environment | Use a local `model_id_or_path` containing config, tokenizer, model code, and weights; or pre-download/cache `baichuan-inc/Baichuan-7B`. Do not treat the tiny smoke as proof that real weights are installed. |
| `ModuleNotFoundError: No module named 'models'` when using local source | The checkout root is not on `PYTHONPATH` or `--repo-root` points at the wrong directory | Use `python scripts/local_model_smoke.py --repo-root /path/to/Baichuan-7B`, or manually prepend the checkout root to `PYTHONPATH`. The root must contain `models/configuration_baichuan.py` and `models/modeling_baichuan.py`. |
| `ModuleNotFoundError: No module named 'xformers'` | The local modeling file imports `from xformers import ops as xops` at import time | Install a torch-compatible xFormers build, use an environment that already has one, or use the official pinned stack when possible. Even eval-mode tiny forward needs the import to succeed. |
| xFormers or Torch binary mismatch errors | `torch`, CUDA, and `xformers` versions are incompatible | The repo pins `torch==2.0.0` and `xformers==0.0.20`; newer stacks can be usable for smoke checks but are compatibility-sensitive. Rebuild/install matching wheels for the target CUDA/Torch version. |
| CUDA allocation or `.to('cuda:0')` fails | CUDA is unavailable, no visible GPU, insufficient driver/runtime, or no memory | Use CPU only for tiny config smoke; defer full 7B generation until a CUDA-capable environment with enough memory and cached weights is available. Run the helper with `--cuda` only to check a tiny CUDA allocation. |
| `hidden_size must be divisible by num_heads` | `BaiChuanConfig(hidden_size=..., num_attention_heads=...)` is invalid | Choose dimensions where `hidden_size % num_attention_heads == 0`; e.g. `hidden_size=32, num_attention_heads=4` for toy smoke. |
| `Attention mask should be of size ...` | Direct low-level attention call received the wrong 4D mask shape | For normal model calls, pass a 2D tokenizer mask `(batch, seq)` to `BaiChuanForCausalLM` and let the model expand it. If calling `Attention` directly, use `(batch, 1, q_len, kv_seq_len)`. |
| `You cannot specify both decoder_input_ids and decoder_inputs_embeds` | Both `input_ids` and `inputs_embeds` were passed | Pass exactly one. For generation, `inputs_embeds` is only intended for the first non-cached step. |
| `use_cache=True is incompatible with gradient checkpointing` | Training mode with gradient checkpointing tries to use generation cache | This is expected; the model forces `use_cache=False`. For inference/generation checks, use `model.eval()` and do not enable gradient checkpointing. |
| Warning that the model will lose `generate` or should inherit from `GenerationMixin` | Newer Transformers versions changed generation inheritance behavior for custom `PreTrainedModel` classes | The repo was authored around `transformers==4.29.1`. Treat current `generate()` availability as version-sensitive; prefer official/pinned remote-code environments for real generation or update the custom class inheritance in a private fork. |

## Safe isolation steps

1. Separate a config-only smoke from real model loading.
   - Config-only: run the bundled `local_model_smoke.py`; no weights, tokenizer, data, CUDA, or network are required.
   - Real inference: use `AutoTokenizer.from_pretrained(..., trust_remote_code=True)` and `AutoModelForCausalLM.from_pretrained(..., trust_remote_code=True)` with official or local weights.
2. Keep local source imports explicit.
   - The Baichuan-7B checkout is not a pip package with `setup.py`/`pyproject.toml` in this evidence set.
   - The helper adds `--repo-root` to `sys.path`; for notebooks/scripts, do the same deliberately.
3. Prefer eval mode for smoke tests.
   - `model.eval()` exercises the inference attention path.
   - Training mode uses xFormers memory-efficient attention kernels and may require GPU/kernel support that is irrelevant to loading checks.
4. Do not over-interpret CUDA success.
   - A tiny CUDA tensor allocation proves only basic CUDA availability.
   - Full 7B generation also requires enough VRAM/offload, compatible weights, tokenizer files, and a compatible Transformers remote-code stack.

## Generation/cache checks

When generation gives unexpected positions or shapes, inspect the values returned by `prepare_inputs_for_generation`:

```python
prepared = model.prepare_inputs_for_generation(
    input_ids,
    attention_mask=attention_mask,
    use_cache=True,
)
print(prepared.keys())
print(prepared["position_ids"])
```

Expected keys are `input_ids` or `inputs_embeds`, `position_ids`, `past_key_values`, `use_cache`, and `attention_mask`. With `past_key_values`, `input_ids` and `position_ids` should be narrowed to the last token.

## When to route elsewhere

- Dataset paths, MMLU/C-Eval categories, CUDA benchmark scoring, or output JSON/CSV files: route to `evaluation-workflows`.
- `tokenizer.model` placement for pretraining, UTF-8 corpus shards, DeepSpeed JSON, hostfile syntax, checkpoint save paths, or multi-node launch failures: route to `pretraining-and-deepspeed`.
- Cross-cutting install, package pin, and backend issues: use parent [shared troubleshooting](../../../references/troubleshooting.md).

## Cross-links

- Workflow reference: [workflows](workflows.md)
- Local helper: [local_model_smoke.py](../scripts/local_model_smoke.py)
- Parent root skill: [Baichuan-7B root](../../../SKILL.md)
- Shared API reference: [root API reference](../../../references/api-reference.md)
