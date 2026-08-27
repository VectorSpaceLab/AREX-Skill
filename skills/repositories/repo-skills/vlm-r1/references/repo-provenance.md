# VLM-R1 repo provenance

This file records the source snapshot used to create the `vlm-r1` operating skill. It intentionally avoids local checkout paths and private environment details.

## Source snapshot

- Public repository: `https://github.com/om-ai-lab/VLM-R1.git`
- Branch: `main`
- Commit: `90052f478646e38bc67363862f699b7afca6b337`
- Exact tag: none at `HEAD`
- Dirty state during skill creation: generated `skills/` output was untracked after creation; no source-code modifications were used as evidence.
- Nested Python distribution: `open-r1`
- Package version from metadata/inspection: `0.1.0.dev0`
- Import package: `open_r1`

## Evidence paths used

- `README.md`
- `setup.sh`
- `Dockerfile`
- `run_scripts/multinode_training_args.yaml`
- `run_scripts/multinode_training_demo.sh`
- `run_scripts/run_grpo_gui.sh`
- `run_scripts/run_grpo_gui_defect_detection.sh`
- `run_scripts/run_grpo_rec.sh`
- `run_scripts/run_grpo_rec_internvl.sh`
- `run_scripts/run_grpo_rec_lora.sh`
- `run_scripts/run_grpo_rec_more_params.sh`
- `src/eval/test_od_r1.py`
- `src/eval/test_rec_baseline.py`
- `src/eval/test_rec_r1.py`
- `src/eval/test_rec_r1_internvl.py`
- `src/open-r1-multimodal/setup.py`
- `src/open-r1-multimodal/configs/ddp.yaml`
- `src/open-r1-multimodal/configs/qwen2vl_sft_config.yaml`
- `src/open-r1-multimodal/configs/zero2.yaml`
- `src/open-r1-multimodal/configs/zero3.yaml`
- `src/open-r1-multimodal/data_config/rec.yaml`
- `src/open-r1-multimodal/data_config/rec_internvl.yaml`
- `src/open-r1-multimodal/data_jsonl/gui_multi-image.jsonl`
- `src/open-r1-multimodal/local_scripts/create_vision_cot_data.py`
- `src/open-r1-multimodal/local_scripts/prepare_hf_data.py`
- `src/open-r1-multimodal/local_scripts/train_qwen2_vl.sh`
- `src/open-r1-multimodal/local_scripts/train_aria_moe.sh`
- `src/open-r1-multimodal/local_scripts/zero*.json`
- `src/open-r1-multimodal/src/open_r1/configs.py`
- `src/open-r1-multimodal/src/open_r1/grpo_jsonl.py`
- `src/open-r1-multimodal/src/open_r1/trainer/grpo_config.py`
- `src/open-r1-multimodal/src/open_r1/trainer/grpo_trainer.py`
- `src/open-r1-multimodal/src/open_r1/vlm_modules/vlm_module.py`
- `src/open-r1-multimodal/src/open_r1/vlm_modules/qwen_module.py`
- `src/open-r1-multimodal/src/open_r1/vlm_modules/internvl_module.py`
- `src/open-r1-multimodal/src/open_r1/vlm_modules/glm_module.py`
- `assets/add_new_model.md`
- `ascend_inference/300IDuo/README.md`
- `ascend_inference/300IDuo/offline_inference.py`
- `ascend_inference/300IDuo/vllm_ascend_client.sh`
- `ascend_inference/300IDuo/vllm_ascend_server.sh`
- `ascend_inference/910B/vllm_ascend/README.md`
- `ascend_inference/910B/vllm_ascend/offline_inference.py`
- `ascend_inference/910B/vllm_ascend/vllm_ascend_client.sh`
- `ascend_inference/910B/vllm_ascend/vllm_ascend_server.sh`
- `ascend_inference/910B/xllm/README.md`
- `ascend_inference/910B/xllm/xllm_client.sh`
- `ascend_inference/910B/xllm/xllm_server.sh`

## Refresh triggers

Refresh this skill if any of these change:

- The nested `open-r1` package metadata, dependency pins, or package entrypoint layout.
- `grpo_jsonl.py`, trainer classes, reward functions, or VLM module interfaces.
- Root or nested GRPO launch scripts, DeepSpeed configs, or multi-node launch templates.
- REC/OVD evaluation scripts or bbox coordinate normalization logic.
- Ascend vllm-ascend/XLLM deployment docs or model checkpoint guidance.
- The GLM/Transformers compatibility issue is fixed or the project updates its pinned Transformers version.
