# Prompt Templates

OpenCompass builds evaluation prompts inside a dataset `infer_cfg`. The central pieces are `ice_template` for in-context examples, `prompt_template` for the test sample prompt, and the model-side `meta_template` for turning dialogue roles into the final model/API input.

## String Templates

A string `PromptTemplate` substitutes sample fields with `safe_format` behavior:

```python
prompt_template = dict(
    type=PromptTemplate,
    template='Question: {question}\nAnswer: {answer}',
)
```

Important behavior:

- Fields present in the sample are substituted.
- Fields missing from the sample remain literal, for example `{missing_field}` stays in the rendered prompt instead of raising `KeyError`.
- In generative inference, the field named by `reader_cfg.output_column` is replaced before rendering to prevent answer leakage.
- `gen_field_replace_token` controls the replacement text for the output field and defaults to an empty string.

If a user sees `Answer:` with no answer, that may be correct masking. If they see `{answer}` literally, the sample likely does not contain an `answer` field or `reader_cfg.output_column` points to a different column than the template uses.

## Dialogue Templates and PromptList

Dialogue-style `PromptTemplate` uses dictionaries with `begin`, `round`, and `end` sections and renders an intermediate `PromptList`:

```python
prompt_template = dict(
    type=PromptTemplate,
    template=dict(
        begin=[
            dict(role='SYSTEM', fallback_role='HUMAN', prompt='Solve carefully.'),
        ],
        round=[
            dict(role='HUMAN', prompt='Question: {question}'),
            dict(role='BOT', prompt='Answer: {answer}'),
        ],
    ),
)
```

Use these conventions:

- `HUMAN` is usually the user/question role.
- `BOT` is usually the model/answer role.
- `SYSTEM` should include `fallback_role='HUMAN'` unless every target model `meta_template` reserves a `SYSTEM` role.
- `begin` and `end` are added for the full prompt, not for each generated in-context example.
- When no model `meta_template` is present, OpenCompass can concatenate `PromptList` content into a plain prompt, but model-specific chat formatting is lost.

Subtle generation behavior: for generative dialogue evaluation, the last `BOT` turn is the role to be generated. Its prompt text, such as `Answer: `, is not always passed as normal user input for API-style models; the model `meta_template` with `generate=True` determines the cutoff. Keep the final `BOT` turn minimal and make any required answer instruction part of the preceding `HUMAN` or `SYSTEM` turn if the backend cannot prefill assistant text.

## In-Context Examples

Few-shot prompting normally uses both templates:

```python
infer_cfg = dict(
    ice_template=dict(
        type=PromptTemplate,
        template='Q: {question}\nA: {answer}',
    ),
    prompt_template=dict(
        type=PromptTemplate,
        template='Answer the questions.\n</E>Q: {question}\nA: {answer}',
        ice_token='</E>',
    ),
    retriever=dict(type=FixKRetriever, fix_id_list=[0, 1]),
    inferencer=dict(type=GenInferencer),
)
```

Rules to remember:

- `ice_token` must appear in a template when the template is expected to insert retrieved examples; otherwise OpenCompass raises a lookup/not-implemented error.
- If `prompt_template` is omitted and `ice_template` has `ice_token`, OpenCompass can reuse `ice_template` as the full prompt template.
- For dialogue templates, generated ICE is a `PromptList` bracketed by internal `section='ice'` markers so the final model parser can distinguish examples from the test turn.
- For string templates, `ice_separator` and `ice_eos_token` on the retriever control how examples are joined.

## PPL Candidate Templates

For `PPLInferencer`, `template` should be a dictionary keyed by candidate labels. The prediction is the label with the lowest perplexity/log-likelihood score.

```python
prompt_template = dict(
    type=PromptTemplate,
    template=dict(
        A='Question: {question}\nA. {A}\nB. {B}\nAnswer: A',
        B='Question: {question}\nA. {A}\nB. {B}\nAnswer: B',
    ),
)
```

Use label-keyed dialogue templates the same way when evaluating chat prompts by PPL. If no candidate-template keys are available, OpenCompass falls back to unique values in the test output column, which is often unstable for free-form answers.

## RawPromptTemplate

`RawPromptTemplate` bypasses `PromptList` conversion and emits OpenAI-compatible messages directly:

```python
prompt_template = dict(
    type=RawPromptTemplate,
    messages=[
        {'role': 'system', 'content': 'You are helpful.'},
        {'role': 'user', 'content': '{problem}'},
        {'role': 'assistant', 'content': ''},
    ],
)
```

Capabilities and limits:

- Valid roles are lowercase `system`, `user`, and `assistant`.
- `{'expand_column': 'history'}` inserts a list of message dictionaries from the sample.
- A string equal to the configured `ice_token` can insert message-list ICE; non-message string ICE is skipped because messages must be dictionaries.
- `format_variables=False` preserves placeholders without substitution.

## Meta Template Role Mapping

Dataset dialogue templates produce role-tagged turns; model `meta_template` maps those roles to final text or API roles.

```python
meta_template = dict(
    round=[
        dict(role='HUMAN', begin='<|user|>\n', end='\n'),
        dict(role='BOT', begin='<|assistant|>\n', end='\n', generate=True),
    ],
    reserved_roles=[
        dict(role='SYSTEM', begin='<|system|>\n', end='\n'),
    ],
)
```

Guidelines:

- Put ordinary conversation roles in `round`.
- Put roles such as `SYSTEM` in `reserved_roles` when they appear in `begin`/`end` but are not part of the alternating round pattern.
- Add `generate=True` to the role the model should complete, usually `BOT`.
- Use `fallback_role` in the dataset prompt when a role may be absent from a model `meta_template`.
- API model meta templates use `api_role` mappings (`HUMAN`, `BOT`, `SYSTEM`) rather than textual `begin`/`end` wrappers.

## Chain-of-Thought Prompting

OpenCompass CoT prompting is usually just prompt text plus a generative inferencer:

- Zero-shot CoT: add wording like `Let's think step by step` to the test prompt.
- Few-shot CoT: include worked reasoning examples before the live `{question}`.
- Self-consistency: switch to an SC-style inferencer and configure sampling; deterministic generation makes multiple samples ineffective.
- Tree-of-thought workflows require task-specific prompt wrappers and are not a simple `PromptTemplate` edit.
