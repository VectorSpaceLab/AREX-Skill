#!/usr/bin/env python3
"""Generate XLNet pretraining commands without executing them.

This helper prints shell commands for:

- `data_utils.py` preprocessing
- `train_gpu.py` GPU pretraining
- `train.py` TPU pretraining

It only formats commands and performs compatibility checks.
"""

from __future__ import annotations

import argparse
import shlex
import sys


PREPROCESS_DEFAULTS = {
    "bsz_per_host": 32,
    "num_core_per_host": 16,
    "seq_len": 512,
    "reuse_len": 256,
    "bi_data": True,
    "mask_alpha": 6,
    "mask_beta": 1,
    "num_predict": 85,
    "uncased": True,
    "use_eod": True,
    "from_raw_text": True,
    "use_tpu": True,
    "split": "train",
    "task": 0,
    "num_task": 1,
    "pass_id": 0,
}

GPU_DEFAULTS = {
    "num_core_per_host": 8,
    "train_batch_size": 16,
    "num_passes": 1,
    "learning_rate": 1e-4,
    "clip": 1.0,
    "min_lr_ratio": 0.001,
    "warmup_steps": 0,
    "adam_epsilon": 1e-8,
    "decay_method": "poly",
    "weight_decay": 0.0,
    "train_steps": 100000,
    "iterations": 1000,
    "save_steps": 1000,
    "seq_len": 512,
    "reuse_len": 256,
    "bi_data": True,
    "mask_alpha": 6,
    "mask_beta": 1,
    "num_predict": 85,
    "uncased": True,
    "perm_size": 256,
    "mem_len": 384,
    "same_length": False,
    "clamp_len": -1,
    "n_layer": 6,
    "d_model": 32,
    "d_embed": 32,
    "n_head": 4,
    "d_head": 8,
    "d_inner": 32,
    "dropout": 0.0,
    "dropatt": 0.0,
    "untie_r": True,
    "summary_type": "last",
    "ff_activation": "relu",
    "use_bfloat16": False,
    "init": "normal",
    "init_std": 0.02,
    "init_range": 0.1,
}

TPU_DEFAULTS = {
    "num_hosts": 1,
    "num_core_per_host": 8,
    "train_batch_size": 2048,
    "num_passes": 1,
    "learning_rate": 1e-4,
    "clip": 1.0,
    "min_lr_ratio": 0.001,
    "warmup_steps": 0,
    "adam_epsilon": 1e-8,
    "decay_method": "poly",
    "weight_decay": 0.0,
    "train_steps": 100000,
    "iterations": 1000,
    "save_steps": 1000,
    "max_save": 100000,
    "seq_len": 512,
    "reuse_len": 256,
    "bi_data": True,
    "mask_alpha": 6,
    "mask_beta": 1,
    "num_predict": 85,
    "uncased": True,
    "perm_size": 256,
    "mem_len": 384,
    "same_length": False,
    "clamp_len": -1,
    "n_layer": 24,
    "d_model": 1024,
    "d_embed": 1024,
    "n_head": 16,
    "d_head": 64,
    "d_inner": 4096,
    "dropout": 0.0,
    "dropatt": 0.0,
    "untie_r": True,
    "summary_type": "last",
    "ff_activation": "relu",
    "use_bfloat16": False,
    "track_mean": False,
    "init": "normal",
    "init_std": 0.02,
    "init_range": 0.1,
    "use_tpu": True,
}


def shell_join(parts):
  return " \\\n  ".join(shlex.quote(str(part)) for part in parts)


def emit_flag(name, value):
  if value is None:
    return None
  if isinstance(value, bool):
    return f"--{name}={'True' if value else 'False'}"
  return f"--{name}={value}"


def extend_flags(parts, items):
  for name, value in items:
    token = emit_flag(name, value)
    if token is not None:
      parts.append(token)
  return parts


def add_bool_pair(parser, dest, *, default, on_flag, off_flag, on_help, off_help):
  group = parser.add_mutually_exclusive_group()
  group.add_argument(on_flag, dest=dest, action="store_true", help=on_help)
  group.add_argument(off_flag, dest=dest, action="store_false", help=off_help)
  parser.set_defaults(**{dest: default})


def add_shared_text_flags(parser, *, defaults):
  parser.add_argument(
      "--seq-len", type=int, default=defaults["seq_len"],
      help="Sequence length used by preprocessing and training.")
  parser.add_argument(
      "--reuse-len", type=int, default=defaults["reuse_len"],
      help="Length of the reused prefix inside each sequence.")
  add_bool_pair(
      parser, "bi_data", default=defaults["bi_data"],
      on_flag="--bi-data", off_flag="--uni-data",
      on_help="Build bidirectional streams.",
      off_help="Build unidirectional streams.")
  parser.add_argument(
      "--mask-alpha", type=int, default=defaults["mask_alpha"],
      help="How many tokens form a masking group.")
  parser.add_argument(
      "--mask-beta", type=int, default=defaults["mask_beta"],
      help="How many tokens to mask within each group.")
  parser.add_argument(
      "--num-predict", type=int, default=defaults["num_predict"],
      help="Fixed number of prediction targets.")
  add_bool_pair(
      parser, "uncased", default=defaults["uncased"],
      on_flag="--uncased", off_flag="--cased",
      on_help="Lowercase before SentencePiece encoding.",
      off_help="Preserve case before SentencePiece encoding.")


def check_layout(parser, seq_len, reuse_len, perm_size=None):
  if seq_len <= 0:
    parser.error("--seq-len must be > 0")
  if reuse_len < 0:
    parser.error("--reuse-len must be >= 0")
  if reuse_len >= seq_len - 3:
    parser.error("--reuse-len must be smaller than seq-len - 3")
  if perm_size is not None:
    if perm_size <= 0:
      parser.error("--perm-size must be > 0")
    if perm_size > reuse_len:
      parser.error("--perm-size must be <= reuse-len")
    if perm_size > seq_len - reuse_len:
      parser.error("--perm-size must be <= seq-len - reuse-len")


def build_preprocess_command(args, parser):
  if not args.input_glob:
    parser.error("--input-glob is required")
  if not args.save_dir:
    parser.error("--save-dir is required")
  if not args.sp_path:
    parser.error("--sp-path is required")
  if args.num_task <= 0:
    parser.error("--num-task must be > 0")
  if args.task < 0 or args.task >= args.num_task:
    parser.error("--task must satisfy 0 <= task < num-task")
  if args.pass_id < 0:
    parser.error("--pass-id must be >= 0")
  if args.bsz_per_host <= 0:
    parser.error("--bsz-per-host must be > 0")
  if args.num_core_per_host <= 0:
    parser.error("--num-core-per-host must be > 0")
  effective_num_core = 1 if not args.use_tpu else args.num_core_per_host
  if args.bsz_per_host % effective_num_core != 0:
    parser.error("--bsz-per-host must be divisible by the effective core count")
  if args.bi_data and args.bsz_per_host % (2 * effective_num_core) != 0:
    parser.error(
        "--bsz-per-host must be divisible by 2 * the effective core count when --bi-data is enabled")
  check_layout(parser, args.seq_len, args.reuse_len)

  parts = [args.python_bin, "data_utils.py"]
  extend_flags(parts, [
      ("bsz_per_host", args.bsz_per_host),
      ("num_core_per_host", effective_num_core),
      ("seq_len", args.seq_len),
      ("reuse_len", args.reuse_len),
      ("input_glob", args.input_glob),
      ("save_dir", args.save_dir),
      ("split", args.split),
      ("task", args.task),
      ("num_task", args.num_task),
      ("pass_id", args.pass_id),
      ("sp_path", args.sp_path),
      ("mask_alpha", args.mask_alpha),
      ("mask_beta", args.mask_beta),
      ("num_predict", args.num_predict),
      ("use_eod", args.use_eod),
      ("from_raw_text", args.from_raw_text),
      ("use_tpu", args.use_tpu),
      ("bi_data", args.bi_data),
      ("uncased", args.uncased),
  ])
  return shell_join(parts)


def build_gpu_command(args, parser):
  if not args.record_info_dir:
    parser.error("--record-info-dir is required")
  if not args.model_dir:
    parser.error("--model-dir is required")
  if args.num_hosts <= 0:
    parser.error("--num-hosts must be > 0")
  if args.train_batch_size <= 0:
    parser.error("--train-batch-size must be > 0")
  if args.num_core_per_host <= 0:
    parser.error("--num-core-per-host must be > 0")
  if args.train_batch_size % args.num_core_per_host != 0:
    parser.error("--train-batch-size must be divisible by --num-core-per-host")
  if args.save_steps is None or args.save_steps <= 0:
    parser.error("--save-steps is required and must be > 0 for GPU training")
  if args.num_passes <= 0:
    parser.error("--num-passes must be > 0")
  check_layout(parser, args.seq_len, args.reuse_len, args.perm_size)

  parts = [args.python_bin, "train_gpu.py"]
  extend_flags(parts, [
      ("num_hosts", args.num_hosts),
      ("num_core_per_host", args.num_core_per_host),
      ("record_info_dir", args.record_info_dir),
      ("model_dir", args.model_dir),
      ("init_checkpoint", args.init_checkpoint),
      ("num_passes", args.num_passes),
      ("learning_rate", args.learning_rate),
      ("clip", args.clip),
      ("min_lr_ratio", args.min_lr_ratio),
      ("warmup_steps", args.warmup_steps),
      ("adam_epsilon", args.adam_epsilon),
      ("decay_method", args.decay_method),
      ("weight_decay", args.weight_decay),
      ("train_batch_size", args.train_batch_size),
      ("train_steps", args.train_steps),
      ("iterations", args.iterations),
      ("save_steps", args.save_steps),
      ("seq_len", args.seq_len),
      ("reuse_len", args.reuse_len),
      ("bi_data", args.bi_data),
      ("mask_alpha", args.mask_alpha),
      ("mask_beta", args.mask_beta),
      ("num_predict", args.num_predict),
      ("perm_size", args.perm_size),
      ("uncased", args.uncased),
      ("mem_len", args.mem_len),
      ("same_length", args.same_length),
      ("clamp_len", args.clamp_len),
      ("n_layer", args.n_layer),
      ("d_model", args.d_model),
      ("d_embed", args.d_embed),
      ("n_head", args.n_head),
      ("d_head", args.d_head),
      ("d_inner", args.d_inner),
      ("dropout", args.dropout),
      ("dropatt", args.dropatt),
      ("untie_r", args.untie_r),
      ("summary_type", args.summary_type),
      ("ff_activation", args.ff_activation),
      ("use_bfloat16", args.use_bfloat16),
      ("init", args.init),
      ("init_std", args.init_std),
      ("init_range", args.init_range),
  ])
  return shell_join(parts)


def build_tpu_command(args, parser):
  if not args.record_info_dir:
    parser.error("--record-info-dir is required")
  if not args.model_dir:
    parser.error("--model-dir is required")
  if args.train_batch_size <= 0:
    parser.error("--train-batch-size must be > 0")
  if args.num_hosts <= 0:
    parser.error("--num-hosts must be > 0")
  if args.num_core_per_host <= 0:
    parser.error("--num-core-per-host must be > 0")
  if args.train_batch_size % (args.num_hosts * args.num_core_per_host) != 0:
    parser.error(
        "--train-batch-size must be divisible by num-hosts * num-core-per-host")
  if args.save_steps is None or args.save_steps <= 0:
    parser.error("--save-steps is required and must be > 0 for TPU training")
  if args.max_save is not None and args.max_save <= 0:
    parser.error("--max-save must be > 0 when supplied")
  if args.num_passes <= 0:
    parser.error("--num-passes must be > 0")
  check_layout(parser, args.seq_len, args.reuse_len, args.perm_size)

  parts = [args.python_bin, "train.py"]
  extend_flags(parts, [
      ("master", args.master),
      ("tpu", args.tpu),
      ("gcp_project", args.gcp_project),
      ("tpu_zone", args.tpu_zone),
      ("use_tpu", args.use_tpu),
      ("num_hosts", args.num_hosts),
      ("num_core_per_host", args.num_core_per_host),
      ("record_info_dir", args.record_info_dir),
      ("model_dir", args.model_dir),
      ("init_checkpoint", args.init_checkpoint),
      ("num_passes", args.num_passes),
      ("learning_rate", args.learning_rate),
      ("clip", args.clip),
      ("min_lr_ratio", args.min_lr_ratio),
      ("warmup_steps", args.warmup_steps),
      ("adam_epsilon", args.adam_epsilon),
      ("decay_method", args.decay_method),
      ("weight_decay", args.weight_decay),
      ("train_batch_size", args.train_batch_size),
      ("train_steps", args.train_steps),
      ("iterations", args.iterations),
      ("save_steps", args.save_steps),
      ("max_save", args.max_save),
      ("seq_len", args.seq_len),
      ("reuse_len", args.reuse_len),
      ("bi_data", args.bi_data),
      ("mask_alpha", args.mask_alpha),
      ("mask_beta", args.mask_beta),
      ("num_predict", args.num_predict),
      ("perm_size", args.perm_size),
      ("uncased", args.uncased),
      ("mem_len", args.mem_len),
      ("same_length", args.same_length),
      ("clamp_len", args.clamp_len),
      ("n_layer", args.n_layer),
      ("d_model", args.d_model),
      ("d_embed", args.d_embed),
      ("n_head", args.n_head),
      ("d_head", args.d_head),
      ("d_inner", args.d_inner),
      ("dropout", args.dropout),
      ("dropatt", args.dropatt),
      ("untie_r", args.untie_r),
      ("summary_type", args.summary_type),
      ("ff_activation", args.ff_activation),
      ("use_bfloat16", args.use_bfloat16),
      ("track_mean", args.track_mean),
      ("init", args.init),
      ("init_std", args.init_std),
      ("init_range", args.init_range),
  ])
  return shell_join(parts)


def add_shared_optimization_flags(parser, *, defaults):
  parser.add_argument("--learning-rate", type=float, default=defaults["learning_rate"],
                      help="Maximum learning rate.")
  parser.add_argument("--clip", type=float, default=defaults["clip"],
                      help="Gradient clipping value.")
  parser.add_argument("--min-lr-ratio", type=float, default=defaults["min_lr_ratio"],
                      help="Minimum ratio for cosine or polynomial decay.")
  parser.add_argument("--warmup-steps", type=int, default=defaults["warmup_steps"],
                      help="Number of linear warmup steps.")
  parser.add_argument("--adam-epsilon", type=float, default=defaults["adam_epsilon"],
                      help="Adam epsilon.")
  parser.add_argument("--decay-method", choices=["poly", "cos"],
                      default=defaults["decay_method"], help="Learning-rate decay schedule.")
  parser.add_argument("--weight-decay", type=float, default=defaults["weight_decay"],
                      help="Weight decay strength.")


def add_shared_model_flags(parser, *, defaults):
  parser.add_argument("--perm-size", type=int, default=defaults["perm_size"],
                      help="Permutation window size used during training.")
  parser.add_argument("--mem-len", type=int, default=defaults["mem_len"],
                      help="Cached memory length.")
  add_bool_pair(
      parser, "same_length", default=defaults["same_length"],
      on_flag="--same-length", off_flag="--no-same-length",
      on_help="Use same-length attention.",
      off_help="Disable same-length attention.")
  parser.add_argument("--clamp-len", type=int, default=defaults["clamp_len"],
                      help="Clamp relative position length.")
  parser.add_argument("--n-layer", type=int, default=defaults["n_layer"],
                      help="Number of transformer layers.")
  parser.add_argument("--d-model", type=int, default=defaults["d_model"],
                      help="Hidden size of the model.")
  parser.add_argument("--d-embed", type=int, default=defaults["d_embed"],
                      help="Embedding dimension.")
  parser.add_argument("--n-head", type=int, default=defaults["n_head"],
                      help="Attention head count.")
  parser.add_argument("--d-head", type=int, default=defaults["d_head"],
                      help="Attention head dimension.")
  parser.add_argument("--d-inner", type=int, default=defaults["d_inner"],
                      help="Feed-forward hidden size.")
  parser.add_argument("--dropout", type=float, default=defaults["dropout"],
                      help="Dropout rate.")
  parser.add_argument("--dropatt", type=float, default=defaults["dropatt"],
                      help="Attention dropout rate.")
  add_bool_pair(
      parser, "untie_r", default=defaults["untie_r"],
      on_flag="--untie-r", off_flag="--tie-r",
      on_help="Untie the relative position biases.",
      off_help="Tie the relative position biases.")
  parser.add_argument("--summary-type", default=defaults["summary_type"],
                      help="Sequence summarization strategy.")
  parser.add_argument("--ff-activation", default=defaults["ff_activation"],
                      help="Feed-forward activation type.")
  add_bool_pair(
      parser, "use_bfloat16", default=defaults["use_bfloat16"],
      on_flag="--use-bfloat16", off_flag="--no-bfloat16",
      on_help="Use bfloat16 math.",
      off_help="Use float32 math.")
  parser.add_argument("--init", choices=["normal", "uniform"],
                      default=defaults["init"],
                      help="Parameter initialization method.")
  parser.add_argument("--init-std", type=float, default=defaults["init_std"],
                      help="Stddev for normal initialization.")
  parser.add_argument("--init-range", type=float, default=defaults["init_range"],
                      help="Range for uniform initialization.")


def add_training_data_flags(parser, *, defaults):
  add_shared_text_flags(parser, defaults=defaults)
  parser.add_argument("--num-passes", type=int, default=defaults["num_passes"],
                      help="Number of passes to load from each record-info file.")


def build_parser():
  parser = argparse.ArgumentParser(
      description="Generate XLNet pretraining commands for preprocessing, GPU training, or TPU training.",
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      "--python-bin", default="python",
      help="Python executable to place at the start of the generated command.")

  subparsers = parser.add_subparsers(dest="mode", required=True)

  preprocess = subparsers.add_parser(
      "preprocess", help="Generate a data_utils.py preprocessing command.",
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  preprocess.add_argument("--input-glob", required=True, help="Input corpus glob.")
  preprocess.add_argument("--save-dir", required=True, help="Preprocessing output directory.")
  preprocess.add_argument("--sp-path", required=True, help="SentencePiece model path.")
  preprocess.add_argument("--bsz-per-host", type=int, default=PREPROCESS_DEFAULTS["bsz_per_host"],
                          help="Batch size per host for preprocessing.")
  preprocess.add_argument("--num-core-per-host", type=int, default=PREPROCESS_DEFAULTS["num_core_per_host"],
                          help="Logical core count per host.")
  preprocess.add_argument("--split", choices=["train", "dev", "test"],
                          default=PREPROCESS_DEFAULTS["split"],
                          help="Split name used in output filenames.")
  preprocess.add_argument("--task", type=int, default=PREPROCESS_DEFAULTS["task"],
                          help="Worker index for file sharding.")
  preprocess.add_argument("--num-task", type=int, default=PREPROCESS_DEFAULTS["num_task"],
                          help="Total number of preprocessing workers.")
  preprocess.add_argument("--pass-id", type=int, default=PREPROCESS_DEFAULTS["pass_id"],
                          help="Repeated pass number.")
  add_bool_pair(
      preprocess, "use_eod", default=PREPROCESS_DEFAULTS["use_eod"],
      on_flag="--use-eod", off_flag="--no-use-eod",
      on_help="Insert <eod> at blank-line document boundaries.",
      off_help="Skip blank lines instead of inserting <eod>.")
  add_bool_pair(
      preprocess, "from_raw_text", default=PREPROCESS_DEFAULTS["from_raw_text"],
      on_flag="--from-raw-text", off_flag="--pretokenized-ids",
      on_help="Read raw text and SentencePiece-encode it.",
      off_help="Read whitespace-separated integer ids.")
  add_bool_pair(
      preprocess, "use_tpu", default=PREPROCESS_DEFAULTS["use_tpu"],
      on_flag="--use-tpu", off_flag="--cpu-only",
      on_help="Keep the preprocessing core-count behavior used by TPU-style runs.",
      off_help="Force single-core preprocessing behavior.")
  add_shared_text_flags(preprocess, defaults=PREPROCESS_DEFAULTS)

  gpu = subparsers.add_parser(
      "gpu", help="Generate a train_gpu.py command.",
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  gpu.add_argument("--record-info-dir", required=True,
                   help="Directory or comma-separated directories containing record-info JSON files.")
  gpu.add_argument("--model-dir", required=True, help="Training output directory.")
  gpu.add_argument("--num-hosts", type=int, default=1,
                   help="Number of hosts. The GPU entrypoint still runs on one host by default.")
  gpu.add_argument("--init-checkpoint", default=None, help="Initialization checkpoint.")
  gpu.add_argument("--num-core-per-host", type=int, default=GPU_DEFAULTS["num_core_per_host"],
                   help="Number of GPU towers per host.")
  gpu.add_argument("--train-batch-size", type=int, default=GPU_DEFAULTS["train_batch_size"],
                   help="Whole-host batch size.")
  gpu.add_argument("--train-steps", type=int, default=GPU_DEFAULTS["train_steps"],
                   help="Total number of training steps.")
  gpu.add_argument("--iterations", type=int, default=GPU_DEFAULTS["iterations"],
                   help="Training iterations per loop.")
  gpu.add_argument("--save-steps", type=int, default=GPU_DEFAULTS["save_steps"],
                   help="Checkpoint interval.")
  gpu.add_argument("--num-passes", type=int, default=GPU_DEFAULTS["num_passes"],
                   help="Number of passes to load from each record-info file.")
  add_shared_optimization_flags(gpu, defaults=GPU_DEFAULTS)
  add_shared_text_flags(gpu, defaults=GPU_DEFAULTS)
  add_shared_model_flags(gpu, defaults=GPU_DEFAULTS)

  tpu = subparsers.add_parser(
      "tpu", help="Generate a train.py TPU command.",
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  tpu.add_argument("--master", default=None, help="TPU master URL or local master.")
  tpu.add_argument("--tpu", default=None, help="Cloud TPU name or grpc:// address.")
  tpu.add_argument("--gcp-project", default=None, help="GCP project id.")
  tpu.add_argument("--tpu-zone", default=None, help="TPU zone.")
  add_bool_pair(
      tpu, "use_tpu", default=TPU_DEFAULTS["use_tpu"],
      on_flag="--use-tpu", off_flag="--cpu-only",
      on_help="Generate the TPU entrypoint command.",
      off_help="Generate the non-TPU entrypoint command.")
  tpu.add_argument("--num-hosts", type=int, default=TPU_DEFAULTS["num_hosts"],
                   help="Number of TPU hosts.")
  tpu.add_argument("--num-core-per-host", type=int, default=TPU_DEFAULTS["num_core_per_host"],
                   help="Number of TPU cores per host.")
  tpu.add_argument("--record-info-dir", required=True,
                   help="Directory or comma-separated directories containing record-info JSON files.")
  tpu.add_argument("--model-dir", required=True, help="Training output directory.")
  tpu.add_argument("--init-checkpoint", default=None, help="Initialization checkpoint.")
  tpu.add_argument("--num-passes", type=int, default=TPU_DEFAULTS["num_passes"],
                   help="Number of passes to load from each record-info file.")
  tpu.add_argument("--train-batch-size", type=int, default=TPU_DEFAULTS["train_batch_size"],
                   help="Global batch size across hosts and cores.")
  tpu.add_argument("--train-steps", type=int, default=TPU_DEFAULTS["train_steps"],
                   help="Total number of training steps.")
  tpu.add_argument("--iterations", type=int, default=TPU_DEFAULTS["iterations"],
                   help="Training iterations per loop.")
  tpu.add_argument("--save-steps", type=int, default=TPU_DEFAULTS["save_steps"],
                   help="Checkpoint interval.")
  tpu.add_argument("--max-save", type=int, default=TPU_DEFAULTS["max_save"],
                   help="Maximum number of checkpoints to retain.")
  add_shared_optimization_flags(tpu, defaults=TPU_DEFAULTS)
  add_shared_text_flags(tpu, defaults=TPU_DEFAULTS)
  add_shared_model_flags(tpu, defaults=TPU_DEFAULTS)
  add_bool_pair(
      tpu, "track_mean", default=TPU_DEFAULTS["track_mean"],
      on_flag="--track-mean", off_flag="--no-track-mean",
      on_help="Track mean loss in TPU monitoring.",
      off_help="Disable mean-loss tracking.")

  return parser


def main(argv=None):
  parser = build_parser()
  args = parser.parse_args(argv)

  if args.mode == "preprocess":
    command = build_preprocess_command(args, parser)
  elif args.mode == "gpu":
    command = build_gpu_command(args, parser)
  elif args.mode == "tpu":
    command = build_tpu_command(args, parser)
  else:
    parser.error(f"Unknown mode: {args.mode}")

  print(command)
  return 0


if __name__ == "__main__":
  sys.exit(main())
