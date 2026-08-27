# Troubleshooting

Start with the two safe probes:
- `python scripts/check_runtime.py`
- `python scripts/validate_path_conf.py --mode local --script nets/resnet_at_cifar10_run.py --conf path.conf`

## Common failures

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| `ImportError: tensorflow` or missing `tf.contrib` | Python or TensorFlow version is not TF1-era | use a Python 3.6 + TensorFlow 1.x environment and rerun `check_runtime.py` |
| `tensorflow.contrib.lite.python.lite_constants` missing | TensorFlow is too new or incomplete | do not use TF2; switch back to the supported TF1 stack |
| `path.conf` preview reports missing dataset path | the mode-specific `data_dir_*_<dataset>` entry is still `None` | fill the key or accept the placeholder preview if you only need a template |
| `run_local.sh` cannot find idle GPUs | `nvidia-smi` is unavailable or all visible GPUs are above the 50% memory-use threshold | reduce `--nb_gpus`, free a GPU, or use another host |
| `MultiGpuWrapper` warns about Horovod / TF-Plus | optional distributed backends are not installed | stay on single-GPU mode or install one supported backend |
| Docker or Seven launcher fails before execution | container/cluster tooling is missing or the environment is Tencent-specific | use `create_minimal_copy.sh` for isolated staging and keep the source checkout untouched |
| AutoML conversion or parsing fails | the hparam file still has placeholders, or the result log lacks `accuracy`, `pruning ratio`, or `loss` lines | regenerate the file or feed a fuller TensorFlow log |

## Launcher-specific tips

- The dataset suffix must match the run script name pattern `at_<dataset>_run.py`.
- `data_hdfs_host` and `model_http_url` are forwarded only when they are not `None`.
- The GPU picker uses a 50% memory threshold, so a card can be visible but still skipped.
- If `check_runtime.py` cannot import `utils.multi_gpu_wrapper`, run it from a PocketFlow checkout root or pass `--repo-root <checkout>`.
- If the preview looks right but the run still fails, the issue is usually environment-specific rather than the config file itself.

## What not to do

- Do not edit the source checkout in place just to make a container or Seven job work.
- Do not assume Horovod or TF-Plus is present; check first.
- Do not use the AutoML helpers to explain learner semantics; that belongs in the learner sub-skill.
