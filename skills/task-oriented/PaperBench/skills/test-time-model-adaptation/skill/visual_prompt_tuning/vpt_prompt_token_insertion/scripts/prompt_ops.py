#!/usr/bin/env python3
import argparse
import json


def _shape_3d(values, name):
    if not isinstance(values, list) or not values or not isinstance(values[0], list) or not values[0]:
        raise ValueError(f"{name} must be a non-empty 3D list")
    batch = len(values)
    length = len(values[0])
    hidden = len(values[0][0])
    for sample in values:
        if len(sample) != length:
            raise ValueError(f"{name} has ragged sequence length")
        for token in sample:
            if len(token) != hidden:
                raise ValueError(f"{name} has ragged hidden size")
    return batch, length, hidden


def _shape_2d(values, name):
    if not isinstance(values, list) or not values or not isinstance(values[0], list) or not values[0]:
        raise ValueError(f"{name} must be a non-empty 2D list")
    rows = len(values)
    hidden = len(values[0])
    for row in values:
        if len(row) != hidden:
            raise ValueError(f"{name} has ragged hidden size")
    return rows, hidden


def prepend_prompts(tokens, prompts, location="prepend"):
    if location != "prepend":
        raise ValueError("VPT default skill only supports prepend prompts")
    batch, length, hidden = _shape_3d(tokens, "tokens")
    prompt_count, prompt_hidden = _shape_2d(prompts, "prompts")
    if length < 2:
        raise ValueError("tokens must contain CLS and at least one image token")
    if prompt_hidden != hidden:
        raise ValueError("prompt hidden size must match token hidden size")
    output = []
    for sample in tokens:
        output.append([sample[0]] + [p[:] for p in prompts] + [token[:] for token in sample[1:]])
    return {
        "tokens": output,
        "metadata": {"batch": batch, "prompt_count": prompt_count, "hidden_size": hidden, "location": location},
    }


def replace_deep_prompts(prompted_tokens, layer_prompts, layer_index):
    batch, length, hidden = _shape_3d(prompted_tokens, "prompted_tokens")
    if not isinstance(layer_prompts, list) or not layer_prompts:
        raise ValueError("layer_prompts must be a non-empty 3D list")
    if not (0 <= layer_index < len(layer_prompts)):
        raise ValueError("layer_index out of range")
    prompt_count, prompt_hidden = _shape_2d(layer_prompts[layer_index], "layer_prompts[layer_index]")
    if prompt_hidden != hidden:
        raise ValueError("deep prompt hidden size must match token hidden size")
    if length <= 1 + prompt_count:
        raise ValueError("prompted_tokens do not contain image tokens after prompt slots")
    output = []
    for sample in prompted_tokens:
        output.append([sample[0]] + [p[:] for p in layer_prompts[layer_index]] + [token[:] for token in sample[1 + prompt_count:]])
    return {"tokens": output, "metadata": {"batch": batch, "layer_index": layer_index, "prompt_count": prompt_count}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--deep-layer", type=int, default=None)
    args = parser.parse_args()
    payload = json.loads(open(args.input_json, encoding="utf-8").read())
    result = prepend_prompts(payload["tokens"], payload["prompts"], payload.get("location", "prepend"))
    if args.deep_layer is not None:
        result = replace_deep_prompts(result["tokens"], payload["layer_prompts"], args.deep_layer)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
