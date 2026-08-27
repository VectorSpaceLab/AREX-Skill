# Custom examples

## Custom evaluator YAML

```yaml
custom_evaluators:
  contains_keyword:
    class: my_components.keyword_evaluator.ContainsKeywordEvaluator
    config_cls: my_components.keyword_evaluator.ContainsKeywordConfig

evaluators:
  - name: contains_keyword
    evaluator_type: individual
    keyword: approved
    metric_calculators:
      - method: AVERAGE
```

Evaluator implementation should read `experiment_result.raw_output.text_output` and return `EvaluatorOutput(name="contains_keyword", display_name=..., result=<number>)`.

## Custom reader YAML

```yaml
custom_reader:
  jsonl_reader:
    class: my_components.jsonl_reader.JsonlReader
    config_cls: my_components.jsonl_reader.JsonlReaderConfig

dataset:
  source_type: dataset
  reader: jsonl_reader
  file_path: /absolute/path/to/data.jsonl
  reader_config:
    text_key: prompt
    expected_key: answer
```

Reader output `InputData.content` keys must match the custom function parameters.

## Custom variation generator YAML

```yaml
custom_variation_generators:
  static_prompt_generator:
    class: my_components.static_prompt.StaticPromptGenerator
    config_cls: my_components.static_prompt.StaticPromptConfig

variations:
  - name: task
    generator_name: static_prompt_generator
    generator_config:
      values:
        - "Answer directly: {question}"
        - "Think briefly, then answer: {question}"
```

The generator returns `WrapperVariation(value_type="str", value=<prompt>)` values.

## Custom data generator YAML

```yaml
custom_data_generators:
  static_question_generator:
    class: my_components.static_data.StaticQuestionGenerator
    config_cls: my_components.static_data.StaticQuestionGeneratorConfig

dataset:
  source_type: machine_generated
  data_generators:
    static_question_generator:
      questions:
        - question: What is 2+2?
          expected_result: "4"
```

The data generator returns chunks of `InputData`.

## Custom wrapper usage

YAML registers the wrapper class, but the custom function must instantiate it:

```python
from my_components.number_wrapper import NumberWrapper

def score(item: str, state):
    temperature = NumberWrapper(0.0, name="temperature", state=state).get_value()
```

YAML variation:

```yaml
variations:
  - name: temperature
    variations:
      - value_type: float
        value: 0.0
        instantiated_value: 0.0
      - value_type: float
        value: 0.7
        instantiated_value: 0.7
```
