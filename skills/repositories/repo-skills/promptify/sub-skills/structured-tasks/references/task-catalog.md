# Built-in Task Catalog

## Purpose

Read this when you need to choose the right Promptify task class quickly. It maps the built-in task families to their constructors, output schemas, and most important arguments.

## Task families

| Family | Class | Output schema | Key arguments | Template | Notes |
| --- | --- | --- | --- | --- | --- |
| Named entity recognition | NER | NERResult | domain, labels, examples, instruction | ner | labels and domain are optional and become prompt variables |
| Classification | Classify | Classification or MultiLabelResult | labels, multi_label, domain, examples, instruction | classify_binary, classify_multiclass, classify_multilabel | binary mode is selected when len(labels) == 2 |
| Question answering | QA | Answer | domain, examples, instruction, question on call | qa | call as qa(text, question="...") |
| Summarization | Summarize | Summary | max_length, key_points, domain, instruction | summarize | key_points=True adds a key_points field |
| Relation extraction | ExtractRelations | ExtractionResult | domain, examples, instruction | relation_extraction | returns relations as subject-predicate-object triples |
| Tabular extraction | ExtractTable | ExtractionResult | examples, instruction | tabular_extraction | returns rows as key/value dictionaries |
| Question generation | GenerateQuestions | internal wrapper with questions list | num_questions, domain, instruction | question_generation | returns a model whose questions field holds GeneratedQuestion items |
| SQL generation | GenerateSQL | SQLQuery | schema, examples, instruction | sql_writer | schema text is inserted into the prompt |
| Text normalization | NormalizeText | internal wrapper with normalized_text | rules, examples, instruction | text_normalization | rules are prompt instructions, not validation rules |
| Topic extraction | ExtractTopics | internal wrapper with topics list | num_topics, domain, instruction | topic_modelling | each topic has topic and words fields |
| Custom structured task | Task | any Pydantic BaseModel | output_schema, instruction, kwargs | none | use when no built-in task fits |

## Choosing between them

- Pick NER when the answer is spans with labels.
- Pick Classify when the answer is a single label or a small label set.
- Pick QA when the answer should be extracted from context.
- Pick Summarize when the answer is a summary plus optional key points.
- Pick ExtractRelations or ExtractTable when the answer is structured facts from free text.
- Pick GenerateQuestions or GenerateSQL when the task creates new text, but the output still needs to be structured.
- Pick NormalizeText or ExtractTopics when the output is normalized text or topic clusters.
- Pick Task when the output schema is fully custom.
