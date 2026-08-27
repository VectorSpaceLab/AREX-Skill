# DeepKE-LLM workflows

This reference distills DeepKE's large-language-model knowledge extraction examples into workflow-selection guidance. It is self-contained and deliberately conservative about GPU/API cost.

## Scenario decision table

| User intent | Choose | Required resources | Why |
| --- | --- | --- | --- |
| Schema-based bilingual IE with a released DeepKE large model | OneKE | Local OneKE-compatible checkpoint/cache, GPU memory for the selected model, tokenizer assets | OneKE is the most direct schema-driven DeepKE-LLM path for NER/RE/EE-style extraction without writing a custom prompt pipeline. |
| Fine-tune a model for CCKS/instruction KGC with LoRA, P-tuning, or OpenDelta | InstructKGC | Instruction JSONL, base model weights, PEFT/OpenDelta stack, GPU(s), output directory | InstructKGC owns most supervised instruction-tuning workflows for LLaMA/ZhiXi, ChatGLM, MOSS, Baichuan, Qwen, CPM-Bee, and related models. |
| Call GPT/OpenAI-compatible models for IE, data augmentation, or CCKS KGC | LLMICL / API workflows | API key, base URL, model name, prompt templates, budget/network approval | Use when the model is remote and the task is prompt/in-context rather than local fine-tuning. |
| Few-shot relation extraction with LLM prompting/data augmentation | UnleashLLMRE | API or local LLM, few-shot relation examples, relation label definitions | Use when the problem is relation extraction with few labeled examples and the user wants prompt/LLM augmentation guidance. |
| Represent triples as Python-like code prompts for code LLMs | CodeKGC | Schema prompt, in-context examples, test examples, OpenAI-compatible code model or local code LLM | Use when the user explicitly asks for code-style triple prompts or the data already follows CodeKGC files. |
| Fine-tune CPM-Bee through DeepKE's OpenDelta-style path | CPM-Bee | CPM-Bee model assets, OpenDelta/fine-tuning stack, GPU | Use for tasks tied to CPM-Bee; dependency and model assumptions differ from LLaMA/ChatGLM workflows. |

## Universal preflight checklist

1. Identify whether the task is conversion, inference, fine-tuning, evaluation, or debugging.
2. Determine local vs remote model execution. Local models need checkpoint/cache paths and GPU memory; remote workflows need credentials and a cost budget.
3. Run `python scripts/check_llm_workflow_env.py --workflow <workflow>` to inspect packages and environment variables without loading models.
4. Validate instruction data with [data-formats.md](data-formats.md). Most converters emit JSONL; do not parse the result with `json.load()` unless it is explicitly a JSON array.
5. For fine-tuning, keep `output_dir`, adapter directory, logging directory, and checkpoint paths unique.
6. For API prompting, never store API keys in shared config, skill files, or fixtures.

## OneKE planning recipe

Use OneKE when the user wants schema-constrained bilingual extraction from text and can provide the model runtime.

1. **Task/schema**: decide entity types, relation types, event types, or other schema labels up front.
2. **Instruction/input**: each request should specify the task instruction, schema list, and input text. The model is not a replacement for schema design.
3. **Runtime**: verify tokenizer/model checkpoint availability and GPU memory before loading. A CPU import check does not prove OneKE inference readiness.
4. **Output validation**: require JSON-like output or a clearly parseable text format. Report hallucinated labels or labels outside the schema.
5. **Batching**: start with a tiny batch and max-generation length appropriate to expected extracted content.

## InstructKGC conversion and tuning recipe

Use this when the user has labeled IE/KG data and wants instruction-form records or LoRA/P-tuning/OpenDelta fine-tuning.

1. **Prepare source records**: source data typically contains raw `text` and one task-specific label field such as entities, relations, events, SPO triples, or KG triples.
2. **Prepare schema**: keep schemas small enough for prompts. DeepKE's source converter can split large schemas into multiple instructions; the bundled converter offers a simple standalone path for common NER/RE/SPO records.
3. **Convert**:

   ```bash
   python scripts/convert_ie_instruction.py \
     --input data/sample.jsonl \
     --output data/instructions.jsonl \
     --task RE \
     --language en \
     --source my-dataset \
     --mode train
   ```

4. **Fine-tune**: select the model family and method deliberately. LoRA/P-tuning/OpenDelta settings are not interchangeable across LLaMA, ChatGLM, MOSS, Baichuan, Qwen, and CPM-Bee.
5. **Evaluate**: parse model output back into the task schema and compare with gold labels. Do not compare raw natural language strings alone.

## LLMICL/API workflow recipe

Use this when the task depends on a remote or OpenAI-compatible LLM.

1. Confirm API endpoint, model name, timeout, max tokens, temperature, and budget.
2. Create a prompt with task instruction, schema, extraction examples, and the target text.
3. Ask for strict JSON or a task-specific parseable format, then validate the response.
4. For data augmentation, keep generated examples separate from gold labels and mark them as synthetic until reviewed.
5. For CCKS-style triples, post-process generated triple text and inspect empty/invalid rows before evaluation.

## UnleashLLMRE recipe

Use this when the user wants few-shot relation extraction with LLMs.

1. Define relation labels and natural-language definitions.
2. Select representative few-shot examples per relation, including a no-relation/other class when appropriate.
3. Build prompts that include head/tail entity markers and ask for exactly one relation label or a structured output.
4. If using generated augmentation, review label balance and leakage before adding examples to training.
5. Evaluate on held-out examples with label-normalization rules recorded.

## CodeKGC recipe

Use this when the user explicitly wants code-style prompts for relational triple extraction.

1. **Schema prompt**: define Python-like classes for relations, entities, triples, and the `Extract` container.
2. **ICL prompt**: write examples as docstring text followed by `extract = Extract([...])` statements.
3. **Test example**: append the target text docstring and let the code model generate an `Extract` statement.
4. **Parsing**: execute nothing from untrusted model output. Parse the generated structure as text or with a restricted AST parser in a controlled local tool.
5. **Validation**: relation/entity class names must match the schema prompt; reject arbitrary imports, function calls, or code outside the extraction statement.

## CPM-Bee recipe

Use CPM-Bee only when the user selected that model family or inherited CPM-Bee checkpoints/data.

1. Prepare a separate environment from classic DeepKE if dependencies conflict.
2. Confirm model/tokenizer assets and OpenDelta/fine-tuning dependencies.
3. Start with a tiny conversion and inference/fine-tuning dry run before a full job.
4. Record adapter output paths and base model revision for reproducibility.

## What safe generated-skill checks can prove

The bundled diagnostics and converters can prove that data is syntactically shaped, required packages appear installed, API variables are present, CUDA is visible, and model/checkpoint paths exist. They do **not** prove that a local 13B model fits in memory, a remote API will answer, LoRA training converges, or OneKE outputs are high quality. Preserve those as runtime requirements in task reports.
