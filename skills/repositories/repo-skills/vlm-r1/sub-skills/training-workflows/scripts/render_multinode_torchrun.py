#!/usr/bin/env python3
"""Render validated per-node torchrun commands for VLM-R1 GRPO training."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Iterable


def parse_key_value_list(raw: str | None, item_name: str) -> OrderedDict[str, str]:
    result: OrderedDict[str, str] = OrderedDict()
    if not raw:
        return result
    for item in raw.split(','):
        item = item.strip()
        if not item:
            continue
        if '=' not in item:
            raise argparse.ArgumentTypeError(f"{item_name} item must be NAME=VALUE: {item!r}")
        name, value = item.split('=', 1)
        name = name.strip()
        value = value.strip()
        if not name:
            raise argparse.ArgumentTypeError(f"{item_name} item has an empty name: {item!r}")
        if not value:
            raise argparse.ArgumentTypeError(f"{item_name} item has an empty value: {item!r}")
        if name in result:
            raise argparse.ArgumentTypeError(f"duplicate {item_name} name: {name}")
        result[name] = value
    return result


def parse_hosts_file(path: str) -> OrderedDict[str, str]:
    text = Path(path).read_text(encoding='utf-8')
    stripped = text.strip()
    result: OrderedDict[str, str] = OrderedDict()
    if not stripped:
        return result
    if stripped.startswith('{'):
        data = json.loads(stripped)
        if not isinstance(data, dict):
            raise ValueError('JSON host file must be an object mapping node name to address')
        for name, value in data.items():
            if not isinstance(name, str) or not isinstance(value, str):
                raise ValueError('JSON host file keys and values must be strings')
            if not name.strip() or not value.strip():
                raise ValueError('host file contains an empty node name or address')
            result[name.strip()] = value.strip()
        return result

    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            name, value = line.split('=', 1)
        elif ':' in line:
            name, value = line.split(':', 1)
        else:
            raise ValueError(f'host file line {lineno} must be NAME=VALUE or NAME: VALUE')
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if not name or not value:
            raise ValueError(f'host file line {lineno} has an empty node name or address')
        if name in result:
            raise ValueError(f'duplicate host name in host file: {name}')
        result[name] = value
    return result


def parse_nodes(raw: str | None, hosts: OrderedDict[str, str]) -> list[str]:
    if raw:
        nodes = [item.strip() for item in raw.split(',') if item.strip()]
    else:
        nodes = list(hosts.keys())
    if not nodes:
        raise ValueError('provide --nodes or --hosts')
    seen = set()
    for node in nodes:
        if node in seen:
            raise ValueError(f'duplicate node in --nodes: {node}')
        seen.add(node)
    return nodes


def parse_yaml_args(path: str) -> list[str]:
    """Parse a small key: value YAML subset used by VLM-R1 launcher examples."""
    args: list[str] = []
    text = Path(path).read_text(encoding='utf-8')
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if ':' not in stripped:
            raise ValueError(f'args YAML line {lineno} must be key: value')
        key, value = stripped.split(':', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            raise ValueError(f'args YAML line {lineno} has an empty key')
        if not value:
            continue
        args.extend(arg_pair_to_cli(key, value))
    return args


def arg_pair_to_cli(key: str, value: str) -> list[str]:
    if not key.replace('_', '').replace('-', '').isalnum():
        raise ValueError(f'invalid argument key: {key!r}')
    cli_key = '--' + key
    if key in {'reward_funcs', 'reward_weights'}:
        values = [item.strip() for item in value.replace(',', ' ').split() if item.strip()]
        if not values:
            raise ValueError(f'{key} requires at least one value')
        return [cli_key, *values]
    return [cli_key, value]


def parse_repeated_arg(values: Iterable[str] | None) -> list[str]:
    args: list[str] = []
    for item in values or []:
        if '=' not in item:
            raise ValueError(f'--arg must be KEY=VALUE: {item!r}')
        key, value = item.split('=', 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ValueError(f'--arg must have non-empty KEY and VALUE: {item!r}')
        args.extend(arg_pair_to_cli(key, value))
    return args


def sh_join(command: list[str]) -> str:
    return ' '.join(shlex.quote(part) for part in command)


def make_inner_command(workdir: str | None, env: list[str], command: list[str]) -> str:
    pieces: list[str] = []
    if workdir:
        pieces.append('cd ' + shlex.quote(workdir))
        pieces.append('&&')
    pieces.extend(shlex.quote(item) for item in env)
    pieces.append(sh_join(command))
    return ' '.join(pieces)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Render one validated torchrun command per node for VLM-R1 GRPO training.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  Render two nodes from an inline host map:
    render_multinode_torchrun.py \
      --hosts train-a=10.0.0.11,train-b=10.0.0.12 \
      --nodes train-a,train-b \
      --master train-a \
      --workdir src/open-r1-multimodal \
      --arg output_dir=outputs/rl/two-node \
      --arg model_name_or_path=Qwen/Qwen2.5-VL-3B-Instruct \
      --arg data_file_paths=data/a.jsonl:data/b.jsonl \
      --arg image_folders=images/a:images/b \
      --arg task_type=rec \
      --arg is_reward_customized_from_vlm_module=true \
      --arg reward_funcs=accuracy,format \
      --arg deepspeed=local_scripts/zero3.json

  Detect a missing master address:
    render_multinode_torchrun.py --nodes train-a,train-b --master train-a
""",
    )
    parser.add_argument('--hosts', help='comma-separated NAME=ADDRESS host map')
    parser.add_argument('--hosts-file', help='host map file: JSON object or NAME=ADDRESS lines')
    parser.add_argument('--nodes', help='comma-separated node names in rank order; defaults to host-map order')
    parser.add_argument('--master', help='master node name; defaults to the first node')
    parser.add_argument('--master-addr', help='explicit master address; otherwise derived from host map')
    parser.add_argument('--master-port', type=int, default=12345, help='rendezvous port, default: 12345')
    parser.add_argument('--nproc-per-node', type=int, default=8, help='GPU workers per node, default: 8')
    parser.add_argument('--workdir', help='directory to cd into before torchrun')
    parser.add_argument('--script', default='src/open_r1/grpo_jsonl.py', help='training script path, default: src/open_r1/grpo_jsonl.py')
    parser.add_argument('--env', action='append', help='environment assignment KEY=VALUE; may be repeated')
    parser.add_argument('--arg', action='append', help='training argument KEY=VALUE; may be repeated')
    parser.add_argument('--args-yaml', help='small key: value file converted to training args')
    parser.add_argument('--train-args', help='raw shell-style training args appended after generated args')
    parser.add_argument('--ssh', action='store_true', help='wrap each command as ssh NODE sh-command')
    parser.add_argument('--ssh-user', help='optional ssh user prefix')
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)

    try:
        hosts = parse_key_value_list(ns.hosts, 'host')
        if ns.hosts_file:
            file_hosts = parse_hosts_file(ns.hosts_file)
            for name in file_hosts:
                if name in hosts:
                    raise ValueError(f'duplicate host name across --hosts and --hosts-file: {name}')
            hosts.update(file_hosts)
        nodes = parse_nodes(ns.nodes, hosts)
        if hosts:
            unknown = [node for node in nodes if node not in hosts]
            if unknown:
                raise ValueError('nodes missing from host map: ' + ', '.join(unknown))
        master = ns.master or nodes[0]
        if master not in nodes:
            raise ValueError(f'master node {master!r} is not present in node order')
        if ns.master_addr:
            master_addr = ns.master_addr
        elif master in hosts:
            master_addr = hosts[master]
        else:
            raise ValueError('missing master address: provide --master-addr or include the master in --hosts')
        if ns.master_port <= 0 or ns.master_port >= 65536:
            raise ValueError('--master-port must be between 1 and 65535')
        if ns.nproc_per_node <= 0:
            raise ValueError('--nproc-per-node must be greater than zero')

        env = []
        for item in ns.env or []:
            if '=' not in item:
                raise ValueError(f'--env must be KEY=VALUE: {item!r}')
            key, value = item.split('=', 1)
            if not key or not value:
                raise ValueError(f'--env must have non-empty KEY and VALUE: {item!r}')
            env.append(f'{key}={value}')

        train_args: list[str] = []
        train_args.extend(parse_repeated_arg(ns.arg))
        if ns.args_yaml:
            train_args.extend(parse_yaml_args(ns.args_yaml))
        if ns.train_args:
            train_args.extend(shlex.split(ns.train_args))

    except Exception as exc:  # argparse-friendly validation error
        parser.error(str(exc))

    nnodes = len(nodes)
    print(f'# master={master} master_addr={master_addr} master_port={ns.master_port} nnodes={nnodes}')
    print(f'# node_order={",".join(nodes)}')

    for rank, node in enumerate(nodes):
        command = [
            'torchrun',
            f'--nproc_per_node={ns.nproc_per_node}',
            f'--nnodes={nnodes}',
            f'--node_rank={rank}',
            f'--master_addr={master_addr}',
            f'--master_port={ns.master_port}',
            ns.script,
            *train_args,
        ]
        inner = make_inner_command(ns.workdir, env, command)
        print(f'\n# node={node} rank={rank}')
        if ns.ssh:
            destination = f'{ns.ssh_user}@{node}' if ns.ssh_user else node
            print('ssh ' + shlex.quote(destination) + ' ' + shlex.quote(inner))
        else:
            print(inner)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
