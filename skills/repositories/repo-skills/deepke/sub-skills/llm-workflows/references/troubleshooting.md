# DeepKE-LLM troubleshooting

Start with the safe diagnostic:

```bash
python scripts/check_llm_workflow_env.py --workflow <oneke|instructkgc|llmicl|unleashllmre|codekgc|cpm-bee>
```

It checks package imports, CUDA visibility, API variable presence, and optional path existence. It does not load model weights, call an API, download data, or start training.

## API and credentials

| Symptom | Likely cause | Fix direction |
| --- | --- | --- |
| Authentication error from an OpenAI-compatible call | Missing/invalid API key | Set credentials in local environment/client config only; never commit them to skill files or fixtures. |
| Endpoint/model error | `BASE_URL` or `MODEL` does not match a served chat/completions model | Verify the endpoint with a minimal non-DeepKE request before debugging prompts. |
| Response is prose instead of JSON/triples | Prompt lacks strict output contract or model does not follow it | Add explicit schema, examples, and validation; reject unparsable output rather than silently accepting it. |
| Cost or timeout spike | Too many examples, large schema, high max tokens, or long documents | Shorten prompt, split schema, lower max tokens, batch carefully, and ask for budget approval. |

## Local model/GPU problems

- `torch.cuda.is_available()` false means local large-model inference/fine-tuning is not verified. Do not reinterpret that as a successful OneKE/LoRA run.
- Out-of-memory errors are usually addressed by reducing sequence/generation length, batch size, beam count, or using quantization/adapter methods; first confirm the model actually loaded with the intended precision.
- DeepSpeed failures often come from GPU count mismatch, bf16/fp16 incompatibility, bad ZeRO config, or launching with `CUDA_VISIBLE_DEVICES` when the workflow expects a DeepSpeed `--include` argument.
- Missing tokenizer/model files should be solved by providing a local cache/checkpoint path or approving a download. Do not hide network downloads inside a troubleshooting step.

## Dependency conflicts

DeepKE-LLM dependencies can conflict with classic DeepKE, PURE/AllenNLP, ASP/Apex, or older Transformers stacks. Prefer isolated environments.

Common fixes:

1. Create a new environment for the selected LLM workflow.
2. Install only that workflow's requirements plus `deepke` if needed.
3. Run `check_llm_workflow_env.py`.
4. Run a tiny conversion or one-record inference before a full job.

## JSONL and converter failures

| Symptom | Likely cause | Fix direction |
| --- | --- | --- |
| `json.decoder.JSONDecodeError: Extra data` | JSONL was read as a single JSON document | Parse line by line or convert to a JSON array. |
| Converter output lacks `output` in train mode | Source records lack labels or `--output-from-field` points at a missing key | Inspect one source record and choose the correct label field. |
| Empty schema in instructions | Source records lack `schema`, labels cannot infer schema, or `--schema` was omitted | Provide `--schema-field`, `--schema`, or labels that expose entity/relation types. |
| LLM output labels outside schema | Model hallucinated labels or prompt schema is too broad | Reject/normalize only according to a recorded label map; do not silently add labels. |

## Known source-script pitfall

The source `LLMICL/ccks2023_convert.py` contains argument definitions using `str=int` instead of `type=int` for some flags. That raises an argparse `TypeError` before conversion. Do not copy that bug into local adapters; use the bundled scripts or patch the argument definitions deliberately.

The same source helper also uses inconsistent option names in the test converter path (`input_path`/`output_path` versus declared `input_file`/`output_file`). Verify CLI flags before relying on copied scripts.

## Prompt and output quality

- For IE tasks, ask for JSON or another deterministic format; free-form prose is hard to score.
- Keep schemas within context limits and split large schemas deliberately.
- Include negative/no-label examples when the task has many absent labels.
- For data augmentation, mark generated data as synthetic and review a sample before adding it to gold training data.
- For CodeKGC, parse generated Python-like text but do not execute it.

## When to report a block

Report a block instead of retrying when:

- The user requested local OneKE or fine-tuning but no compatible GPU/model checkpoint is available.
- API credentials, endpoint access, or budget are missing for an API workflow.
- Required model/data downloads are disallowed or fail under the current network constraints.
- Dependency conflicts require creating or mutating an environment and the user has not approved that action.
