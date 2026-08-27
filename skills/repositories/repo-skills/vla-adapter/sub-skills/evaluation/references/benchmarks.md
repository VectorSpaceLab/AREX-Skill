# Benchmarks, checkpoints, and metric interpretation

Use this reference to map a user request onto a valid VLA-Adapter evaluation suite and to interpret full-run metrics. Do not compare partial smoke runs with the published numbers.

## Suite and checkpoint map

| Benchmark | Suite flag | Published checkpoint names | Full-run volume | Primary metric |
| --- | --- | --- | --- | --- |
| LIBERO-Spatial | `libero_spatial` | `LIBERO-Spatial`, `LIBERO-Spatial-Pro` | 10 tasks × 50 trials = 500 episodes | Overall success rate |
| LIBERO-Object | `libero_object` | `LIBERO-Object`, `LIBERO-Object-Pro` | 10 tasks × 50 trials = 500 episodes | Overall success rate |
| LIBERO-Goal | `libero_goal` | `LIBERO-Goal`, `LIBERO-Goal-Pro` | 10 tasks × 50 trials = 500 episodes | Overall success rate |
| LIBERO-Long / LIBERO-10 | `libero_10` | `LIBERO-Long`, `LIBERO-Long-Pro` | 10 tasks × 50 trials = 500 episodes | Overall success rate |
| CALVIN ABC→D | `calvin_abc` | `CALVIN-ABC-Pro`; custom original checkpoints may be named differently | 1,000 five-instruction sequences | Average successful sequence length |

Checkpoint arguments can be local directories such as `outputs/LIBERO-Spatial-Pro` or model identifiers supported by the evaluator. For the most robust reproduction path, use local checkpoint directories that contain all downloaded files. This is especially important for CALVIN and for original/custom checkpoints, because the component-loading helper has explicit support for the released Pro LIBERO Hub ids but not every possible model id.

## Command generation examples

Invoke the skill-local builder by absolute skill path and always pass the
absolute native checkout root. It prints (but does not run) a command beginning
with `cd <absolute-repo-root> &&`.

LIBERO-Spatial Pro:

```bash
python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/evaluation/scripts/build_eval_command.py" \
  --repo-root "$VLA_ADAPTER_REPO_ROOT" \
  --benchmark libero \
  --suite libero_spatial \
  --checkpoint outputs/LIBERO-Spatial-Pro \
  --use-pro-version \
  --gpu 0 \
  --log-file eval_logs/Spatial--chkpt.log
```

LIBERO-Long original:

```bash
python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/evaluation/scripts/build_eval_command.py" \
  --repo-root "$VLA_ADAPTER_REPO_ROOT" \
  --benchmark libero \
  --suite libero_10 \
  --checkpoint outputs/LIBERO-Long \
  --no-use-pro-version \
  --gpu 0 \
  --log-file eval_logs/Long--chkpt.log
```

CALVIN ABC→D Pro:

```bash
python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/evaluation/scripts/build_eval_command.py" \
  --repo-root "$VLA_ADAPTER_REPO_ROOT" \
  --benchmark calvin \
  --suite calvin_abc \
  --checkpoint outputs/CALVIN-ABC-Pro \
  --use-pro-version \
  --gpu 0 \
  --log-file eval_logs/CALVIN--ABC.log
```

The generated commands intentionally omit a trailing `&`. Add backgrounding
only when monitoring and log collection are already planned.


## Published LIBERO results

The README table and bundled result logs report these VLA-Adapter metrics on H100-class hardware. Small hardware, driver, CUDA, simulator, or random-seed differences can shift results slightly.

| Suite | Original metric | Pro metric | Evidence log labels |
| --- | ---: | ---: | --- |
| `libero_spatial` | 97.8% | 99.6% | `Inference-Spatial--97.8.log`, `Inference--Spatial_Pro--99.6.log` |
| `libero_object` | 99.2% | 99.6% | `Inference-Object--99.2.log`, `Inference--Object_Pro--99.6.log` |
| `libero_goal` | 97.2% | 98.2% | `Inference-Goal--97.2.log`, `Inference-Goal_Pro--98.2.log` |
| `libero_10` | 95.0% | 96.4% | `Inference-Long--95.0.log`, `Inference--Long_Pro--96.4.log` |
| Average | 97.3% | 98.5% | README comparison table |

Full-run LIBERO logs end with:

- `Total episodes: 500`
- `Total successes: <count>`
- `Overall success rate: <fraction> (<percent>%)`

Because rich terminal formatting can wrap the numeric rate onto the next line, parse the line following `Overall success rate` when needed.

## Published CALVIN ABC→D results

CALVIN evaluates sequences of five language instructions. A result of 4.50 means the policy completes an average of 4.50 subtasks before the first failure across the 1,000 generated sequences.

| Method | 1 instruction | 2 instructions | 3 instructions | 4 instructions | 5 instructions | Avg. len |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| VLA-Adapter original | 99.1% | 94.6% | 88.8% | 82.8% | 76.5% | 4.42 |
| VLA-Adapter-Pro | 98.5% | 95.0% | 90.5% | 85.3% | 80.0% | 4.50 |

The Pro CALVIN evidence log label is `Inference--CALVIN_Pro--4.50.log`. Its final summary includes `Average successful sequence length: 4.50`, chain success rates for 1 through 5 instructions, and per-task success counts.

## How to interpret deviations

- Lower LIBERO percentages from fewer than 50 trials per task are sampling checks, not paper-comparable evaluations.
- A high early task success rate with a low final LIBERO overall rate often indicates long-horizon failures on later tasks; inspect per-task log blocks and rollout videos.
- CALVIN chain success rates should decrease from 1 to 5 instructions; a non-monotonic parse usually means the wrong log lines were extracted.
- CALVIN average sequence length is bounded by 0 to 5 and should be interpreted alongside chain success rates and per-task failure counts.
- Benchmark comparisons should use the same checkpoint family, suite, image preprocessing, action postprocessing, evaluation volume, and preferably similar GPU class.
