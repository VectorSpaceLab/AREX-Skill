def render_prompts(class_names, templates):
    if not class_names or not templates:
        raise ValueError("class_names and templates are required")
    rendered = {}
    for name in class_names:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("class names must be non-empty strings")
        rendered[name] = []
        for template in templates:
            if "{}" not in template:
                raise ValueError("templates must contain {} placeholder")
            rendered[name].append(template.format(name))
    return rendered


def validate_pairs(pairs):
    if not pairs:
        raise ValueError("at least one pair is required")
    dim = None
    validated = []
    for pair in pairs:
        for key in ["id", "class_name", "image_embedding", "text_embedding"]:
            if key not in pair:
                raise ValueError(f"missing pair field: {key}")
        image = list(pair["image_embedding"])
        text = list(pair["text_embedding"])
        if not image or len(image) != len(text):
            raise ValueError("image/text embeddings must be same non-zero length")
        if not all(isinstance(x, (int, float)) for x in image + text):
            raise ValueError("embeddings must be numeric")
        if dim is None:
            dim = len(image)
        elif dim != len(image):
            raise ValueError("all embeddings must share one dimension")
        validated.append({**pair, "embedding_dim": dim})
    return validated
