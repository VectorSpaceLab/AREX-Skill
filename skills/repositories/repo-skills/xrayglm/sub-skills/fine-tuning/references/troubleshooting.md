# Fine-tuning troubleshooting and stop rules

Use this table after recording the exact command, environment, visible GPUs,
data revision, and checkpoint revision. Do not repeatedly retry an unexplained
failure; preserve logs and stop at the indicated gate.

| Symptom | Likely cause | Safe action / stop condition |
|---|---|---|
| Validator says malformed record | Missing field, empty/non-string value, wrong JSON root, or an `annotations` record in the OpenI source format | Keep the source unchanged. Route conversion to `data-preparation`; rerun the validator on its output. Do not train. |
| Relative images fail from another working directory | Base directory differs between validation and launcher | Rerun with an absolute `--base-dir` that contains the image tree, and use the same root in the reviewed launcher. Do not rewrite `img` values just to satisfy a check. |
| Image is present but unreadable | Corrupt/truncated file, unsupported format, permission, or wrong path | Replace or restore the source asset through data preparation; do not silently skip it or train with a blank tensor. |
| All OpenI records fail field checks | `data/Xray/openi-zh.json` is `{"annotations": [{"image_id", "caption"}]}`, not trainer-ready records | Stop. Produce explicit `img`/`prompt`/`label` records and image mapping upstream. A wrapper alone does not fix the schema. |
| Token sequence exceeds expected length | Source/target truncation, special-token accounting, or image block was changed | Recompute with the actual tokenizer. Ensure the 32 image positions remain intact and record effective max lengths. Do not increase limits blindly. |
| Image embeddings have a shape mismatch | `image_length`, image processor size, model checkpoint, or `pre_image` convention disagree | Restore the matching VisualGLM configuration (default image length 32, processor 224) and rerun a model/CUDA smoke test. Stop on mismatch. |
| `use_lora` and `use_qlora` both appear | Source branch prioritizes LoRA | Choose one explicitly. If QLoRA was intended, remove `use_lora` and run the separate CUDA NF4 gate. |
| QLoRA warns CPU-only or missing `libcudart` | Installed bitsandbytes cannot provide CUDA NF4 | Hard block QLoRA. Use LoRA, or install a compatible CUDA bitsandbytes build and pass the `LinearNF4` CUDA probe. Do not call import success readiness. |
| QLoRA `LinearNF4` construction/forward fails | Incompatible bitsandbytes, torch/CUDA ABI, dtype, or device | Save the complete diagnostic, stop QLoRA, and use LoRA until a compatible build is verified. No training retries. |
| `deepspeed` missing | `requirements_wo_ds.txt` was used or wrong Python environment is active | Install/activate the intended Python 3.10 environment and verify DeepSpeed 0.10.3 import. Do not substitute CPU execution for distributed training. |
| SAT/model import fails | Wrong environment/version or model cache unavailable | Verify SAT 0.3.7, `finetune_XrayGLM` and `lora_mixin` imports, model checkpoint/cache and working directory. Resolve before launch. |
| `torch.cuda.is_available()` is false | Wrong CUDA runtime, hidden devices, driver, or environment | Check the exact Python executable, `CUDA_VISIBLE_DEVICES`, driver, and torch CUDA build. CPU is only a parser/data check; stop training. |
| NCCL hangs or rank aborts | Bad GPU visibility, hostfile, network/IB/GDR setting, stale process, or device mismatch | Terminate the job safely, preserve rank logs, test a minimal approved distributed smoke, then adjust one NCCL/hostfile setting at a time. Do not resume blindly. |
| OOM during model/image forward | Six-billion-parameter model, image encoder, batch size, activation checkpointing, precision, or adapter mismatch | Stop; reduce reviewed batch/eval batch or sequence budgets, confirm FP16/adapter mode, and recalculate resources. Do not catch OOM and continue with partial state. |
| Checkpoint saves nowhere or is incomplete | Relative `--save`, permissions, save interval beyond short run, rank failure, or disk exhaustion | Stop and inspect disk/path/permissions and rank completion. Never overwrite the base checkpoint; do not treat a partial checkpoint as resumable without inspection. |
| Resume changes data order or duplicates work | `--resume-dataloader` state does not match data/config | Compare data revision, loader state, world size, batch size, and adapter config. If uncertain, start a new output directory only after approval. |
| Unexpected trainable parameters | Adapter naming/version mismatch or a full-model path was enabled | Print `requires_grad` names and parameter counts, compare to the requested adapter, and stop before optimizer creation if unexpected base/vision weights are enabled. |
| Merge produces load or output mismatch | Wrong base/rank/adapter, NF4 dequantization issue, incomplete files, or merge into original | Restore the untouched base and adapter. Merge into a new directory only, preserve config, and compare a small CUDA output before use. |

## Required failure report

For any blocked run, retain: command/template revision; JSON and image-root
paths plus count; validator output; Python/torch/CUDA/SAT/DeepSpeed/
bitsandbytes versions; `CUDA_VISIBLE_DEVICES`; hostfile; adapter flags and
rank/prefix settings; first error from each rank; checkpoint destination; and
whether the base checkpoint was modified. This report is sufficient to resume
triage without rerunning a costly job.

## Stop conditions

Stop immediately for a malformed or unreadable record, unresolved path base,
missing required checkpoint, QLoRA without a passing CUDA NF4 probe, missing
DeepSpeed/NCCL for a requested distributed run, unexplained trainable base
parameters, OOM with no reviewed resource change, rank divergence, or a
partial/ambiguous checkpoint. Escalate medical-content quality or data rights
to the upstream data-preparation/review process; this route does not declare
radiology labels clinically valid.
