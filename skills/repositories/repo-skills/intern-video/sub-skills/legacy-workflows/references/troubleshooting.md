# Legacy Workflow Troubleshooting

InternVideo1 is a set of old, mostly independent subprojects. Most failures come from routing a task to the wrong component, mixing environments, or trying to run large distributed workflows without the required data/checkpoints.

## Wrong Component Selected

**Symptom:** The user asks for retrieval, VQA, open-set, or localization but starts from `Pretrain/VideoMAE` only.

**Fix:** Use `references/workflows.md` to split the task:

- VideoMAE handles masked-video pretraining and visual finetuning.
- Video-text retrieval has its own downstream folder and script families.
- VQA/zero-shot multiple choice belong to multi-modalities downstream.
- Open-set action recognition belongs to the MMAction-derived open-set folder.
- Spatial-temporal and temporal localization are separate workflows with different data formats.

## Legacy Environment Conflicts

**Symptom:** Imports fail for `mmcv`, `mmaction`, `decord`, `av`, `timm`, `deepspeed`, `habitat`, or CLIP-related packages.

**Fix:** Do not install all legacy requirements into one environment. Prepare a component-specific environment matching the selected workflow:

- VideoMAE and spatial-temporal localization expect timm 0.4.x, decord, einops, and DeepSpeed-era versions.
- Open-set recognition expects a PyTorch/CUDA-compatible `mmcv-full` build and may fail if plain `mmcv` is installed instead.
- VLN expects Habitat Simulator/Habitat-lab plus Matterport3D data and is not a normal video-classification environment.
- ViCLIP and multi-modalities downstream expect CLIP/OpenCLIP or All-In-One-derived packages.

If exact old binary packages are unavailable, keep the answer at static guidance level or route to a newer InternVideo branch when the user is not reproducing legacy results.

## Missing Checkpoints

**Symptom:** The script starts but cannot load InternVideo-MM, VideoMAE, ViCLIP, CLIP, or navigation checkpoints.

**Fix:** Identify which component owns the checkpoint:

- VideoMAE checkpoints for visual pretraining/finetuning and many legacy visual downstream tasks.
- InternVideo-MM B/16 for Multi-Modalities-Pretraining and multi-modalities downstream.
- ViCLIP checkpoints for InternVid-trained video-text representation work.
- Original CLIP visual/text weights for ViCLIP and downstream video-language code.
- VLN pretrained model bundles for navigation evaluation.

Do not substitute a newer InternVideo2 or MLLM checkpoint unless the user is intentionally porting the workflow.

## Dataset Or Annotation Layout Mismatch

**Symptom:** Data loaders fail with missing annotation files, unknown dataset names, empty videos, or feature path errors.

**Fix:** Match the component's expected data form:

- Retrieval: original MSR-VTT, MSVD, LSMDC, ActivityNet, DiDeMo, or VATEX data plus the retrieval annotation bundle.
- Open-set: UCF-101 for closed-set training and HMDB-51 or MiT-v2 as unknown/out-of-distribution tests.
- Spatial-temporal localization: AVA or AVA-Kinetics annotations and auxiliary mapping/ground-truth metadata.
- Temporal localization: pre-extracted feature tensors and ActivityNet-style annotations for THUMOS14, ActivityNet, HACS, or FineAction.
- VLN: Matterport3D scene datasets, VLN-CE preprocessed splits, and navigation pretrained models.
- ViCLIP/InternVid: large video-text annotation/data sources and preprocessing outputs such as SQLite/serialized metadata when selected.

## Distributed Launch Or SLURM Problems

**Symptom:** Commands fail around `torch.distributed.launch`, `torchrun`, `srun`, rendezvous endpoints, `MASTER_PORT`, node rank, or GPU counts.

**Fix:** Treat legacy shell files as command-shape evidence. Reconstruct launch variables for the user's cluster rather than copying a source script verbatim. Confirm:

- Number of GPUs and nodes.
- Rendezvous host/port or SLURM partition.
- Batch size and update frequency adjusted to available memory.
- Dataset and output variables provided by the user.

If the user has no cluster/GPU allocation, classify full training/evaluation as unverified and offer static configuration review only.

## Submodule Or External Repo Missing

**Symptom:** UniFormerV2 or Ego4D/Ego-Tasks references cannot be found or are empty.

**Fix:** State that these are external/submodule surfaces. Do not assume they are bundled in the runtime skill. For UniFormerV2, give high-level component routing and require a separately prepared pinned checkout for detailed commands. For Ego4D/Ego-Tasks, treat detailed commands as out-of-scope unless the user supplies that repository.

## Video Decode Failures

**Symptom:** Video reading fails, frames are missing, or preprocessing/compression utilities produce corrupt outputs.

**Fix:** Confirm the selected workflow's decoder stack and data form. Many components use decord/OpenCV/PyAV and differ between raw videos, compressed 3fps retrieval videos, AVA clips, and pre-extracted features. Do not apply a retrieval compression rule to VideoMAE pretraining or localization without checking the target data loader.

## Open-Set Recognition Specific Failures

**Symptom:** Thresholding, OOD detection, AUROC computation, or libMR/OpenMax baselines fail.

**Fix:** Separate the pipeline stages: train/finetune, get uncertainty threshold, OOD distribution detection, then AUROC calculation. Make sure the model output directory and experiment family match the chosen backbone (`mae`, `i3d`, `tsm`, `slowfast`, `tpn_slowonly`, or `csn`). For libMR/OpenMax baselines, C/Cython compilation may be required and should not be treated as a generic Python import issue.

## VLN Specific Failures

**Symptom:** Habitat import, simulator asset, or scene dataset errors appear.

**Fix:** Verify that the task really is visual-language navigation. If yes, the user must provide Habitat-compatible simulator setup, Matterport3D scene assets, VLN-CE preprocessed splits, and matching pretrained navigation models. If the request is ordinary video QA or video captioning, route away from VLN.

## Reproducibility Expectations

**Symptom:** The user expects exact paper numbers from a modern machine with partial data.

**Fix:** State that InternVideo1 reproduction is sensitive to old dependencies, checkpoints, datasets, GPU scale, and distributed launch settings. Offer a compatibility checklist and command-shape plan, but do not claim exact reproduction unless the user has matched the legacy environment and assets.
