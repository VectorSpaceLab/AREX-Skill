#!/usr/bin/env python3
"""Run deterministic ChatterBot logic adapter demos without provider calls."""
from __future__ import annotations

import argparse
import json


def run_math_time() -> dict:
    from chatterbot import ChatBot

    bot = ChatBot(
        "Math Time Demo",
        database_uri=None,
        logic_adapters=["chatterbot.logic.MathematicalEvaluation", "chatterbot.logic.TimeLogicAdapter"],
    )
    math_response = bot.get_response("What is 4 + 9?")
    time_response = bot.get_response("What time is it?")
    return {"math": {"text": math_response.text, "confidence": math_response.confidence}, "time": {"text": time_response.text, "confidence": time_response.confidence}}


def run_specific_default() -> dict:
    from chatterbot import ChatBot
    from chatterbot.trainers import ListTrainer

    specific = ChatBot(
        "Specific Demo",
        database_uri=None,
        logic_adapters=[
            {"import_path": "chatterbot.logic.BestMatch"},
            {"import_path": "chatterbot.logic.SpecificResponseAdapter", "input_text": "Help me!", "output_text": "Open the guide."},
        ],
    )
    exact = specific.get_response("Help me!")

    default_bot = ChatBot(
        "Default Demo",
        database_uri=None,
        logic_adapters=[{"import_path": "chatterbot.logic.BestMatch", "default_response": "I do not understand.", "maximum_similarity_threshold": 0.90}],
    )
    ListTrainer(default_bot, show_training_progress=False).train(["How can I help you?", "Read the docs."])
    fallback = default_bot.get_response("How do I make pancakes?")
    return {"specific": {"text": exact.text, "confidence": exact.confidence}, "default": {"text": fallback.text, "confidence": fallback.confidence}}


def run_unit() -> dict:
    try:
        from chatterbot import ChatBot
        from chatterbot.logic import UnitConversion
        from chatterbot.conversation import Statement
    except Exception as exc:
        return {"ok": False, "error": f"import failed: {exc.__class__.__name__}: {exc}"}

    try:
        bot = ChatBot("Unit Demo", database_uri=None, logic_adapters=["chatterbot.logic.UnitConversion"])
        adapter = UnitConversion(bot)
        response = adapter.process(Statement(text="How many meters are in one kilometer?"))
        return {"ok": True, "text": response.text, "confidence": response.confidence}
    except Exception as exc:
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}", "hint": "Install pint before using UnitConversion."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe ChatterBot logic adapter smoke demos.")
    parser.add_argument("--mode", choices=["math-time", "specific-default", "unit", "all"], default="all")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = {}
    if args.mode in {"math-time", "all"}:
        result["math_time"] = run_math_time()
    if args.mode in {"specific-default", "all"}:
        result["specific_default"] = run_specific_default()
    if args.mode in {"unit", "all"}:
        result["unit"] = run_unit()

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    if result.get("unit", {}).get("ok") is False and args.mode == "unit":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
