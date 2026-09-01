from typing import Dict, Iterable, List


def create_layout(env_count: int, state_keys: Iterable[str]) -> Dict[str, object]:
    if env_count <= 0:
        raise ValueError('env_count must be positive')
    keys = list(state_keys)
    if not keys:
        raise ValueError('state_keys must not be empty')
    states = {key: [0.0 for _ in range(env_count)] for key in keys}
    return {'env_count': env_count, 'state_keys': keys, 'states': states, 'isolation_ok': True}


def validate_layout(layout: Dict[str, object]) -> bool:
    env_count = int(layout['env_count'])
    states = layout['states']
    return env_count > 0 and all(len(values) == env_count for values in states.values())


def apply_resets(layout: Dict[str, object], reset_mask: List[bool], reset_value: float = 0.0) -> Dict[str, object]:
    env_count = int(layout['env_count'])
    if len(reset_mask) != env_count:
        raise ValueError('reset_mask length must match env_count')
    for key, values in layout['states'].items():
        for index, reset in enumerate(reset_mask):
            if reset:
                values[index] = reset_value
    return layout
