#!/usr/bin/env python3
"""DFS search for the 5x5 mini crossword task.

This is a small CLI adaptation of the notebook-derived workflow. It keeps the
same proposal parsing and board-consistency checks, but exposes the search loop
as a reusable script.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from tot.models import gpt
from tot.prompts.crosswords import propose_prompt, value_prompt
from tot.tasks.crosswords import MiniCrosswordsEnv

CONFIDENCE_TO_VALUE = {
    'certain': 1.0,
    'high': 0.5,
    'medium': 0.2,
    'low': 0.1,
}


def prompt_wrap(obs: str) -> str:
    return propose_prompt.format(input=obs)


def parse_line(input_str: str):
    pattern = r'^([hv][1-5])\. ([a-zA-Z]{5,5}) \((certain|high|medium|low)\).*$'
    match = re.match(pattern, input_str)
    if match:
        return [match.group(1), match.group(2), match.group(3)]
    return None


def parse_response(response: str):
    parsed = []
    for line in response.split('\n'):
        item = parse_line(line)
        if item is not None:
            parsed.append((item[0].lower() + '. ' + item[1].lower(), CONFIDENCE_TO_VALUE.get(item[2], 0)))
    return parsed or None


def get_candidates_to_scores(env: MiniCrosswordsEnv, model: str, temperature: float, n_samples: int):
    obs = env.render()
    if obs in env.cache:
        return env.cache[obs]
    responses = gpt(prompt_wrap(obs), model=model, temperature=temperature, n=n_samples)
    candidates_to_scores = {}
    for response in responses:
        parsed_response = parse_response(response)
        if parsed_response:
            for candidate, score in parsed_response:
                candidates_to_scores[candidate] = candidates_to_scores.get(candidate, 0) + score
    env.cache[obs] = candidates_to_scores
    return candidates_to_scores


def prompt_status(env: MiniCrosswordsEnv, model: str, temperature: float):
    count = {'sure': 0, 'maybe': 0, 'impossible': 0}
    for ans, data, status in zip(env.ans, env.data, env.status):
        if ans.count('_') >= 4:
            continue
        ans = ' '.join(ans.lower())
        line = f'{data}: {ans}'
        prompt = value_prompt.format(input=line)
        if prompt in env.prompt_status_cache:
            res = env.prompt_status_cache[prompt]
        else:
            res = gpt(prompt, model=model, temperature=temperature, n=1)[0]
            env.prompt_status_cache[prompt] = res
        res = res.split('\n')[-1].strip()
        if res in count:
            count[res] += 1
    return count


def dfs(env: MiniCrosswordsEnv, actions, infos, time_limit: int, prune: bool, max_per_state: int, model: str, temperature: float, judge_temperature: float, n_samples: int):
    candidates_to_scores = get_candidates_to_scores(env, model=model, temperature=temperature, n_samples=n_samples)
    if len(candidates_to_scores) == 0:
        return

    board, status, steps = env.board.copy(), env.status.copy(), env.steps
    cnt_per_state = 0
    for action in sorted(candidates_to_scores, key=candidates_to_scores.get, reverse=True):
        obs, r, done, info = env.step(action)
        if len(infos) < time_limit and env.steps < 10 and not any(_ == 2 for _ in env.status):
            cnt_per_state += 1
            if cnt_per_state > max_per_state:
                break
            count = prompt_status(env, model=model, temperature=judge_temperature)
            actions.append(action)
            infos.append(
                {
                    'total_step': len(infos),
                    'env_step': env.steps,
                    'actions': actions.copy(),
                    'info': info,
                    'count': count,
                }
            )
            if not prune or count['impossible'] < 1:
                dfs(env, actions, infos, time_limit, prune, max_per_state, model, temperature, judge_temperature, n_samples)
            actions.pop()
        env.reset(env.idx, board=board.copy(), status=status.copy(), steps=steps)


def run(args):
    env = MiniCrosswordsEnv(args.file)
    outputs = []
    stride = args.stride
    for idx in range(args.start, min(args.end, len(env)), stride):
        env.reset(idx)
        infos = []
        actions = []
        dfs(env, actions, infos, args.time_limit, args.prune, args.max_per_state, args.model, args.temperature, args.judge_temperature, args.n_samples)
        outputs.append({'idx': idx, 'infos': infos})
        print(f'idx={idx} infos={len(infos)}')

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(outputs, indent=2), encoding='utf-8')
    print(f'wrote {output_path}')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', default='mini0505.json')
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=100)
    parser.add_argument('--stride', type=int, default=5)
    parser.add_argument('--time-limit', type=int, default=100)
    parser.add_argument('--prune', action='store_true')
    parser.add_argument('--max-per-state', type=int, default=3)
    parser.add_argument('--model', default='gpt-4')
    parser.add_argument('--temperature', type=float, default=0.7)
    parser.add_argument('--judge-temperature', type=float, default=0.7)
    parser.add_argument('--n-samples', type=int, default=8)
    parser.add_argument('--output', default='./logs/crosswords/dfs_search.json')
    return parser.parse_args()


if __name__ == '__main__':
    run(parse_args())
