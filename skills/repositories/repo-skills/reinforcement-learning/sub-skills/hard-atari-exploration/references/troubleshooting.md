# Hard Atari Troubleshooting

Use this matrix when hard-exploration Atari runs fail, produce confusing metrics, or appear to contradict each other. For protocol details see [`rnd-and-envpool-guide.md`](rnd-and-envpool-guide.md), [`go-explore-and-robustification.md`](go-explore-and-robustification.md), and [`run-management.md`](run-management.md).

## First triage: identify the protocol

| Symptom/question | Likely issue | Action |
| --- | --- | --- |
| "Go-Explore scored 31k but PPO+RND scored 3k; which is better?" | Protocol mismatch. Go-Explore Phase 1 is deterministic restore-based search; PPO+RND is sticky-action RL. | Do not rank them directly. Compare deterministic search to deterministic search, and sticky-action policy scores to sticky-action policy scores. |
| "Robustification has no score from reset but Phase 1 has a high score." | Phase 1 found a trajectory; robustification has not yet learned a policy that executes from reset. | Track `curriculum_progress` and final sticky-action eval separately from Phase 1 score. |
| "A run used `montezuma_goexplore` and another used `montezuma`." | Different environment contracts. | `montezuma_goexplore` means deterministic Phase 1 restore protocol; `montezuma` means sticky-action RL env key. |

## Installation and backend problems

| Error/symptom | Likely cause | Fix/check |
| --- | --- | --- |
| `ModuleNotFoundError: envpool` | PPO+RND training backend is missing. | Install a package set that includes envpool, or run only the self-contained smoke/data checks. Go-Explore restore does not use envpool. |
| Envpool import fails on platform-specific GUI/Qt/procgen symbols | Envpool optional submodule import side effect. | Use a known-good envpool build for the platform. If the workflow stubs unused procgen modules, keep the stub before importing envpool. |
| `ale_py` or `gymnasium` cannot create Atari env | Atari dependencies or ROMs are unavailable. | Install Gymnasium Atari extras and accept/import ROMs according to your environment policy. The bundled smoke script intentionally does not require ROMs. |
| `cv2` missing | Cell-key resizing or frame preprocessing dependency absent. | Install OpenCV headless for exact cell-key resizing. The smoke script can still run a fallback cell-key invariant check unless strict exactness is required. |
| W&B prompts for login or touches network | Optional external logging enabled. | Omit the W&B flag for local/offline runs; rely on `metrics.jsonl`, checkpoints, and `final.json`. |
| Display/window error on a server | Human render/test path opened without a display. | Do not render for training. Use non-rendering envpool/CPU smoke checks or set up a virtual display only for explicit human replay. |

## PPO+RND failures

| Error/symptom | Likely cause | Fix/check |
| --- | --- | --- |
| Intrinsic reward is zero or near-zero from the first update | RND predictor learned target too fast; predictor update proportion too high; RND input not normalized correctly. | Verify single-frame RND input, observation RMS warmup, clip to `[-5, 5]`, and a small predictor update proportion. |
| Intrinsic reward explodes or NaNs | Observation RMS not seeded, bad normalization shape, or int-return RMS not updated as scale-only std. | Seed observation RMS with random rollouts; confirm `obs_rms` shape `(84,84)` and int-return RMS variance is positive/finite. |
| Resume changes learning behavior sharply | Checkpoint omitted RMS/filter/optimizer state. | Require actor-critic, predictor, target, optimizer, `obs_rms`, `int_ret_rms`, `int_filter`, update counter, and recent returns in checkpoints. |
| Score stays at zero for a small local run | Sparse-reward scale issue, not necessarily a bug. | Treat small `n_envs` or short `total_frames` as plumbing only. Increase parallelism/budget for first-key discovery. |
| Entropy collapses before reward discovery | Exploration too weak or training too aggressive. | Inspect entropy coefficient, predictor update speed, learning rate, and advantage scaling. |
| Losses become NaN | PPO instability or invalid observations/rewards. | Stop/resume from earlier checkpoint, lower LR, check normalized observations, ensure rewards and advantages are finite, inspect `nan_flag`. |

## Go-Explore Phase 1 failures

| Error/symptom | Likely cause | Fix/check |
| --- | --- | --- |
| Archive cells do not grow beyond root | Cell key computed from stale post-restore read, worker not stepping, or deterministic env not initialized correctly. | Compute keys only from frames returned by `step`; confirm sticky is off and raw ALE env is unwrapped. |
| Replay verification mismatch during demo extraction | Experience-log trajectory is inconsistent with archived DONE score, chunks missing, or protocol changed. | Do not write/use the demo. Keep checkpoint and `explog/` together; replay with deterministic frameskip 4, sticky 0, seed 0. |
| `DONE` cell absent | Phase 1 has not found an end-of-episode trajectory. | Continue Phase 1 or lower expectations; `max_archive_score` alone is not a demo-ready final score. |
| Missing experience-log chunk after resume/copy | Checkpoint references flushed chunks not present in current run directory. | Restore/copy the original `explog/` chunks or preserve ancestor chunk path during resume. |
| Reported best score changes after resume | RNG/archive/log state not fully restored or old cell capture was stitched to a new prefix. | Restore RNG and archive counters; ensure sampled cell captures are immutable per batch. |
| Cell key length is not 88 bytes | Resize/quantization implementation changed. | Resize grayscale frame to `11x8` and quantize to values `0..8`; 88 bytes exactly. |

## Demo pickle problems

| Error/symptom | Likely cause | Fix/check |
| --- | --- | --- |
| Missing key such as `returns` or `checkpoint_action_nr` | Demo was not extracted with the expected schema. | Re-extract or repair only if you can prove the deterministic replay. Validate with `python scripts/hard_atari_smoke.py --section demo --demo path/to/demo.pkl`. |
| `len(actions) != len(rewards)` | Corrupt or truncated demo. | Reject the demo. Robustification needs aligned actions and raw rewards. |
| `returns` differs from `cumsum(rewards)` | Demo return bookkeeping inconsistent. | Reject or regenerate. Curriculum success relies on return-to-here values. |
| `score` differs from `sum(rewards)` | Extraction truncation or write corruption. | Reject or regenerate; do not train on ambiguous score. |
| Checkpoint indices are unsorted or outside action range | Invalid restore table. | Regenerate with periodic checkpoints whose action indices lie in `[0, len(actions))`. |
| Protocol says sticky is nonzero | This is not a deterministic Phase 1 demo. | Do not use it as a Go-Explore robustification demo unless the robustification wrapper is deliberately redesigned for that source. |

## Robustification failures

| Error/symptom | Likely cause | Fix/check |
| --- | --- | --- |
| `curriculum_progress` stalls around a low fraction | Single-machine scale ceiling, weak policy entropy, difficult/long demo, or too few reset envs. | Try a shorter first-reward demo, more envs, longer budget, adjusted entropy, or staged demos. Do not treat Phase 1 score as from-reset success. |
| Success near demo end is always zero | Demo schema invalid, score comparison impossible, sticky filter too hard, or recurrent state not warmed/masked correctly. | Validate demo, inspect `returns`, reduce demo horizon for bootstrap, and check reset wrapper bookkeeping. |
| Eval score is zero despite progress during training | Final evaluation still uses lag/success curriculum kills or does not start from reset. | Turn off training-curriculum kills for eval; set starting point to reset and use game-over/time-cap termination. |
| Resume restarts curriculum from the end | Reset manager state was not saved/restored. | Check checkpoint for `max_starting_point`, success statistics, RNG states, and per-env RNG states. |
| GRU hidden state carries across episode boundaries | Done mask not applied. | Reset/mask recurrent hidden state on done and during unroll. |
| Artificial success cutoffs leak into GAE | `random_reset`/success-reset mask ignored. | Mask advantage and loss across curriculum/artificial reset boundaries. |

## Smoke script troubleshooting

| Error/symptom | Meaning | Action |
| --- | --- | --- |
| Torch missing while running `--section rnd` or `--section robustify` | Model shape checks need PyTorch. | Install PyTorch or run data-only sections such as `--section go-explore`, `--section demo`, or `--section final-json`. |
| Demo validation fails | Pickle is malformed or internally inconsistent. | Fix by re-extracting from a replay-verified Phase 1 run; do not patch values by guesswork. |
| All smoke checks pass but real run fails creating env | Smoke deliberately avoids ROM/envpool/ALE execution. | Debug dependency/ROM/protocol setup separately. Passing smoke proves only self-contained contract invariants. |
| Smoke check passes but benchmark score is poor | Smoke is not a benchmark. | Increase budget/parallelism or debug metrics; do not infer learning performance from smoke. |

## Do not paper over these issues

- Do not compare deterministic search and sticky-action RL scores without a protocol caveat.
- Do not use a demo pickle that fails schema or replay-score validation.
- Do not resume PPO+RND without normalizer state.
- Do not move a Go-Explore checkpoint without its experience-log chunks.
- Do not compute a cell key immediately after `restoreState` before a real action.
- Do not report robustification curriculum progress as a from-reset policy score.
