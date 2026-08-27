# ProTeGi CLI and API Reference

This reference distills the ProTeGi automatic text prompt optimization workflow into reusable operating guidance. Use the bundled command builder first; it validates option names, task layouts, prompt markdown structure, and overwrite risk without importing source code or running provider calls.

```bash
python scripts/protegi_command_builder.py \
  --task ethos \
  --data-dir data/ethos \
  --prompts prompts/ethos.md \
  --out runs/ethos.ucb.out \
  --evaluator ucb \
  --scorer 01 \
  --rounds 6 \
  --beam-size 4
```

The helper prints a shell-quoted command for a prepared ProTeGi run directory. It does not execute the command. If files are not staged yet, use `--path-policy warn` and treat warnings as a staging checklist.

## CLI surface

| Native flag | Supported values or default | Operating meaning |
| --- | --- | --- |
| `--task` | default `ethos`; supported `ethos`, `jailbreak`, `liar`, `ar_sarcasm` | Selects the binary task loader. Unsupported names raise before optimization. |
| `--data_dir` | default `data/ethos` | Directory containing task-specific train/test files. |
| `--prompts` | default `prompts/ethos.md`; comma-separated markdown files | One or more seed prompt candidates. Each file is read in full. |
| `--out` | default `test_out.txt` | Optimization log. The native program removes an existing file at this path before writing. |
| `--max_threads` | default `32` | Worker count for multiprocessing evaluation and scoring. Lower it for small machines or provider rate limits. |
| `--temperature` | default `0.0` | Temperature passed to the binary predictor; some gradient-generation helper calls use their own default. |
| `--optimizer` | default `nl-gradient` | Recorded optimizer label. The implemented optimizer path is `ProTeGi`. |
| `--rounds` | default `6` | Optimization loop runs from round 0 through this value; round 0 is the seed-prompt baseline. |
| `--beam_size` | default `4` | Number of candidates retained after score/sort. |
| `--n_test_exs` | default `400` | Number of held-out examples used for the per-round metric log. |
| `--minibatch_size` | default `64` | Training examples sampled when generating textual gradients. |
| `--n_gradients` | default `4` | Number of textual-gradient batches requested per prompt. |
| `--errors_per_gradient` | default `4` | Misclassified examples included in each gradient prompt. |
| `--gradients_per_error` | default `1` | Feedback reasons requested for each sampled error string. |
| `--steps_per_gradient` | default `1` | Improved task-section rewrites requested per feedback reason. |
| `--mc_samples_per_step` | default `2` | Synonym/variation samples per generated task-section step. |
| `--max_expansion_factor` | default `8` | Maximum expanded candidates kept before scoring. |
| `--engine` | default `chatgpt` | Stored in the run config; do not assume it alone changes the provider implementation. |
| `--evaluator` | default `bf`; supported `bf`, `ucb`, `ucb-e`, `sr`, `s-sr`, `sh` | Candidate-selection/evaluation strategy. |
| `--scorer` | default `01`; supported `01`, `ll` | Cached exact-match correctness or cached log-likelihood scoring. |
| `--eval_rounds` | default `8` | Evaluator rounds for non-brute-force strategies. |
| `--eval_prompts_per_round` | default `8` | Prompt arms sampled per evaluation round. |
| `--samples_per_eval` | default `32` | Data examples scored per sampled prompt batch. |
| `--c` | default `1.0` | UCB exploration coefficient; larger values explore more. |
| `--knn_k` | default `2` | Preserved CLI knob from the static surface; verify local code before relying on it in new logic. |
| `--knn_t` | default `0.993` | Preserved CLI knob from the static surface; normally in `[0, 1]`. |
| `--reject_on_errors` | flag, default false | If too many expanded candidates are generated, filter extra candidates on recent error examples before downsampling. |

The run computes `eval_budget = samples_per_eval * eval_rounds * eval_prompts_per_round`. Successive-rejects and successive-halving strategies are more sensitive to small budgets than brute force.

## Task, evaluator, and scorer names

Task names map to task classes:

- `ethos` -> `EthosBinaryTask`
- `jailbreak` -> `JailbreakBinaryTask`
- `liar` -> `DefaultHFBinaryTask`
- `ar_sarcasm` -> `DefaultHFBinaryTask`

Evaluator names map to evaluator classes:

- `bf` -> `BruteForceEvaluator`
- `ucb` -> `UCBBanditEvaluator` using UCB mode
- `ucb-e` -> `UCBBanditEvaluator` using UCB-E mode
- `sr` -> `SuccessiveRejectsEvaluator`
- `s-sr` -> `SuccessiveRejectsEvaluator` with sampled prompts/data per round
- `sh` -> `SuccessiveHalvingEvaluator`

Scorer names map to scorer classes:

- `01` -> `Cached01Scorer`
- `ll` -> `CachedLogLikelihoodScorer`

## API/class map

- `PromptOptimizer`: abstract optimizer base; requires `expand_candidates(prompts, task, predictor, train_examples)`.
- `ProTeGi`: textual-gradient optimizer. It samples misclassified examples, asks for feedback wrapped in `<START>` and `<END>`, rewrites the prompt task section, adds synonym-style variations, deduplicates candidates, scores them, and keeps the beam.
- `DataProcessor`: abstract data loader/evaluator contract.
- `ClassificationTask`: multiprocessing evaluation loop returning F1, texts, labels, and predictions.
- `BinaryClassificationTask`: binary label string mapping: `0 -> No`, `1 -> Yes`.
- `EthosBinaryTask`: semicolon-CSV hate-speech dataset loader with a fixed train/test split.
- `JailbreakBinaryTask`: TSV loader that joins user-role messages from JSON conversations.
- `DefaultHFBinaryTask`: JSONL loader for records with `text` and integer `label`, used by `liar` and `ar_sarcasm`.
- `GPT4Predictor`: abstract predictor base.
- `BinaryPredictor`: renders a prompt with `{{ text }}`, calls the provider, and maps responses starting with `YES` to label `1` and all other starts to label `0`.
- `Cached01Scorer`: mean 0/1 correctness over prompt/example pairs with caching.
- `CachedLogLikelihoodScorer`: renders prompt plus correct label and scores the final answer token log likelihood.
- `BruteForceEvaluator`: samples a budgeted subset and scores every prompt.
- `UCBBandits`: UCB/UCB-E arm-selection state used by the UCB evaluator.
- `UCBBanditEvaluator`: samples prompt arms, scores sampled data, and updates UCB scores.
- `SuccessiveRejectsEvaluator`: repeatedly rejects the weakest prompt arm until only the beam remains.
- `SuccessiveHalvingEvaluator`: repeatedly scores active prompts and keeps above-average survivors.

## Prompt markdown contract

A seed prompt is a markdown text file divided by level-one headings. The parser takes the first word after `#`, lowercases it, strips punctuation, and uses that as the section key. The optimizer expects a `task` section and replaces only that section when generating candidate prompts. The predictor expects a Liquid-style `{{ text }}` placeholder so each example can be rendered.

Minimal pattern:

```markdown
# Task
Describe the binary decision the model should make.

# Output format
Answer Yes or No as labels.

# Prediction
Text: {{ text }}
Label:
```

Prompt checks before spending budget:

- Keep label semantics compatible with `No`/`Yes`.
- Put the editable instruction under `# Task`; do not rename it unless you change the optimizer code.
- Keep the example placeholder exactly `{{ text }}` for the native renderer.
- When passing multiple prompts, use a comma-separated list and verify all prompts share task semantics and labels.

## Task data layouts

| Task | Required files under `data_dir` | Record shape |
| --- | --- | --- |
| `ethos` | `ethos_ishate_binary_shuf.csv` | Semicolon-separated rows without a header. Text is column 0 and numeric hate-speech score is column 1. Rows with clear negative/positive scores are kept; first 200 become test and the rest train. |
| `jailbreak` | `train.tsv`, `test.tsv` | Each line is a JSON conversation, a tab, and an integer label. User-role messages are concatenated into example text. |
| `liar` | `train.jsonl`, `test.jsonl` | Each JSON line contains at least `text` and integer `label`. |
| `ar_sarcasm` | `train.jsonl`, `test.jsonl` | Same default JSONL binary layout as `liar`. |

For a new binary classification dataset, the safest no-code path is to stage `train.jsonl` and `test.jsonl` in the default JSONL shape and choose one of the default-loader task names only if the semantics are acceptable for the experiment. If a new task name or new label mapping is required, plan a source-code extension before running optimization.

## Output interpretation

The optimization log begins with a JSON configuration line, then records each round with elapsed time, current candidate prompt texts, estimated scores, and held-out metrics. Higher scores are better. Round 0 is the seed-prompt baseline; later rounds include expanded candidates from textual gradients and synonym-like sampling.

Before a real run, confirm provider credentials, provider/network budget, task data, prompt layout, and output overwrite behavior. For failure modes, see `references/troubleshooting.md`.
