#!/usr/bin/env python3
"""Self-contained GridWorld smoke checks for the reinforcement-learning skill.

The checks reimplement tiny DP, tabular-control, dynamic-env, Deep SARSA,
and REINFORCE fixtures. They intentionally do not import original repository
files, open Pygame, or run full training loops.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import defaultdict
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

WIDTH = 5
HEIGHT = 5
DP_ACTIONS: List[Tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]
TABULAR_ACTIONS: Dict[int, Tuple[int, int]] = {
    0: (0, -1),   # up on [col, row]
    1: (0, 1),    # down
    2: (-1, 0),   # left
    3: (1, 0),    # right
}
DYNAMIC_ACTIONS: Dict[int, Tuple[int, int]] = {
    0: (0, -1),   # up on [col, row]
    1: (0, 1),    # down
    2: (1, 0),    # right; differs from static tabular action 2
    3: (-1, 0),   # left
    4: (0, 0),    # source-compatible no-op output/action
}


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


# ---------------------------------------------------------------------------
# Dynamic programming fixture: state is [row, col].
class PolicyGrid:
    transition_probability = 1.0
    possible_actions = [0, 1, 2, 3]

    def __init__(self) -> None:
        self.width = WIDTH
        self.height = HEIGHT
        self.reward = [[0.0] * WIDTH for _ in range(HEIGHT)]
        self.reward[2][2] = 1.0
        self.reward[1][2] = -1.0
        self.reward[2][1] = -1.0
        self.all_state = [[row, col] for row in range(HEIGHT) for col in range(WIDTH)]

    def get_all_states(self) -> List[List[int]]:
        return [list(s) for s in self.all_state]

    def state_after_action(self, state: Sequence[int], action: int) -> List[int]:
        dr, dc = DP_ACTIONS[action]
        row = clamp(int(state[0]) + dr, 0, HEIGHT - 1)
        col = clamp(int(state[1]) + dc, 0, WIDTH - 1)
        return [row, col]

    def get_reward(self, state: Sequence[int], action: int) -> float:
        ns = self.state_after_action(state, action)
        return self.reward[ns[0]][ns[1]]

    def get_transition_prob(self, state: Sequence[int], action: int) -> float:
        return self.transition_probability


def dp_to_draw_xy(state: Sequence[int]) -> Tuple[int, int]:
    """Convert DP [row, col] state to drawing coordinates (x=col, y=row)."""
    return int(state[1]), int(state[0])


class PolicyIteration:
    def __init__(self, env: PolicyGrid) -> None:
        self.env = env
        self.value_table = [[0.0] * env.width for _ in range(env.height)]
        self.policy_table = [
            [[0.25, 0.25, 0.25, 0.25] for _ in range(env.width)]
            for _ in range(env.height)
        ]
        self.policy_table[2][2] = []
        self.discount_factor = 0.9

    def policy_evaluation(self) -> None:
        next_value_table = [[0.0] * self.env.width for _ in range(self.env.height)]
        for state in self.env.get_all_states():
            if state == [2, 2]:
                next_value_table[state[0]][state[1]] = 0.0
                continue
            value = 0.0
            policy = self.get_policy(state)
            for action in self.env.possible_actions:
                next_state = self.env.state_after_action(state, action)
                reward = self.env.get_reward(state, action)
                value += policy[action] * (reward + self.discount_factor * self.get_value(next_state))
            next_value_table[state[0]][state[1]] = round(value, 2)
        self.value_table = next_value_table

    def policy_improvement(self) -> None:
        next_policy = [
            [list(self.policy_table[row][col]) for col in range(self.env.width)]
            for row in range(self.env.height)
        ]
        for state in self.env.get_all_states():
            if state == [2, 2]:
                continue
            best_value = -float("inf")
            best_actions: List[int] = []
            for action in self.env.possible_actions:
                next_state = self.env.state_after_action(state, action)
                reward = self.env.get_reward(state, action)
                candidate = reward + self.discount_factor * self.get_value(next_state)
                if candidate > best_value:
                    best_value = candidate
                    best_actions = [action]
                elif candidate == best_value:
                    best_actions.append(action)
            prob = 1.0 / len(best_actions)
            next_policy[state[0]][state[1]] = [prob if a in best_actions else 0.0 for a in self.env.possible_actions]
        self.policy_table = next_policy

    def get_policy(self, state: Sequence[int]):
        if list(state) == [2, 2]:
            return []
        return self.policy_table[state[0]][state[1]]

    def get_value(self, state: Sequence[int]) -> float:
        return round(self.value_table[state[0]][state[1]], 2)


class ValueIteration:
    def __init__(self, env: PolicyGrid) -> None:
        self.env = env
        self.value_table = [[0.0] * env.width for _ in range(env.height)]
        self.discount_factor = 0.9

    def value_iteration(self) -> None:
        next_value_table = [[0.0] * self.env.width for _ in range(self.env.height)]
        for state in self.env.get_all_states():
            if state == [2, 2]:
                next_value_table[state[0]][state[1]] = 0.0
                continue
            values = []
            for action in self.env.possible_actions:
                next_state = self.env.state_after_action(state, action)
                reward = self.env.get_reward(state, action)
                values.append(reward + self.discount_factor * self.get_value(next_state))
            next_value_table[state[0]][state[1]] = round(max(values), 2)
        self.value_table = next_value_table

    def get_action(self, state: Sequence[int]) -> List[int]:
        if list(state) == [2, 2]:
            return []
        best_value = -float("inf")
        best_actions: List[int] = []
        for action in self.env.possible_actions:
            next_state = self.env.state_after_action(state, action)
            reward = self.env.get_reward(state, action)
            candidate = reward + self.discount_factor * self.get_value(next_state)
            if candidate > best_value:
                best_value = candidate
                best_actions = [action]
            elif candidate == best_value:
                best_actions.append(action)
        return best_actions

    def get_value(self, state: Sequence[int]) -> float:
        return round(self.value_table[state[0]][state[1]], 2)


# ---------------------------------------------------------------------------
# Static tabular control fixture: state is [col, row].
class TabularGrid:
    n_actions = 4

    def __init__(self) -> None:
        self.agent = [0, 0]
        self.obstacles = [[1, 2], [2, 1]]
        self.goal = [2, 2]
        self.steps = 0

    def reset(self) -> List[int]:
        self.agent = [0, 0]
        self.steps = 0
        return list(self.agent)

    def step(self, action: int) -> Tuple[List[int], int, bool]:
        dc, dr = TABULAR_ACTIONS[action]
        col = clamp(self.agent[0] + dc, 0, WIDTH - 1)
        row = clamp(self.agent[1] + dr, 0, HEIGHT - 1)
        self.agent = [col, row]
        self.steps += 1
        if self.agent == self.goal:
            return list(self.agent), 100, True
        if self.agent in self.obstacles:
            return list(self.agent), -100, True
        return list(self.agent), 0, False


class SarsaAgent:
    def __init__(self, actions: Sequence[int], rng: random.Random) -> None:
        self.actions = list(actions)
        self.learning_rate = 0.01
        self.discount_factor = 0.9
        self.epsilon = 0.1
        self.q_table = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
        self.rng = rng

    def learn(self, state: str, action: int, reward: float, next_state: str, next_action: int) -> None:
        current_q = self.q_table[state][action]
        next_state_q = self.q_table[next_state][next_action]
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * next_state_q - current_q)
        self.q_table[state][action] = new_q

    def get_action(self, state: str) -> int:
        if self.rng.random() < self.epsilon:
            return self.rng.choice(self.actions)
        return self.arg_max(self.q_table[state], self.rng)

    @staticmethod
    def arg_max(state_action: Sequence[float], rng: random.Random) -> int:
        max_value = max(state_action)
        ties = [idx for idx, value in enumerate(state_action) if value == max_value]
        return rng.choice(ties)


class QLearningAgent:
    def __init__(self, actions: Sequence[int], rng: random.Random) -> None:
        self.actions = list(actions)
        self.learning_rate = 0.01
        self.discount_factor = 0.9
        self.epsilon = 0.1
        self.q_table = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
        self.rng = rng

    def learn(self, state: str, action: int, reward: float, next_state: str) -> None:
        current_q = self.q_table[state][action]
        target = reward + self.discount_factor * max(self.q_table[next_state])
        self.q_table[state][action] += self.learning_rate * (target - current_q)

    def get_action(self, state: str) -> int:
        if self.rng.random() < self.epsilon:
            return self.rng.choice(self.actions)
        return SarsaAgent.arg_max(self.q_table[state], self.rng)


# ---------------------------------------------------------------------------
# Dynamic fixture: position is [col, row], observation length is 15.
class DynamicGrid:
    n_actions = 4
    state_size = 15

    def __init__(self, step_penalty: float = 0.0, render_mode=None) -> None:
        self.step_penalty = float(step_penalty)
        self.render_mode = render_mode
        self.obstacles_init = [[0, 1], [1, 2], [2, 3]]
        self.goal = [4, 4]
        self.agent = [0, 0]
        self.obstacles: List[Dict[str, object]] = []
        self.counter = 0
        self.score = 0.0

    def reset(self) -> List[float]:
        self.agent = [0, 0]
        self.counter = 0
        self.score = 0.0
        self.obstacles = [{"state": list(p), "direction": -1} for p in self.obstacles_init]
        return self._state()

    def step(self, action: int) -> Tuple[List[float], float, bool]:
        self.counter += 1
        # render_mode=None is the headless smoke path; no window is opened here.
        if self.counter % 2 == 1:
            for obstacle in self.obstacles:
                state = obstacle["state"]
                assert isinstance(state, list)
                if state[0] == WIDTH - 1:
                    obstacle["direction"] = 1
                elif state[0] == 0:
                    obstacle["direction"] = -1
                state[0] += 1 if obstacle["direction"] == -1 else -1

        dc, dr = DYNAMIC_ACTIONS[action]
        self.agent = [clamp(self.agent[0] + dc, 0, WIDTH - 1), clamp(self.agent[1] + dr, 0, HEIGHT - 1)]

        done = self.agent == self.goal
        reward = 1.0 if done else 0.0
        for obstacle in self.obstacles:
            if obstacle["state"] == self.agent:
                reward -= 1.0
        reward -= self.step_penalty
        self.score += reward
        return self._state(), reward, done

    def _state(self) -> List[float]:
        ax, ay = self.agent
        state: List[float] = []
        for obstacle in self.obstacles:
            ox, oy = obstacle["state"]  # type: ignore[misc]
            direction = obstacle["direction"]
            state += [float(ox - ax), float(oy - ay), -1.0, float(direction)]
        state += [float(self.goal[0] - ax), float(self.goal[1] - ay), 1.0]
        return state


# ---------------------------------------------------------------------------
# Checks.
def check_dp(args: argparse.Namespace) -> Dict[str, str]:
    env = PolicyGrid()
    require(env.state_after_action([0, 0], 0) == [0, 0], "DP up at top edge should stay in row 0")
    require(env.state_after_action([0, 2], 1) == [1, 2], "DP action 1 should move down on [row,col]")
    require(env.get_reward([0, 2], 1) == -1.0, "DP reward lookup should index reward[row][col]")
    require(dp_to_draw_xy([1, 2]) == (2, 1), "DP draw conversion must swap [row,col] -> (col,row)")

    pi = PolicyIteration(env)
    pi.policy_evaluation()
    require(pi.value_table[0][2] == -0.25, "one policy-evaluation sweep should see trap below [0,2]")
    pi.policy_improvement()
    require(pi.policy_table[2][2] == [], "terminal DP policy should remain empty")

    vi = ValueIteration(env)
    vi.value_iteration()
    require(vi.value_table[1][2] == 1.0, "value iteration should value the state above the goal at +1 after one sweep")
    require(1 in vi.get_action([1, 2]), "greedy action from [1,2] should include down toward the goal")
    return {"status": "PASS", "detail": "DP row/col, policy iteration, and value iteration checks passed"}


def check_tabular(args: argparse.Namespace) -> Dict[str, str]:
    rng = random.Random(args.seed)
    env = TabularGrid()
    state = env.reset()
    require(state == [0, 0], "tabular reset should return [col,row] = [0,0]")
    next_state, reward, done = env.step(3)
    require(next_state == [1, 0] and reward == 0 and not done, "tabular action 3 should move right to [1,0]")
    next_state, reward, done = env.step(1)
    require(next_state == [1, 1] and reward == 0 and not done, "tabular action 1 should move down to [1,1]")
    next_state, reward, done = env.step(1)
    require(next_state == [1, 2] and reward == -100 and done, "tabular obstacle [1,2] should terminate with -100")

    sarsa = SarsaAgent(actions=range(env.n_actions), rng=rng)
    sarsa.q_table["next"][1] = 5.0
    sarsa.learn("state", 0, 1.0, "next", 1)
    require(abs(sarsa.q_table["state"][0] - 0.055) < 1e-12, "SARSA TD update should match alpha*(r+gamma*Q(s',a'))")

    ql = QLearningAgent(actions=range(env.n_actions), rng=rng)
    ql.q_table["next"] = [0.0, 2.0, 4.0, 1.0]
    ql.learn("state", 2, 1.0, "next")
    require(abs(ql.q_table["state"][2] - 0.046) < 1e-12, "Q-learning update should use max next-state value")
    return {"status": "PASS", "detail": "tabular [col,row], SARSA, and Q-learning checks passed"}


def check_dynamic(args: argparse.Namespace) -> Dict[str, str]:
    env = DynamicGrid(step_penalty=0.1, render_mode=None)
    state = env.reset()
    require(len(state) == 15, "dynamic reset should return a 15-dimensional state")
    next_state, reward, done = env.step(2)
    require(env.agent == [1, 0], "dynamic action 2 should move right, unlike static tabular action 2")
    require(len(next_state) == 15 and not done, "dynamic one-step state should remain length 15 and nonterminal")

    env.reset()
    env.step(4)
    require(env.agent == [0, 0], "dynamic action 4 should behave as a source-compatible no-op")
    require(env.render_mode is None, "dynamic smoke should remain headless via render_mode=None")
    return {"status": "PASS", "detail": "dynamic headless state/action checks passed"}


def check_neural(args: argparse.Namespace) -> Dict[str, str]:
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
    except Exception as exc:  # pragma: no cover - depends on caller environment.
        if args.strict_torch:
            raise RuntimeError(f"Torch neural checks requested but torch is unavailable: {exc}") from exc
        return {"status": "SKIP", "detail": f"Torch unavailable; skipped neural checks ({exc})"}

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    class QNetwork(nn.Module):
        def __init__(self, state_size: int, action_size: int) -> None:
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(state_size, 30),
                nn.ReLU(),
                nn.Linear(30, 30),
                nn.ReLU(),
                nn.Linear(30, action_size),
            )

        def forward(self, x):
            return self.net(x)

    class DeepSarsaAgent:
        def __init__(self) -> None:
            self.action_space = [0, 1, 2, 3, 4]
            self.action_size = len(self.action_space)
            self.state_size = 15
            self.discount_factor = 0.99
            self.learning_rate = 1e-3
            self.epsilon = 1.0
            self.epsilon_decay = 0.9999
            self.epsilon_min = 0.01
            self.model = QNetwork(self.state_size, self.action_size)
            self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
            self.loss_fn = nn.MSELoss()

        def train_model(self, state, action: int, reward: float, next_state, next_action: int, done: bool) -> float:
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
            state_t = torch.as_tensor(state, dtype=torch.float32)
            next_state_t = torch.as_tensor(next_state, dtype=torch.float32)
            q_pred = self.model(state_t)[action]
            with torch.no_grad():
                if done:
                    target = torch.tensor(float(reward), dtype=torch.float32)
                else:
                    target = torch.tensor(float(reward), dtype=torch.float32) + self.discount_factor * self.model(next_state_t)[next_action]
            loss = self.loss_fn(q_pred, target)
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            return float(loss.detach().item())

    class PolicyNetwork(nn.Module):
        def __init__(self, state_size: int, action_size: int) -> None:
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(state_size, 24),
                nn.ReLU(),
                nn.Linear(24, 24),
                nn.ReLU(),
                nn.Linear(24, action_size),
            )

        def forward(self, x):
            return self.net(x)

    class ReinforceAgent:
        def __init__(self) -> None:
            self.action_size = 5
            self.state_size = 15
            self.discount_factor = 0.99
            self.model = PolicyNetwork(self.state_size, self.action_size)
            self.optimizer = optim.Adam(self.model.parameters(), lr=1e-3)
            self.states: List[List[float]] = []
            self.actions: List[int] = []
            self.rewards: List[float] = []

        def discount_rewards(self, rewards: Sequence[float]) -> List[float]:
            discounted = [0.0 for _ in rewards]
            running = 0.0
            for idx in reversed(range(len(rewards))):
                running = running * self.discount_factor + float(rewards[idx])
                discounted[idx] = running
            return discounted

        def append_sample(self, state: Sequence[float], action: int, reward: float) -> None:
            self.states.append([float(x) for x in state])
            self.actions.append(int(action))
            self.rewards.append(float(reward))

        def train_model(self) -> float:
            returns = torch.as_tensor(self.discount_rewards(self.rewards), dtype=torch.float32)
            returns = (returns - returns.mean()) / (returns.std(unbiased=False) + 1e-8)
            states = torch.as_tensor(self.states, dtype=torch.float32)
            actions = torch.as_tensor(self.actions, dtype=torch.long)
            logits = self.model(states)
            log_probs = torch.log_softmax(logits, dim=-1)
            chosen = log_probs.gather(1, actions.unsqueeze(1)).squeeze(1)
            loss = -(chosen * returns).sum()
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            self.states, self.actions, self.rewards = [], [], []
            return float(loss.detach().item())

    env = DynamicGrid(render_mode=None)
    state = env.reset()
    next_state, reward, done = env.step(2)

    deep = DeepSarsaAgent()
    before_epsilon = deep.epsilon
    loss = deep.train_model(state, action=2, reward=reward, next_state=next_state, next_action=1, done=done)
    require(math.isfinite(loss), "Deep SARSA loss should be finite")
    require(deep.epsilon < before_epsilon, "Deep SARSA epsilon should decay after one train step")
    q_values = deep.model(torch.as_tensor(state, dtype=torch.float32))
    require(tuple(q_values.shape) == (5,), "Deep SARSA Q-network should emit five source-compatible action values")

    reinforce = ReinforceAgent()
    returns = reinforce.discount_rewards([0.0, 1.0])
    require(len(returns) == 2 and abs(returns[0] - 0.99) < 1e-6 and abs(returns[1] - 1.0) < 1e-6,
            "REINFORCE discounted returns should be computed backwards")
    reinforce.append_sample(state, 2, 0.0)
    reinforce.append_sample(next_state, 1, 1.0)
    pg_loss = reinforce.train_model()
    require(math.isfinite(pg_loss), "REINFORCE policy-gradient loss should be finite")
    require(not reinforce.states and not reinforce.actions and not reinforce.rewards,
            "REINFORCE trajectory buffers should clear after training")
    return {"status": "PASS", "detail": "Torch Deep SARSA and REINFORCE one-step checks passed"}


CHECKS: Dict[str, Callable[[argparse.Namespace], Dict[str, str]]] = {
    "dp": check_dp,
    "tabular": check_tabular,
    "dynamic": check_dynamic,
    "neural": check_neural,
}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run self-contained, headless GridWorld smoke checks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python scripts/grid_world_smoke.py
  python scripts/grid_world_smoke.py --section dp
  python scripts/grid_world_smoke.py --section neural --strict-torch
  python scripts/grid_world_smoke.py --section dp --section tabular --json
""",
    )
    parser.add_argument(
        "--section",
        action="append",
        choices=["all", "dp", "tabular", "dynamic", "neural"],
        help="Section to run. Repeat for multiple sections. Default: all.",
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed for stochastic tie-breaking and Torch checks.")
    parser.add_argument(
        "--strict-torch",
        action="store_true",
        help="Fail instead of skipping when Torch is unavailable for neural checks.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON results.")
    return parser.parse_args(argv)


def selected_sections(raw_sections: Iterable[str] | None) -> List[str]:
    if not raw_sections or "all" in raw_sections:
        return ["dp", "tabular", "dynamic", "neural"]
    out: List[str] = []
    for section in raw_sections:
        if section not in out:
            out.append(section)
    return out


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    sections = selected_sections(args.section)
    results: List[Dict[str, str]] = []
    ok = True
    for section in sections:
        try:
            result = CHECKS[section](args)
        except Exception as exc:
            ok = False
            result = {"status": "FAIL", "detail": f"{type(exc).__name__}: {exc}"}
        result = {"section": section, **result}
        results.append(result)

    if args.json:
        print(json.dumps({"ok": ok, "results": results}, indent=2, sort_keys=True))
    else:
        for result in results:
            print(f"{result['status']} {result['section']}: {result['detail']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
