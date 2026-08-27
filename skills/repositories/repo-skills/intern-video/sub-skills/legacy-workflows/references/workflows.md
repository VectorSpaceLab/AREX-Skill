# InternVideo1 Legacy Workflow Reference

## Pretraining areas

| Component | Purpose | Notes |
|---|---|---|
| VideoMAE | Masked video autoencoder pretraining and supervised finetuning | Uses VideoMAE-style entrypoints such as pretraining, class finetuning, and visualization scripts. |
| Multi-Modalities-Pretraining | Video-language contrastive learning demo/inference | Treat as legacy multimodal model evidence; newer retrieval work is usually in InternVideo2 multi-modality. |
| ViCLIP | Video CLIP trained with InternVid subsets | Useful for zero-shot/transfer baselines and InternVid model references. |
| UniFormerV2 | Spatiotemporal learning with image ViTs | Listed as a submodule/external component; verify availability before use. |

## Downstream areas

| Downstream task | Typical evidence path | Operational notes |
|---|---|---|
| Video-text retrieval | Video-Text-Retrieval | Dataset-specific scripts for MSR-VTT, DiDeMo, LSMDC, MSVD, VATEX, ActivityNet; requires checkpoint/data paths. |
| Open-set action recognition | Open-Set-Action-Recognition | MMAction-like dependency surface; isolate from other subprojects. |
| Spatial-temporal action localization | Spatial-Temporal-Action-Localization | AVA/AVA-Kinetics style scripts and configs; needs detection/localization data. |
| Temporal action localization | Temporal-Action-Localization | ActivityNet, THUMOS14, HACS, FineAction scripts. |
| Visual-language navigation | Visual-Language-Navigation | VLN-CE style environment and data assumptions. |
| VQA and zero-shot tasks | multi-modalities-downstream | VQA, zero-shot action recognition, multiple-choice evaluation. |

## Practical use

- Start from the README in the exact subproject, then create an isolated environment for that subproject.
- Expect older dependency pins, separate setup files, and less uniform launcher style than InternVideo2.
- When a user asks to reproduce a legacy benchmark, first collect: dataset name, checkpoint URL/local path, exact subproject, GPU count, and whether external submodules are initialized.
