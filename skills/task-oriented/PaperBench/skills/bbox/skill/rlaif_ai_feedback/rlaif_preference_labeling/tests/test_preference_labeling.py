from preference_labeling import HeuristicLabeler, build_prompt, label_pair, stable_softmax
import importlib.util
from pathlib import Path


def test_softmax_normalizes_and_orders_values():
    probs = stable_softmax([0.0, 2.0])
    assert abs(sum(probs) - 1.0) < 1e-9
    assert probs[1] > probs[0]


def test_swapped_order_remaps_to_original_responses():
    labeler = HeuristicLabeler(position_bias=4.0)
    context = "alpha beta gamma delta"
    result = label_pair(
        "summarization",
        context,
        "alpha beta gamma delta",
        "unrelated",
        labeler,
        mitigate_position_bias=True,
    )
    original_record = result["records"][0]
    swapped_record = result["records"][1]
    assert original_record["probabilities_display_order"][0] > original_record["probabilities_display_order"][1]
    assert swapped_record["swapped"] is True
    assert swapped_record["probabilities_original_order"][0] > swapped_record["probabilities_original_order"][1]
    assert result["preference"][0] > result["preference"][1]


def test_chain_of_thought_rationale_is_prompt_metadata_only():
    result = label_pair(
        "summarization",
        "The original text says a kitten has Giardia.",
        "The kitten has a parasite called Giardia.",
        "The kitten is healthy.",
        HeuristicLabeler(),
        chain_of_thought=True,
    )
    assert result["records"][0]["rationale"]
    assert "Rationale:" in result["records"][0]["prompt"]
    assert "reward" not in result
    assert "policy" not in result


def test_prompt_contains_required_candidate_fields():
    prompt = build_prompt("helpful_dialogue", "Human: hello", "Hi there", "Go away")
    assert "Context -" in prompt
    assert "Response 1 -" in prompt
    assert "Response 2 -" in prompt


def test_script_can_be_loaded_by_exec_module_without_sys_modules_registration():
    script = Path(__file__).resolve().parents[1] / "scripts" / "preference_labeling.py"
    spec = importlib.util.spec_from_file_location("standalone_preference_labeling", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.label_pair(
        "summarization",
        "alpha beta gamma",
        "alpha beta gamma",
        "unrelated",
        module.HeuristicLabeler(),
    )
    assert result["preference"][0] > result["preference"][1]
