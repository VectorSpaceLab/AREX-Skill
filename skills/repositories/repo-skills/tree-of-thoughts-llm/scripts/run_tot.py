#!/usr/bin/env python3
"""Bundled Tree of Thoughts runner."""

import argparse
import json
import os

from tot.methods.bfs import naive_solve, solve
from tot.models import gpt_usage
from tot.tasks import get_task


def run(args):
    task = get_task(args.task)
    logs, cnt_avg, cnt_any = [], 0, 0
    if args.naive_run:
        file = (
            f"./logs/{args.task}/{args.backend}_{args.temperature}_naive_"
            f"{args.prompt_sample}_sample_{args.n_generate_sample}_"
            f"start{args.task_start_index}_end{args.task_end_index}.json"
        )
    else:
        file = (
            f"./logs/{args.task}/{args.backend}_{args.temperature}_"
            f"{args.method_generate}{args.n_generate_sample}_"
            f"{args.method_evaluate}{args.n_evaluate_sample}_"
            f"{args.method_select}{args.n_select_sample}_"
            f"start{args.task_start_index}_end{args.task_end_index}.json"
        )
    os.makedirs(os.path.dirname(file), exist_ok=True)

    for i in range(args.task_start_index, args.task_end_index):
        if args.naive_run:
            ys, info = naive_solve(args, task, i)
        else:
            ys, info = solve(args, task, i)

        infos = [task.test_output(i, y) for y in ys]
        info.update({'idx': i, 'ys': ys, 'infos': infos, 'usage_so_far': gpt_usage(args.backend)})
        logs.append(info)
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=4)

        accs = [info['r'] for info in infos]
        cnt_avg += sum(accs) / len(accs)
        cnt_any += any(accs)
        print(i, 'sum(accs)', sum(accs), 'cnt_avg', cnt_avg, 'cnt_any', cnt_any, '\n')

    n = args.task_end_index - args.task_start_index
    print(cnt_avg / n, cnt_any / n)
    print('usage_so_far', gpt_usage(args.backend))


def parse_args():
    args = argparse.ArgumentParser()
    args.add_argument('--backend', type=str, choices=['gpt-4', 'gpt-3.5-turbo', 'gpt-4o'], default='gpt-4')
    args.add_argument('--temperature', type=float, default=0.7)

    args.add_argument('--task', type=str, required=True, choices=['game24', 'text', 'crosswords'])
    args.add_argument('--task_start_index', type=int, default=900)
    args.add_argument('--task_end_index', type=int, default=1000)

    args.add_argument('--naive_run', action='store_true')
    args.add_argument('--prompt_sample', type=str, choices=['standard', 'cot'])

    args.add_argument('--method_generate', type=str, choices=['sample', 'propose'])
    args.add_argument('--method_evaluate', type=str, choices=['value', 'vote'])
    args.add_argument('--method_select', type=str, choices=['sample', 'greedy'], default='greedy')
    args.add_argument('--n_generate_sample', type=int, default=1)
    args.add_argument('--n_evaluate_sample', type=int, default=1)
    args.add_argument('--n_select_sample', type=int, default=1)

    return args.parse_args()


if __name__ == '__main__':
    args = parse_args()
    print(args)
    run(args)
