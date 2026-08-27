#!/usr/bin/env python3
"""Print safe Triton launch command templates without starting services."""
from __future__ import annotations
import argparse, json, shlex


def shell(argv):
    return ' '.join(shlex.quote(str(x)) for x in argv)


def build(args):
    warnings=[]; notes=[]
    triton_args=[f'--model-repository={args.model_repository}', f'--model-control-mode={args.model_control_mode}']
    if args.model_control_mode == 'poll':
        triton_args.append(f'--repository-poll-secs={args.repository_poll_secs}')
    if args.load_model:
        if args.model_control_mode != 'explicit':
            warnings.append('--load-model only has effect with --model-control-mode=explicit.')
        if '*' in args.load_model and len(args.load_model)>1:
            warnings.append("--load-model=* must be the only --load-model argument.")
        for m in args.load_model:
            triton_args.append(f'--load-model={m}')
    effective_allow_gpu_metrics = args.allow_gpu_metrics and not (args.context == 'cpu' or args.gpu == 'none')
    triton_args.append(f'--strict-readiness={str(args.strict_readiness).lower()}')
    triton_args.append(f'--allow-metrics={str(args.allow_metrics).lower()}')
    triton_args.append(f'--allow-gpu-metrics={str(effective_allow_gpu_metrics).lower()}')
    triton_args.append(f'--allow-cpu-metrics={str(args.allow_cpu_metrics).lower()}')
    triton_args.append(f'--metrics-port={args.metrics_port}')
    if args.context == 'binary':
        argv=['tritonserver']+triton_args
    else:
        argv=['docker','run','--rm']
        if args.net_host:
            argv.append('--net=host')
        else:
            argv += [f'-p{args.http_port}:8000', f'-p{args.grpc_port}:8001', f'-p{args.metrics_port}:8002']
        if args.context == 'gpu' or args.gpu != 'none':
            argv.append(f'--gpus={args.gpu if args.gpu != "count" else args.gpu_count}')
        elif args.context == 'cpu':
            notes.append('CPU context omits Docker --gpus; GPU-required models/backends will not load.')
        mount_mode='rw' if args.read_write_repository else 'ro'
        argv += ['-v', f'{args.host_model_repository}:{args.model_repository}:{mount_mode}', args.image, 'tritonserver'] + triton_args
    notes.append('This is a dry-run command plan; run it only after checking paths, ports, container tag, and backend requirements.')
    return {'command': {'argv': argv, 'shell': shell(argv)}, 'warnings': warnings, 'notes': notes}


def main():
    p=argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--context', choices=['docker','cpu','gpu','binary'], default='docker')
    p.add_argument('--model-repository', required=True, help='Model repository path as seen by Triton, normally /models in containers.')
    p.add_argument('--host-model-repository', default=None, help='Host path to mount. Defaults to --model-repository.')
    p.add_argument('--image', default='nvcr.io/nvidia/tritonserver:26.07-py3')
    p.add_argument('--gpu', choices=['none','all','count'], default='all')
    p.add_argument('--gpu-count', default='1')
    p.add_argument('--http-port', type=int, default=8000); p.add_argument('--grpc-port', type=int, default=8001); p.add_argument('--metrics-port', type=int, default=8002)
    p.add_argument('--model-control-mode', choices=['none','explicit','poll'], default='none')
    p.add_argument('--load-model', action='append')
    p.add_argument('--repository-poll-secs', type=int, default=15)
    p.add_argument('--strict-readiness', dest='strict_readiness', action='store_true', default=True)
    p.add_argument('--no-strict-readiness', dest='strict_readiness', action='store_false')
    p.add_argument('--allow-metrics', dest='allow_metrics', action='store_true', default=True); p.add_argument('--no-allow-metrics', dest='allow_metrics', action='store_false')
    p.add_argument('--allow-gpu-metrics', dest='allow_gpu_metrics', action='store_true', default=True); p.add_argument('--no-allow-gpu-metrics', dest='allow_gpu_metrics', action='store_false')
    p.add_argument('--allow-cpu-metrics', dest='allow_cpu_metrics', action='store_true', default=True); p.add_argument('--no-allow-cpu-metrics', dest='allow_cpu_metrics', action='store_false')
    p.add_argument('--net-host', dest='net_host', action='store_true', default=True); p.add_argument('--no-net-host', dest='net_host', action='store_false')
    p.add_argument('--read-write-repository', action='store_true')
    p.add_argument('--json', action='store_true')
    a=p.parse_args(); a.host_model_repository=a.host_model_repository or a.model_repository
    out=build(a)
    if a.json: print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(out['command']['shell'])
        for w in out['warnings']: print('warning:', w)
        for n in out['notes']: print('note:', n)

if __name__=='__main__': main()
