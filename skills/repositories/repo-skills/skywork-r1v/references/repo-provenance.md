# Repository provenance

This skill was generated from the Skywork-R1V repository checkout in the current batch workspace.

Schema: `disco.repo-provenance.v1`

## Snapshot

- Source commit: `b806cefffa71be98cdadec30ef79cdeeb703a4a0`
- Branch: `main`
- Tag at HEAD: none
- Working tree state: dirty
- Dirty paths: `skills/` (generated skill and review artifacts)
- Public remote: `https://github.com/SkyworkAI/Skywork-R1V.git`
- Repo package metadata: no top-level installable Python package; embedded evaluation package `vlmeval` reports version `0.1.0` in `eval/vlmevalkit/setup.py`

## Evidence paths used

- `README.md`
- `inference/inference_with_transformers.py`
- `inference/inference_with_vllm.py`
- `inference/utils.py`
- `inference/setup.sh`
- `r1v4/README.md`
- `r1v4/batch_nonstream.py`
- `r1v4/batch_stream.py`
- `r1v4/batch_planner_nonstream.py`
- `r1v4/batch_planner_stream.py`
- `r1v4/parse_utils.py`
- `r1v4/visual.py`
- `r1v4/test_cases.jsonl`
- `eval/README.md`
- `eval/vlmevalkit/build_env.sh`
- `eval/vlmevalkit/eval_shell/launch_vlm_model.sh`
- `eval/vlmevalkit/eval_shell/run_eval.sh`
- `eval/vlmevalkit/eval_shell/rule_base_mmmu.py`
- `eval/vlmevalkit/eval_shell/rule_base_logicvista.py`
- `eval/vlmevalkit/run.py`
- `eval/vlmevalkit/run_phyx.py`
- `eval/EMMA/generate_response.py`
- `eval/EMMA/data_utils.py`
- `eval/EMMA/run_skywork.sh`
- `eval/MMK12/evaluate.py`
- `eval/MMK12/calculate_score.py`
- `eval/MMK12/launch_skywork_r1v3.sh`
- `eval/vlmevalkit/setup.py`
- `eval/vlmevalkit/requirements.txt`

## Refresh note

If the repository changes, refresh the generated skill when any of these shift:

- local inference flags or image preprocessing behavior
- R1V4 batch model names, payload schema, or tagged response grammar
- VLMEvalKit launch/evaluation scripts, dataset expectations, or judge flow
- EMMA/MMK12 command surfaces or result formats
