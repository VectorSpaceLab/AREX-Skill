#!/usr/bin/env python3
"""No-network smoke for YiVal string_expected_result evaluator and AHP selection."""

from __future__ import annotations

import json

from yival.evaluators.string_expected_result_evaluator import StringExpectedResultEvaluator
from yival.result_selectors.ahp_selection import AHPSelection
from yival.schemas.common_structures import InputData
from yival.schemas.evaluator_config import ExpectedResultEvaluatorConfig, MatchingTechnique, MethodCalculationMethod, MetricCalculatorConfig, EvaluatorOutput
from yival.schemas.experiment_config import CombinationAggregatedMetrics, Experiment, ExperimentResult, MultimodalOutput
from yival.schemas.selector_strategies import AHPConfig


def main() -> int:
    metric_calculators = [MetricCalculatorConfig(MethodCalculationMethod.AVERAGE)]
    evaluator = StringExpectedResultEvaluator(
        ExpectedResultEvaluatorConfig(
            name="string_expected_result",
            evaluator_type="individual",  # dataclass accepts the string used by YAML paths
            matching_technique=MatchingTechnique.INCLUDES,
            metric_calculators=metric_calculators,
        )
    )
    input_data = InputData(content={"question": "What is 2+2?"}, expected_result="4")
    result = ExperimentResult(
        input_data=input_data,
        combination={"answer_style": "short"},
        raw_output=MultimodalOutput(text_output="4"),
        latency=0.01,
        token_usage=1,
        evaluator_outputs=[],
    )
    evaluator_output = evaluator.evaluate(result)

    experiment = Experiment(
        combination_aggregated_metrics=[
            CombinationAggregatedMetrics(
                combo_key='{"answer_style": "short"}',
                experiment_results=[result],
                aggregated_metrics={},
                average_token_usage=1,
                average_latency=0.01,
                combine_evaluator_outputs=[EvaluatorOutput(name="string_expected_result: matching", result=evaluator_output.result)],
            ),
            CombinationAggregatedMetrics(
                combo_key='{"answer_style": "long"}',
                experiment_results=[],
                aggregated_metrics={},
                average_token_usage=100,
                average_latency=10.0,
                combine_evaluator_outputs=[EvaluatorOutput(name="string_expected_result: matching", result=1)],
            ),
        ],
        group_experiment_results=[],
    )
    selector = AHPSelection(
        AHPConfig(
            criteria=["string_expected_result: matching", "average_token_usage", "average_latency"],
            criteria_weights={"string_expected_result: matching": 0.8, "average_token_usage": 0.1, "average_latency": 0.1},
            criteria_maximization={"string_expected_result: matching": True, "average_token_usage": False, "average_latency": False},
            normalize_func=None,
        )
    )
    selection = selector.select(experiment)
    print(json.dumps({
        "evaluator_output": evaluator_output.asdict(),
        "selection": selection.__dict__,
    }, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
