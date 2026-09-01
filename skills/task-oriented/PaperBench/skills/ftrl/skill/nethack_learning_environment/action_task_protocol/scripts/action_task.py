MOVES = {'N': (0,-1), 'S': (0,1), 'E': (1,0), 'W': (-1,0), 'NE': (1,-1), 'NW': (-1,-1), 'SE': (1,1), 'SW': (-1,1)}
COMMANDS = {'EAT', 'OPEN', 'KICK', 'READ', 'PRAY', 'WAIT'}

def valid_actions():
    return sorted(MOVES) + sorted(COMMANDS)

def step_position(obs, action):
    if action not in MOVES:
        return list(obs['agent'])
    dx, dy = MOVES[action]
    nx, ny = obs['agent'][0] + dx, obs['agent'][1] + dy
    rows = obs['raw_rows']
    if ny < 0 or ny >= len(rows) or nx < 0 or nx >= len(rows[0]) or rows[ny][nx] in '|-':
        return list(obs['agent'])
    return [nx, ny]

def staircase_reward(obs, action, new_pos=None, step_penalty=-0.01):
    pos = new_pos if new_pos is not None else step_position(obs, action)
    success = pos in obs.get('stairs', [])
    return {'reward': (1.0 if success else 0.0) + step_penalty, 'done': success, 'success': success, 'position': pos}

def aggregate_success(results):
    total = len(results)
    return 0.0 if total == 0 else sum(1 for r in results if r.get('success')) / total


def require_valid_action(action):
    if action not in MOVES and action not in COMMANDS:
        raise ValueError('unknown NLE action: ' + str(action))
    return action
