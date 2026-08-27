#!/usr/bin/env python3
"""Write small YiVal custom component skeleton files."""

from __future__ import annotations

import argparse
from pathlib import Path

SKELETONS = {
    "evaluator": '''from dataclasses import dataclass, field
from typing import List

from yival.evaluators.base_evaluator import BaseEvaluator
from yival.schemas.evaluator_config import BaseEvaluatorConfig, EvaluatorOutput, EvaluatorType, MetricCalculatorConfig


@dataclass
class SimpleEvaluatorConfig(BaseEvaluatorConfig):
    keyword: str = "ok"
    metric_calculators: List[MetricCalculatorConfig] = field(default_factory=list)
    evaluator_type = EvaluatorType.INDIVIDUAL


class SimpleEvaluator(BaseEvaluator):
    default_config = SimpleEvaluatorConfig(name="simple_evaluator", evaluator_type=EvaluatorType.INDIVIDUAL)

    def __init__(self, config: SimpleEvaluatorConfig):
        super().__init__(config)
        self.config = config

    def evaluate(self, experiment_result):
        text = experiment_result.raw_output.text_output or ""
        return EvaluatorOutput(
            name=self.config.name,
            display_name="keyword",
            result=1 if self.config.keyword in text else 0,
            metric_calculators=self.config.metric_calculators,
        )
''',
    "reader": '''from dataclasses import dataclass
from typing import Iterator, List
import json

from yival.data.base_reader import BaseReader
from yival.schemas.common_structures import InputData
from yival.schemas.reader_configs import BaseReaderConfig


@dataclass
class JsonlReaderConfig(BaseReaderConfig):
    expected_key: str = "expected_result"


class JsonlReader(BaseReader):
    default_config = JsonlReaderConfig()

    def __init__(self, config: JsonlReaderConfig):
        super().__init__(config)
        self.config = config

    def read(self, path: str) -> Iterator[List[InputData]]:
        chunk: List[InputData] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                expected = row.pop(self.config.expected_key, None)
                chunk.append(InputData(content=row, expected_result=expected))
                if len(chunk) >= self.config.chunk_size:
                    yield chunk
                    chunk = []
        if chunk:
            yield chunk
''',
    "variation-generator": '''from dataclasses import dataclass, field
from typing import Iterator, List

from yival.schemas.experiment_config import WrapperVariation
from yival.schemas.varation_generator_configs import BaseVariationGeneratorConfig
from yival.variation_generators.base_variation_generator import BaseVariationGenerator


@dataclass
class StaticVariationConfig(BaseVariationGeneratorConfig):
    values: List[str] = field(default_factory=list)


class StaticVariationGenerator(BaseVariationGenerator):
    default_config = StaticVariationConfig()

    def __init__(self, config: StaticVariationConfig):
        super().__init__(config)
        self.config = config

    def generate_variations(self) -> Iterator[List[WrapperVariation]]:
        yield [WrapperVariation(value_type="str", value=value) for value in self.config.values]
''',
    "data-generator": '''from dataclasses import dataclass, field
from typing import Iterator, List, Dict

from yival.data_generators.base_data_generator import BaseDataGenerator
from yival.schemas.common_structures import InputData
from yival.schemas.data_generator_configs import BaseDataGeneratorConfig


@dataclass
class StaticDataGeneratorConfig(BaseDataGeneratorConfig):
    rows: List[Dict[str, str]] = field(default_factory=list)
    expected_key: str = "expected_result"


class StaticDataGenerator(BaseDataGenerator):
    default_config = StaticDataGeneratorConfig()

    def __init__(self, config: StaticDataGeneratorConfig):
        super().__init__(config)
        self.config = config

    def generate_examples(self) -> Iterator[List[InputData]]:
        chunk: List[InputData] = []
        for row in self.config.rows:
            row = dict(row)
            expected = row.pop(self.config.expected_key, None)
            chunk.append(InputData(content=row, expected_result=expected))
        yield chunk
''',
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=sorted(SKELETONS), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    filename = args.kind.replace("-", "_") + ".py"
    path = args.output_dir / filename
    path.write_text(SKELETONS[args.kind], encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
