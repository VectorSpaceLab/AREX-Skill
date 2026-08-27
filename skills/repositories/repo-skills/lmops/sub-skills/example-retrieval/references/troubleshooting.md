# Troubleshooting

Use this reference when a retrieval-family plan looks correct on paper but fails on credentials, paths, dependencies, or hardware.

If the root `lmops` skill is available, also consult `../../../references/troubleshooting.md` for shared install, credential, hardware, and output-root guidance.

## Credential and access problems

### Hugging Face downloads fail

Typical causes:

- The task bundle or model is gated.
- The cache directory is not writable.
- The environment has no network access.

Checks:

- Confirm the model or dataset name is valid before blaming the workflow.
- Confirm the cache directory is staged and writable.
- Confirm the user really wants a download-heavy run and not just a command plan.

### OpenAI inference fails

Typical causes:

- No token in the environment.
- The selected model/engine is not compatible with the local inference helper.
- The HF prediction file that OpenAI mode expects has not been created yet.

Checks:

- Re-read the UPRISE flow: OpenAI inference reuses a prior prediction file from the HF path.
- Keep the token external. Do not write it into scripts or generated plan files.
- If you are not sure whether a chat model is supported, treat the plan as a concept only and do not claim a verified run.

## Task / metric mismatch

This is the most common logic error in UPRISE and SE2 planning.

Symptoms:

- The validator says the metric does not match the task.
- A task-class extension was added but the downstream metric name is missing or misspelled.
- The user mixed a classification task with a text-completion metric, or vice versa.

Checks:

- Confirm the metric family: `simple_accuracy`, `acc_and_f1`, `f1`, `rouge`, `squad`, `trivia_qa`, or `pubmed_qa_acc`.
- Confirm the task type: multiple-choice tasks use option lists; text-completion tasks use `class_num = 1`.
- For inherited aliases such as `mnli_m`, `mnli_mm`, or `arc_e`, use the parent task metric and class shape.
- If the task is custom, add it deliberately to the plan and do not assume the built-in map will infer it.

## Checkpoint and prompt-pool path issues

Symptoms:

- The planner looks fine, but inference cannot find the retriever checkpoint.
- The prompt encoder or retriever step cannot find the prompt-pool JSON.
- The score file exists but the generated train/inference step expects a different filename or folder layout.

Checks:

- Verify that the prompt pool, retrieved prompt file, scored-data file, and checkpoint all live under the output tree that the generated command expects.
- For UPRISE, the retriever checkpoint and encoded prompt pool must exist before test-time retrieval.
- For SE2, the final inference stage expects the trained retriever checkpoint folder and the encoded prompt-pool index.
- For LLM Retriever, confirm the JSONL data bundle exists before any search or training stage.
- Be careful with generated experiment directory names; the command generator derives them from cluster strings or task names.

## Heavy GPU and hardware issues

Symptoms:

- CUDA OOM during scorer, retriever training, or sequence scoring.
- A command silently assumes more GPUs than the local machine has.
- A workflow says it is "small" even though the public run used multiple V100-class GPUs.

Checks:

- UPRISE and SE2 scoring/inference can require accelerate or distributed launch settings and a model that fits the selected GPU budget.
- SE2’s public walkthrough notes an eight-V100-32GB class setup.
- LLM Retriever reward scoring and KD training can be memory-heavy and may need sharding or reduced batch sizes.
- Structured Prompting many-shot runs can exceed the context window before they exceed GPU memory.
- If a plan needs a real hardware run, do not claim CPU validation as proof.

## Old dependency stack problems

Symptoms:

- Import errors around old DPR, Fairseq, or transformer APIs.
- The structured-prompting or Understand ICL path fails because the local dependency stack is newer than the public workflow.
- SE2 or UPRISE utilities fail because the vendored DPR stack is incomplete in the current environment.

Checks:

- Treat `uprise` and `se2` as DPR-style stacks with old Hydra / accelerate / transformer assumptions.
- Treat Structured Prompting and Understand ICL as older Fairseq-style stacks.
- Treat CED-ICL as a T-Few-style stack with PEFT and Lightning requirements.
- If the command plan is all you need, stop at planning rather than forcing imports.

## Output-directory confusion

Symptoms:

- A script writes data, but the next stage looks in a different folder.
- The user staged outputs manually, but the generated command still uses the default experiment layout.
- The planner output is correct, but the local checkout has a different subdirectory name.

Checks:

- Keep the staged plan and the generated command templates in sync.
- For UPRISE and SE2, inspect the experiment folder name derived from the train/test cluster strings or task name.
- For LLM Retriever, remember that `OUTPUT_DIR` and `DATA_DIR` are independent.
- For Understand ICL, record outputs and analysis outputs are intentionally separated.

## When to stop and re-plan

Re-plan instead of debugging further when:

- The task/metric plan is incomplete or contradictory.
- The user asks for a run that would require credentials you do not have.
- The prompt pool or checkpoint is missing.
- The hardware requirement is clearly beyond the current environment.
- The user really wants a different workflow family such as prompt optimization or RAG acceleration.
