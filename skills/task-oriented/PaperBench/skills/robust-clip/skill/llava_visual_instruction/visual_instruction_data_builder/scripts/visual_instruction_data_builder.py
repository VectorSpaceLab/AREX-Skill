import json

VALID_TYPES = {"conversation", "detail", "reasoning"}

def build_instruction_item(image_id, captions, boxes, response_type="conversation", question=None, answer=None, resource_files=None):
    if response_type not in VALID_TYPES:
        raise ValueError("unknown response_type")
    if not captions:
        raise ValueError("captions are required")
    if not boxes:
        raise ValueError("boxes are required")
    labels = [box["label"] for box in boxes if box.get("label")]
    if not labels:
        raise ValueError("at least one labeled box is required")
    context = {"captions": list(captions), "boxes": boxes, "objects": labels}
    if question is None:
        if response_type == "detail":
            question = "Describe the image in detail using the visible evidence."
        elif response_type == "reasoning":
            question = f"What can be inferred from the relationship among {', '.join(labels[:3])}?"
        else:
            question = f"What objects are visible in image {image_id}?"
    if answer is None:
        answer = f"The image evidence mentions {', '.join(labels)} and captions: {'; '.join(captions)}."
    return {
        "image_id": image_id,
        "response_type": response_type,
        "symbolic_context": context,
        "human_prompt": question,
        "assistant_answer": answer,
        "is_resource_derived": bool(resource_files),
        "resource_files": resource_files or []
    }

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()
    item = build_instruction_item("proxy-001", ["A child studies a plant diagram."], [{"label":"plant","bbox":[0.1,0.2,0.6,0.8]}], "reasoning")
    open(args.output, "w", encoding="utf-8").write(json.dumps(item, indent=2))
