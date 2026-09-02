def format_llava_prompt(item, image_token="<image>", include_answer=False):
    question = item.get("human_prompt", "").strip()
    answer = item.get("assistant_answer", "").strip()
    if not question:
        raise ValueError("human_prompt is required")
    user_prompt = f"### Human: {image_token}\n{question}\n### Assistant:"
    result = {"user_prompt": user_prompt, "answer_withheld_from_user": answer not in user_prompt}
    if include_answer:
        result["training_prompt"] = f"{user_prompt} {answer}"
    return result
