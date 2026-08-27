#!/usr/bin/env python3
"""Build MiniMind-V training commands without launching training."""
from __future__ import annotations
import argparse, shlex
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class StageDefaults:
    script: str; save_weight: str; epochs: int; batch_size: int; lr: float; max_seq_len: int; data_path: str; from_weight: str; freeze_llm: int; project: str
DEFAULTS = {
    "pretrain": StageDefaults("train_pretrain_vlm.py", "pretrain_vlm", 2, 16, 4e-4, 450, "../dataset/pretrain_i2t.parquet", "llm", 2, "MiniMind-V-Pretrain"),
    "sft": StageDefaults("train_sft_vlm.py", "sft_vlm", 2, 4, 5e-6, 768, "../dataset/sft_i2t.parquet", "pretrain_vlm", 1, "MiniMind-V-SFT"),
}

def positive(v):
    i=int(v)
    if i<=0: raise argparse.ArgumentTypeError("must be positive")
    return i

def parser():
    p=argparse.ArgumentParser(description="Print safe MiniMind-V Pretrain/SFT commands without executing training.")
    p.add_argument("stage", choices=sorted(DEFAULTS))
    p.add_argument("--repo-root", default=".", help="Checkout root for --dry-check-files.")
    p.add_argument("--ddp-gpus", type=positive, default=1)
    p.add_argument("--epochs", type=positive); p.add_argument("--batch-size", type=positive)
    p.add_argument("--learning-rate", type=float); p.add_argument("--from-weight"); p.add_argument("--from-resume", type=int, choices=[0,1])
    p.add_argument("--freeze-llm", type=int, choices=[0,1,2]); p.add_argument("--use-moe", type=int, choices=[0,1])
    p.add_argument("--data-path"); p.add_argument("--save-dir"); p.add_argument("--save-weight"); p.add_argument("--device")
    p.add_argument("--dtype", choices=["bfloat16","float16"], default="bfloat16")
    p.add_argument("--hidden-size", type=positive, default=768); p.add_argument("--num-hidden-layers", type=positive, default=8); p.add_argument("--max-seq-len", type=positive)
    p.add_argument("--use-compile", type=int, choices=[0,1], default=0); p.add_argument("--use-wandb", action="store_true"); p.add_argument("--dry-check-files", action="store_true")
    return p

def q(parts): return " ".join(shlex.quote(str(x)) for x in parts)
def from_trainer(repo: Path, rel: str) -> Path:
    p=Path(rel).expanduser(); return p if p.is_absolute() else repo/"trainer"/p

def weight_name(prefix, hidden, moe): return f"{prefix}_{hidden}{'_moe' if moe else ''}.pth"

def main(argv=None):
    a=parser().parse_args(argv); d=DEFAULTS[a.stage]
    save_dir=a.save_dir or "../out"; save_weight=a.save_weight or d.save_weight; epochs=a.epochs or d.epochs; batch=a.batch_size or d.batch_size; lr=a.learning_rate or d.lr
    data=a.data_path or d.data_path; from_weight=a.from_weight or d.from_weight; resume=0 if a.from_resume is None else a.from_resume; freeze=d.freeze_llm if a.freeze_llm is None else a.freeze_llm; moe=0 if a.use_moe is None else a.use_moe; max_seq=a.max_seq_len or d.max_seq_len
    launcher=["torchrun","--nproc_per_node",a.ddp_gpus,d.script] if a.ddp_gpus>1 else ["python",d.script]
    args=["--save_dir",save_dir,"--save_weight",save_weight,"--epochs",epochs,"--batch_size",batch,"--learning_rate",lr,"--dtype",a.dtype,"--hidden_size",a.hidden_size,"--num_hidden_layers",a.num_hidden_layers,"--max_seq_len",max_seq,"--use_moe",moe,"--data_path",data,"--from_weight",from_weight,"--from_resume",resume,"--freeze_llm",freeze,"--use_compile",a.use_compile,"--wandb_project",d.project]
    if a.device: args += ["--device",a.device]
    if a.use_wandb: args += ["--use_wandb"]
    print("# Safe MiniMind-V training command (not executed by this builder)")
    print("cd trainer && "+q([*launcher,*args]))
    if a.stage=="sft" and from_weight=="pretrain_vlm": print("# Tip: if skipping Pretrain, use --from-weight llm.")
    if a.dry_check_files:
        repo=Path(a.repo_root).expanduser().resolve(); missing=0
        checks=[("training script", repo/"trainer"/d.script), ("data parquet", from_trainer(repo,data)), ("tokenizer", repo/"model"/"tokenizer.json"), ("SigLIP2", repo/"model"/"siglip2-base-p32-256-ve")]
        if from_weight!="none": checks.append(("initial weight", repo/"out"/weight_name(from_weight,a.hidden_size,moe)))
        for label,path in checks:
            ok=path.exists(); print(f"[{'OK' if ok else 'MISSING'}] {label}: {path.name if path.name else path}"); missing += 0 if ok else 1
        if missing: print(f"Result: {missing} prerequisite(s) missing. Command was printed for planning only."); return 2
        print("Result: required prerequisite paths are present. This still does not validate GPU capacity or dataset correctness.")
    return 0
if __name__=="__main__": raise SystemExit(main())
