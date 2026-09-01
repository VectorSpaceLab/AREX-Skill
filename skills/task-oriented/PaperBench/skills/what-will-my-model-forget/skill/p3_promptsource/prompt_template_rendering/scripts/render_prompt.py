#!/usr/bin/env python3
import argparse
import json
from typing import Any, Dict, List, Optional

try:
    from jinja2 import Environment, StrictUndefined
except Exception:  # pragma: no cover
    Environment = None
    StrictUndefined = None


def _fallback_render(template: str, context: Dict[str, Any]) -> str:
    import re

    def resolve(expr: str) -> str:
        expr = expr.strip()
        if "[" in expr and expr.endswith("]"):
            base, index_expr = expr[:-1].split("[", 1)
            base_value = context[base.strip()]
            index_value = context[index_expr.strip()]
            return str(base_value[index_value])
        return str(context[expr])

    return re.sub(r"{{\s*(.*?)\s*}}", lambda match: resolve(match.group(1)), template)


def render_prompt(
    example: Dict[str, Any],
    template: str,
    answer_choices: Optional[List[str]] = None,
    choice_index: int = 0,
) -> Dict[str, Any]:
    errors: List[str] = []
    if template.count("|||") != 1:
        return {"ok": False, "input": "", "target": "", "skipped": False, "errors": ["template must contain exactly one ||| separator"]}

    input_template, target_template = template.split("|||", 1)
    context = dict(example)
    if answer_choices is not None:
        context["answer_choices"] = answer_choices

    def choice(options: List[Any]) -> Any:
        if not options:
            raise ValueError("choice() received an empty list")
        return options[choice_index % len(options)]

    try:
        if Environment is not None:
            env = Environment(undefined=StrictUndefined)
            env.globals["choice"] = choice
            rendered_input = env.from_string(input_template).render(**context).strip()
            rendered_target = env.from_string(target_template).render(**context).strip()
        else:
            context["choice"] = choice
            rendered_input = _fallback_render(input_template, context).strip()
            rendered_target = _fallback_render(target_template, context).strip()
    except Exception as exc:
        errors.append(f"rendering failed: {exc}")
        return {"ok": False, "input": "", "target": "", "skipped": False, "errors": errors}

    skipped = rendered_input == "" or rendered_target == ""
    return {"ok": not errors, "input": rendered_input, "target": rendered_target, "skipped": skipped, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a PromptSource-style prompt template.")
    parser.add_argument("--example-json", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--answer-choices-json", default="null")
    parser.add_argument("--choice-index", type=int, default=0)
    args = parser.parse_args()
    result = render_prompt(
        json.loads(args.example_json),
        args.template,
        json.loads(args.answer_choices_json),
        args.choice_index,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
