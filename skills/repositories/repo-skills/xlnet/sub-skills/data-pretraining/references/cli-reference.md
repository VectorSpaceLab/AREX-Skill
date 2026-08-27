# CLI reference

This sub-skill uses the bundled command builder to print shell commands. It does not execute training.

## `data_utils.py` preprocessing flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--input_glob` | Input text or id files. | Matches the corpus shards to preprocess. |
| `--save_dir` | Preprocessing output root. | Creates `corpus_info.json` and `tfrecords/`. |
| `--sp_path` | SentencePiece model path. | Required in both raw-text and id mode. |
| `--from_raw_text` | Parse raw text instead of ids. | `False` means each non-empty line is a whitespace-separated id sequence. |
| `--use_eod` | Insert `<eod>` for blank lines. | Blank lines are document boundaries either way. |
| `--bsz_per_host` | Batch size per host during preprocessing. | Must divide by `num_core_per_host`; if `bi_data=True`, must also divide by `2 * num_core_per_host`. |
| `--num_core_per_host` | Logical core count per host. | `data_utils.py` forces this to `1` when `use_tpu=False`. |
| `--seq_len` | Sequence length. | Must exceed `reuse_len + 3`. |
| `--reuse_len` | Reused prefix length. | Often half of `seq_len`. |
| `--bi_data` | Build bidirectional streams. | Output filename records `bi` or `uni`. |
| `--mask_alpha` / `--mask_beta` | Mask-group sizing. | Part of the filename fingerprint. |
| `--num_predict` | Fixed prediction count. | If set, output filename includes `fnp-<n>`. |
| `--uncased` | Lowercase before tokenization. | Part of the fingerprint. |
| `--split` | `train` / `dev` / `test`. | Used in `record_info-<split>-...` naming. |
| `--task` | Worker index. | Selects `file_paths[task::num_task]`. |
| `--num_task` | Total preprocessing workers. | Keep the same across all workers. |
| `--pass_id` | Repeated pass number. | Changes the random seed and filename prefix. |

## `train_gpu.py` flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--record_info_dir` | Directory or comma-separated list of directories with `record_info*.json`. | Must match the preprocessing fingerprint. |
| `--model_dir` | Training output directory. | Keep separate from `init_checkpoint`. |
| `--init_checkpoint` | Initial checkpoint. | Can point to a pretrained or resumed checkpoint. |
| `--num_hosts` | Number of hosts. | Default `1` for the GPU entrypoint. |
| `--num_core_per_host` | GPUs per host to use. | `train_batch_size` must divide evenly by this value. |
| `--train_batch_size` | Whole GPU training batch. | Split across towers inside `train_gpu.py`. |
| `--train_steps` | Total training steps. | Long-running pretraining usually needs a large value. |
| `--iterations` | Steps per loop. | Controls logging/checkpoint cadence in the loop. |
| `--save_steps` | Checkpoint interval. | Required by the GPU loop because it uses modulo checks. |
| `--num_passes` | Limit passes loaded from each record-info file. | Training-side concept; not the same as preprocessing `pass_id`. |
| `--seq_len` / `--reuse_len` / `--perm_size` | Sequence and permutation layout. | Must be compatible with preprocessing and local permutation constraints. |
| `--mem_len` | Cached memory length. | Matches the XLNet-Large sketch when set to `384`. |
| `--bi_data` | Use bidirectional streams. | Must match preprocessing. |
| `--mask_alpha`, `--mask_beta`, `--num_predict`, `--uncased` | Data fingerprint flags. | Must match preprocessing exactly. |
| `--n_layer`, `--d_model`, `--d_embed`, `--n_head`, `--d_head`, `--d_inner` | XLNet size. | Use the README large-model sketch as a baseline. |
| `--dropout`, `--dropatt`, `--untie_r`, `--summary_type`, `--ff_activation`, `--use_bfloat16` | Runtime/model controls. | Optional but part of the public training contract. |

Note: `train_gpu.py` also defines a `--use_tpu` flag in the source, but the entrypoint still routes through `/gpu:0`; treat TPU execution as a `train.py` concern.

## `train.py` TPU flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--master` | TPU master or local master. | Used when `use_tpu=False`. |
| `--tpu` | Cloud TPU name or grpc address. | Needed for TPU runtime. |
| `--gcp_project` | GCP project id. | Used to resolve TPU cluster access. |
| `--tpu_zone` | TPU zone. | Used with `TPUClusterResolver`. |
| `--use_tpu` | Enable TPU execution. | Default `True`; set `False` only for non-TPU experimentation. |
| `--record_info_dir` | Preprocessed record-info directory or directories. | Must point to the matching `record_info*.json` set. |
| `--model_dir` | TPU training output directory. | Separate from `init_checkpoint`. |
| `--init_checkpoint` | Starting checkpoint. | Optional. |
| `--num_hosts` | Number of TPU hosts. | Part of the total shard count. |
| `--num_core_per_host` | TPU cores per host. | Part of the total shard count. |
| `--train_batch_size` | Global TPU training batch. | Must fit the total host/core count. |
| `--save_steps` | Checkpoint interval. | Forwarded into the TPU `RunConfig`. |
| `--max_save` | Max checkpoints to retain. | `RunConfig.keep_checkpoint_max`. |
| `--seq_len` / `--reuse_len` / `--perm_size` | Pretraining geometry. | `train.py` asserts `seq_len > 0` and `perm_size > 0`. |
| `--num_passes` | Limit passes loaded from each record-info file. | Same meaning as GPU training. |
| `--track_mean` | Track mean loss on TPU. | Useful for monitoring. |
| `--use_bfloat16` | Use bfloat16 math. | Common on TPU. |

## Compatibility checks

The bundled builder should reject or warn about these mismatches:

- `perm_size > reuse_len`
- `perm_size > seq_len - reuse_len`
- `reuse_len >= seq_len - 3`
- `train_batch_size % num_core_per_host != 0` for GPU training
- `bsz_per_host % num_core_per_host != 0` for preprocessing
- `bi_data=True` with `bsz_per_host % (2 * num_core_per_host) != 0`
- empty `input_glob`
- mismatched `record_info` fingerprint flags between preprocessing and training
