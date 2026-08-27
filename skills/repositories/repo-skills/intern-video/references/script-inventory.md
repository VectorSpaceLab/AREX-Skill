# Source Script Inventory and Bundled Replacements

## Purpose

This skill does not copy InternVideo's many large cluster launch scripts verbatim. Instead, it distills their reusable command structure into references and safe bundled helpers.

| Source artifact family | Runtime replacement | Why |
|---|---|---|
| InternVideo2 single-modality `scripts/pretraining`, `scripts/finetuning`, `scripts/distillation` shell launchers | `sub-skills/single-modality/references/workflows.md` and `sub-skills/single-modality/scripts/build_single_modality_command.py` | Hundreds of cluster-specific variants differ mainly by dataset/model/GPU flags. The helper builds safe command skeletons without submitting jobs. |
| InternVideo2 multi-modality `scripts/pretraining`, `scripts/evaluation`, `tools/run.py`, `torchrun.sh` | `sub-skills/multi-modality/references/workflows.md` and `sub-skills/multi-modality/scripts/build_multimodal_launch.py` | Preserves stage2/CLIP task/config/launcher conventions while avoiding rsync/job-submission side effects. |
| InternVideo2 preprocessing scripts such as JSON-to-SQLite converters | `sub-skills/datasets/scripts/validate_internvideo_annotations.py` | Future agents usually need schema/path validation before conversion; the bundled validator is safe on tiny fixtures. |
| InternVideo3 SFT train and rjob scripts | `sub-skills/video-mllm/references/internvideo3-sft.md` plus root backend checker | Cluster-specific, large-GPU runs are unsuitable as bundled scripts; the reference records env vars and command shapes. |
| InternVideo3 benchmark evaluation scripts | `sub-skills/video-mllm/references/evaluation.md` | Benchmark data/model requirements are external and expensive; documented as gated workflows. |
| InternVideo-Next `main_stage1.py` / `main_stage2.py` | `sub-skills/next-pretraining/references/workflows.md` | Full execution needs datasets, FlashAttention, and GPU memory; reference preserves stages, architecture terms, and readiness checks. |
| InternVideo1 legacy scripts | `sub-skills/legacy-workflows/references/workflows.md` | Legacy subprojects are self-contained and heterogeneous; routing/reference guidance is safer than copying outdated launchers. |

When a user provides a local checkout script path, the root `scripts/summarize_training_script.py` helper can summarize environment variables, resource requests, placeholders, and Python entry points without executing the script.
