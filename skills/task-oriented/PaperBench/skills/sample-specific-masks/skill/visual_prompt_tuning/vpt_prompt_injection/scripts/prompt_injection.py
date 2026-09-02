
def parameter_count(prompt_length, dim, layers=1, deep=False):
    if prompt_length <= 0 or dim <= 0 or layers <= 0: raise ValueError('positive sizes required')
    return prompt_length*dim*(layers if deep else 1)

def prepend_prompts(tokens, prompts):
    if not tokens or not prompts: raise ValueError('tokens and prompts required')
    dim=len(tokens[0])
    if any(len(t)!=dim for t in tokens+prompts): raise ValueError('dimension mismatch')
    return [tokens[0]] + [p[:] for p in prompts] + [t[:] for t in tokens[1:]]

def build_prompted_layers(tokens, prompt_tables, deep=False):
    if deep:
        return [prepend_prompts(tokens, p) for p in prompt_tables]
    first=prepend_prompts(tokens, prompt_tables[0])
    return [first]+[tokens for _ in prompt_tables[1:]]
