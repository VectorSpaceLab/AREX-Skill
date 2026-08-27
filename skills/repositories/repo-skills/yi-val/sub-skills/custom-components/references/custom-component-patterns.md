# Custom component patterns

## Reader

Implement `read(self, path) -> Iterator[List[InputData]]`.

```python
from dataclasses import dataclass
from typing import Iterator, List

from yival.data.base_reader import BaseReader
from yival.schemas.common_structures import InputData
from yival.schemas.reader_configs import BaseReaderConfig


@dataclass
class JsonlReaderConfig(BaseReaderConfig):
    text_key: str = "text"


class JsonlReader(BaseReader):
    default_config = JsonlReaderConfig()

    def __init__(self, config: JsonlReaderConfig):
        super().__init__(config)
        self.config = config

    def read(self, path: str) -> Iterator[List[InputData]]:
        # Yield chunks of InputData.
        yield []
```

## Wrapper

Subclass `BaseWrapper` and use `get_variation()` to return the active value.

```python
from dataclasses import dataclass
from yival.schemas.wrapper_configs import BaseWrapperConfig
from yival.wrappers.base_wrapper import BaseWrapper


@dataclass
class NumberWrapperConfig(BaseWrapperConfig):
    pass


class NumberWrapper(BaseWrapper):
    default_config = NumberWrapperConfig()

    def get_value(self):
        variation = self.get_variation()
        return variation if variation is not None else 0
```

## Evaluator

Implement `evaluate(self, experiment_result) -> EvaluatorOutput`.

```python
from dataclasses import dataclass, field
from typing import List

from yival.evaluators.base_evaluator import BaseEvaluator
from yival.schemas.evaluator_config import BaseEvaluatorConfig, EvaluatorOutput, EvaluatorType, MetricCalculatorConfig


@dataclass
class SimpleEvaluatorConfig(BaseEvaluatorConfig):
    metric_calculators: List[MetricCalculatorConfig] = field(default_factory=list)
    evaluator_type = EvaluatorType.INDIVIDUAL


class SimpleEvaluator(BaseEvaluator):
    default_config = SimpleEvaluatorConfig(name="simple_evaluator", evaluator_type=EvaluatorType.INDIVIDUAL)

    def evaluate(self, experiment_result):
        return EvaluatorOutput(name="simple_evaluator", result=1, metric_calculators=self.config.metric_calculators)
```

## Data generator

Implement `generate_examples(self) -> Iterator[List[InputData]]`.

```python
from dataclasses import dataclass, field
from typing import Iterator, List

from yival.data_generators.base_data_generator import BaseDataGenerator
from yival.schemas.common_structures import InputData
from yival.schemas.data_generator_configs import BaseDataGeneratorConfig


@dataclass
class ListDataGeneratorConfig(BaseDataGeneratorConfig):
    items: List[str] = field(default_factory=list)


class ListDataGenerator(BaseDataGenerator):
    default_config = ListDataGeneratorConfig()

    def generate_examples(self) -> Iterator[List[InputData]]:
        yield [InputData(content={"text": item}) for item in self.config.items]
```

## Variation generator

Implement `generate_variations(self) -> Iterator[List[WrapperVariation]]`.

```python
from dataclasses import dataclass, field
from typing import Iterator, List

from yival.schemas.experiment_config import WrapperVariation
from yival.schemas.varation_generator_configs import BaseVariationGeneratorConfig
from yival.variation_generators.base_variation_generator import BaseVariationGenerator


@dataclass
class StaticVariationConfig(BaseVariationGeneratorConfig):
    values: List[str] = field(default_factory=list)


class StaticVariationGenerator(BaseVariationGenerator):
    default_config = StaticVariationConfig()

    def generate_variations(self) -> Iterator[List[WrapperVariation]]:
        yield [WrapperVariation(value_type="str", value=value) for value in self.config.values]
```

## Selection strategy

Implement `select(self, experiment) -> SelectionOutput`.

## Enhancer

Implement `enhance(self, experiment, config, evaluator, token_logger) -> EnhancerOutput`.

For selectors and enhancers, start by adapting the built-in AHP or enhancer interfaces; they depend on the full aggregated `Experiment` object.
