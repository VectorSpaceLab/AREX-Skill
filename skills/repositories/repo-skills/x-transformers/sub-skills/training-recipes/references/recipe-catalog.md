# x-transformers training recipe catalog

This reference summarizes the repository training recipes and the safe adaptation policy for downstream work. Use script names as evidence labels only; do not import native training files into tests, because several start long training loops at import time.

## Safe default

Use `scripts/copy_task_smoke.py` for the default smoke path. It builds a tiny `XTransformer`, trains on a synthetic copy task for 1-3 CPU-safe steps, then calls `generate` for a short sample. A high mismatch count is acceptable for this smoke because it checks API/runtime wiring, not convergence.

A native recipe should only be run when all of these are true:

- its extra packages are installed;
- its dataset or synthetic generator is intentionally available;
- logging side effects are disabled or accepted;
- sequence length, batch size, and step/epoch counts are explicitly reduced;
- GPU use is intentional when the script hard-codes `.cuda()`.

## Dataset and provenance notes

The enwik8 recipes expect a compressed byte file named `data/enwik8.gz` in the current working directory. The repository data note says enwik8 was downloaded from the Hutter Prize page (`http://prize.hutter1.net/`). The scripts read the first 95,000,000 bytes from the gzip file and split the first 90,000,000 bytes for training with the remainder for validation. The skill does not bundle this dataset.

Because the enwik8 loops use large defaults (`num_batches` commonly `1e5`, `seq_len` 256-2048, generation during step 0 in many scripts), treat them as documentation-only unless you have deliberately prepared the data and runtime budget.

## Dependency variants

| Dependency group | Packages / imports | Where it appears | Notes |
|---|---|---|---|
| Base runtime | `torch`, `x_transformers` | all recipes | Required for any model run. The bundled smoke uses only this group. |
| Numeric / data | `numpy`, Python `gzip` | enwik8 recipes | `numpy` is required to map gzip bytes into tensors. |
| Progress / CLI | `tqdm`, `fire` | most recipes, Fire CLIs | `fire` is not needed by hard-coded top-level scripts but is needed by CLI recipes. |
| Distributed / device | `accelerate` | length extrapolation, enwik8 Fire recipes, path-star, self-masked | Required even for `--cpu=True` if the script imports `Accelerator`. |
| Logging | `wandb` | enwik8 Fire recipes, path-star, LEJEPA, XL | Disable online logging where supported; for path-star set `WANDB_MODE=disabled` because the script initializes W&B unconditionally. |
| Optimizer extras | `lion_pytorch`, `adam_atan2_pytorch` | parity, Muon recipe | `pyproject.toml` `examples` extra covers `lion-pytorch`, `adam-atan2-pytorch`, and `tqdm`. |
| EMA / MLP extras | `ema_pytorch`, `x_mlps_pytorch` | self-masked representation recipe | Required before even importing the script. |
| Flash attention | `flash_attn` | optional `flash-pack-seq` extra | Not required by the cataloged smoke path. Install only when adapting features that request flash attention or packed sequences. |
| Tests | `pytest` | `pyproject.toml` `test` extra | Useful for repository tests, not needed for training recipes. |

The safe smoke path only needs the base runtime. Re-probe your active environment before running native recipes, because the longer scripts depend on extras such as Accelerate, Fire, W&B, tqdm, optimizer packages, and self-distillation helpers.

## Script-by-script catalog

| Script | Recipe purpose | CLI / run style | Required extras beyond base | Data expectation | Run-safety decision |
|---|---|---|---|---|---|
| `train_copy.py` | Encoder-decoder copy task using `XTransformer`; synthetic batches with a prefix token and source mask. | Hard-coded top-level loop; no Fire CLI. | `tqdm` in the native file; bundled smoke removes this requirement. | Synthetic only. | **Safest adaptation target.** Native defaults are still long (`1e5` batches), so use the bundled smoke or manually shrink constants. |
| `train_parity.py` | Binary parity curriculum with a decoder, token shift, optional GRU hybrid recurrence, and Lion optimizer. | Hard-coded top-level loop that increments train length until a threshold is met. | `tqdm`, `lion_pytorch`; CUDA is hard-coded. | Synthetic parity sequences. | Reference-only by default. It can run a long curriculum, requires GPU edits or CUDA availability, and needs the Lion extra. |
| `train_length_extrapolate.py` | Enwik8 decoder trained at 256 tokens and validated at longer lengths with polar positional embedding. | Hard-coded top-level loop. | `accelerate`, `tqdm`, `numpy`. | `data/enwik8.gz`. | Reference-only. Data-bound, long-running, and validates 256-4096 token lengths. |
| `train_free.py` | Enwik8 `FreeTransformer` latent recipe with autoregressive and KL losses. | Hard-coded top-level loop. | `tqdm`, `numpy`; CUDA is hard-coded. | `data/enwik8.gz`. | Reference-only. Large model, long defaults, GPU-only as written. |
| `train_belief_state.py` | Enwik8 `BeliefStateWrapper` with forward/backward suffix conditioning generation. | Hard-coded top-level loop. | `tqdm`, `numpy`; CUDA is hard-coded. | `data/enwik8.gz`. | Reference-only. Long, data-bound, GPU-only as written, and wrapper-specific behavior belongs elsewhere. |
| `train_enwik8.py` | Baseline GPT-like autoregressive enwik8 training with W&B and Accelerate. | Fire CLI: `python train_enwik8.py --num_batches=... --batch_size=... --seq_len=... --cpu=True`. | `fire`, `wandb`, `accelerate`, `tqdm`, `numpy`. | `data/enwik8.gz`. | Documentation-only unless data/extras are prepared. Even tiny runs validate and generate at step 0 because modulo checks include `i == 0`. |
| `train_enwik8_xm.py` | Enwik8 XMLatentDecoder recipe with candidate latents and latent KL diagnostic. | Fire CLI with `--candidates`, `--num_latents`, `--cpu`, and batch/length controls. | `fire`, `wandb`, `accelerate`, `tqdm`, `numpy`. | `data/enwik8.gz`. | Documentation-only. Adds latent-specific overhead and logging to the baseline enwik8 cost. |
| `train_enwik8_lejepa_style.py` | Enwik8 latent autoregressive / LEJEPA-style losses with several rollout and predictor controls. | Fire CLI with `--cpu`, loss weights, rollout, batch/length controls. | `fire`, `wandb`, `accelerate`, `tqdm`, `numpy`. | `data/enwik8.gz`. | Documentation-only. Heavy model, W&B side effects, data requirement, and experimental loss controls. |
| `train_entropy_tokenizer.py` | Enwik8 entropy-based tokenization probe around an autoregressive model. | Fire CLI with `--entropy_threshold`, `--accumulate_entropy`, `--ignore_entropy_below`, `--cpu`. | `fire`, `accelerate`, `tqdm`, `numpy`. | `data/enwik8.gz`. | Documentation-only. Useful for tokenizer behavior notes, but still data-bound and long by default. |
| `train_gpt_vae.py` | Enwik8 `GPTVAE` recipe with positive and negative latent generation. | Hard-coded top-level loop. | `tqdm`, `numpy`; CUDA is hard-coded. | `data/enwik8.gz`. | Reference-only. VAE-specific, long, GPU-only as written. |
| `train_path_star.py` | Synthetic graph path-finding sequence dataset with optional `NextLatentWrapper`. | Fire CLI with dataset, model, and next-latent options. | `fire`, `wandb`, `accelerate`, `tqdm`. | Synthetic `PathStarDataset`. | Useful synthetic evidence, but not a safe default native run: default `num_train=20000`, `epochs=25`, W&B initialization, and wrapper-specific training. |
| `train_self_masked_repr.py` | Enwik8 self-masked representation / self-distillation recipe with EMA teacher and optional reverse-KL mode. | Fire CLI with SSL, mask, teacher/student, and recurrent-block controls. | `fire`, `accelerate`, `tqdm`, `numpy`, `ema_pytorch`, `x_mlps_pytorch`. | `data/enwik8.gz`. | Documentation-only. Large in-file training wrappers, extra packages, long defaults, and enwik8 dependency. |
| `train_with_muon.py` | Enwik8 decoder trained with `MuonAdamAtan2` and `model.muon_parameters()`. | Hard-coded top-level loop. | `adam_atan2_pytorch`, `tqdm`, `numpy`; CUDA is hard-coded. | `data/enwik8.gz`. | Reference-only. Requires optimizer extra, data, and GPU as written. |
| `train_xl_enwik8.py` | Transformer-XL-style enwik8 recipe using memory, TBPTT, and optional end-to-end TTT target loss. | Fire CLI with `--seq_len`, `--train_seq_len`, `--tbptt_steps`, `--e2e_ttt`, `--cpu`. | `fire`, `wandb`, `accelerate`, `tqdm`, `numpy`. | `data/enwik8.gz`. | Documentation-only. Long-context memory makes it memory-sensitive; W&B and data prerequisites remain. |

## Practical CLI patterns

### Bundled smoke

```bash
python scripts/copy_task_smoke.py --steps 1 --device cpu
python scripts/copy_task_smoke.py --help
```

Use this when you only need to prove that installed `torch` and `x_transformers` can execute a tiny training/generation loop.

### Fire-based enwik8 scripts

If you intentionally run a Fire recipe, shrink it aggressively and keep logging offline/disabled:

```bash
WANDB_MODE=disabled python train_enwik8.py \
  --num_batches=1 \
  --batch_size=1 \
  --gradient_accumulate_every=1 \
  --seq_len=32 \
  --generate_length=8 \
  --cpu=True \
  --track_experiment_online=False
```

This still needs `data/enwik8.gz` and the Fire/Accelerate/W&B/TQDM/Numpy extras, and it will validate/generate on step 0.

### Synthetic path-star script

For deliberate experimentation only:

```bash
WANDB_MODE=disabled python train_path_star.py \
  --num_train=16 \
  --num_val=4 \
  --epochs=1 \
  --batch_size=2 \
  --dim=32 \
  --depth=1 \
  --heads=2 \
  --use_nextlat=False
```

This avoids enwik8 but still imports W&B and Accelerate and uses a wrapper path owned by the sequence-workflow sub-skill.

## Adaptation rules

- Prefer copying the data-generation idea, not the native script body. Native top-level scripts are not library-safe.
- Replace `.cuda()` with an explicit device argument before running on CPU or mixed hardware.
- Reduce `num_batches`, `epochs`, `seq_len`, `train_seq_len`, `batch_size`, and `gradient_accumulate_every` before first execution.
- Set `WANDB_MODE=disabled` and pass recipe-specific offline flags before running anything that imports W&B.
- Keep enwik8 data acquisition separate from smoke tests; missing `data/enwik8.gz` is expected in lightweight environments.
- Do not use `flash-pack-seq` or `flash_attn` as a default fix. They are optional acceleration features, not prerequisites for the safe copy smoke.
