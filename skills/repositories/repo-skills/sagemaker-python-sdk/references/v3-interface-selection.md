# SageMaker Python SDK v3 interface selection

Use this reference before writing SageMaker code. It maps user intent to the v3
package and interface that should be used by default.

## Install choices

```bash
# Complete v3 SDK meta package
pip install sagemaker

# Modular packages when the user wants a narrower install
pip install sagemaker-core
pip install sagemaker-train
pip install sagemaker-serve
pip install sagemaker-mlops
```

Supported Python versions in this checkout are Python 3.10, 3.11, and 3.12.
Set `AWS_REGION` or `AWS_DEFAULT_REGION` before high-level imports or examples
that construct sessions, serving objects, or workflow objects.

## Intent map

| User says | Default v3 interface | Sub-skill |
| --- | --- | --- |
| train, training job, managed training, custom container | `sagemaker.train.ModelTrainer` | `sub-skills/training/SKILL.md` |
| local training or distributed local training | `ModelTrainer(training_mode=Mode.LOCAL_CONTAINER)` with `Compute(instance_type="local_cpu"/"local_gpu")` | `sub-skills/training/SKILL.md` |
| distributed / multi-node / multi-GPU | `ModelTrainer` plus `Torchrun`, `MPI`, `SMP`, or custom `DistributedConfig` | `sub-skills/training/SKILL.md` |
| HPO / hyperparameter tuning / sweep | `sagemaker.train.tuner.HyperparameterTuner` or low-level `HyperParameterTuningJob` | `sub-skills/training/SKILL.md` |
| fine-tune a foundation model / SFT / DPO / RLVR / RLAIF / CPT / MultiTurnRL | specialized trainer classes such as `SFTTrainer`, `DPOTrainer`, `RLVRTrainer`, `RLAIFTrainer`, `CPTTrainer`, `MultiTurnRLTrainer` | `sub-skills/model-customization/SKILL.md` |
| evaluate a foundation model / LLM-as-judge / benchmark / custom scorer | `BenchMarkEvaluator`, `CustomScorerEvaluator`, `LLMAsJudgeEvaluator`, AI Registry assets | `sub-skills/model-customization/SKILL.md` |
| deploy, host, endpoint inference, local inference | `sagemaker.serve.ModelBuilder` | `sub-skills/serving/SKILL.md` |
| custom inference logic | subclass `InferenceSpec` and pair with `SchemaBuilder` | `sub-skills/serving/SKILL.md` |
| serverless / async / batch transform deployment through ModelBuilder | `ModelBuilder.deploy(..., inference_config=...)` | `sub-skills/serving/SKILL.md` |
| invoke deployed endpoint | returned `Endpoint.invoke(...)` or core `Endpoint.invoke(...)` | `sub-skills/serving/SKILL.md` or `sub-skills/core-resources/SKILL.md` |
| process data / feature engineering / preprocessing job | low-level `ProcessingJob` or helper `ScriptProcessor` / `Processor` | `sub-skills/core-resources/SKILL.md` |
| batch transform / offline scoring | `Transformer` or `TransformJob` | `sub-skills/core-resources/SKILL.md` |
| retrieve a container image URI | `sagemaker.core.image_uris.retrieve(...)` | `sub-skills/core-resources/SKILL.md` |
| build a pipeline / orchestrate workflow | `sagemaker.mlops.workflow.Pipeline` and workflow steps | `sub-skills/mlops/SKILL.md` |
| model registry / approval / governance | `sagemaker.mlops.workflow.ModelStep`, core model package resources, registry APIs | `sub-skills/mlops/SKILL.md` |
| Feature Store / feature group manager / dataset builder | `sagemaker.mlops.feature_store` and core `FeatureGroup` resources | `sub-skills/mlops/SKILL.md` |
| lineage | `sagemaker.core.lineage` | `sub-skills/mlops/SKILL.md` or `sub-skills/core-resources/SKILL.md` |
| migrate old SDK code | use `references/migration-v2-to-v3.md`, then route to the target sub-skill | root |

## Minimal setup pattern

```python
from sagemaker.core.helper.session_helper import Session, get_execution_role

session = Session()
role = get_execution_role(session)
bucket = session.default_bucket()
region = session.boto_region_name
```

If role discovery is not available, ask the user for a role name/ARN or use a
placeholder. Do not invent or hardcode real role ARNs.

## Cloud-vs-local decision

- **No-submit design:** provide code with placeholders and explain prerequisites.
- **Dry-run validation:** use `dry_run=True` where supported by trainers and
  evaluators; dry-run still validates cloud-facing configuration and may need
  credentials and S3 existence checks.
- **Local in-process serving:** safest local serving path when a custom
  `InferenceSpec` can run in Python without containers.
- **Local container mode:** requires Docker, images, local source/model paths,
  and cleanup.
- **Cloud execution:** requires explicit user authorization because SageMaker,
  Bedrock, Batch, EMR, Feature Store, and endpoint resources are billable.

## Self-check before returning code

1. Confirm the selected interface is v3 and SDK-first.
2. Search the output mentally for deprecated v2 imports and methods.
3. Replace real-looking account IDs, ARNs, buckets, regions, subnets, and
   credentials with placeholders or SDK discovery helpers.
4. Include cleanup for endpoints, pipelines, jobs, or lineage objects when code
   creates resources.
5. State any skipped cloud, Docker, credential, or optional-dependency checks.
