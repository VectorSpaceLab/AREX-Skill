#!/usr/bin/env python3
"""Print Triton compose.py or build.py command templates without executing them."""
from __future__ import annotations
import argparse, json, shlex

def q(argv): return ' '.join(shlex.quote(str(x)) for x in argv)

def main():
    p=argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--mode', choices=['compose','source-build'], default='compose')
    p.add_argument('--python', default='python3')
    p.add_argument('--backend', action='append', default=[])
    p.add_argument('--repoagent', action='append', default=[])
    p.add_argument('--cache', action='append', default=[])
    p.add_argument('--endpoint', action='append', default=[])
    p.add_argument('--filesystem', action='append', default=[])
    p.add_argument('--container-version', default=None)
    p.add_argument('--min-image'); p.add_argument('--full-image')
    p.add_argument('--output-name', default='tritonserver-custom')
    p.add_argument('--enable-all', action='store_true')
    p.add_argument('--cpu-only', action='store_true')
    p.add_argument('--enable-gpu', action='store_true')
    p.add_argument('--enable-stats', action='store_true', default=True)
    p.add_argument('--enable-metrics', action='store_true', default=True)
    p.add_argument('--enable-gpu-metrics', action='store_true', default=True)
    p.add_argument('--enable-cpu-metrics', action='store_true', default=True)
    p.add_argument('--enable-tracing', action='store_true')
    p.add_argument('--enable-nvtx', action='store_true')
    p.add_argument('--disable-logging', action='store_true')
    p.add_argument('--build-type', choices=['Release','Debug','RelWithDebInfo'], default='Release')
    p.add_argument('--no-container-build', action='store_true')
    p.add_argument('--build-dir', default=None)
    p.add_argument('--repo-tag', default=None)
    p.add_argument('--extra-core-cmake-arg', action='append', default=[])
    p.add_argument('--extra-backend-cmake-arg', action='append', default=[])
    p.add_argument('--dryrun', action='store_true', default=True)
    p.add_argument('--force-dryrun', action='store_true')
    p.add_argument('--json', action='store_true')
    a=p.parse_args(); warnings=[]; notes=[]
    if a.mode=='compose':
        argv=[a.python,'compose.py']
        for x in a.backend: argv += ['--backend',x]
        for x in a.repoagent: argv += ['--repoagent',x]
        for x in a.cache: argv += ['--cache',x]
        if a.min_image: argv += ['--image','min,'+a.min_image]
        if a.full_image: argv += ['--image','full,'+a.full_image]
        argv += ['--output-name', a.output_name]
        if a.container_version: argv += ['--container-version', a.container_version]
        notes += ['This is a dry-run planner; it does not run compose.py or Docker.', 'Run the printed command only from the Triton source tree selected for the build.', 'Use compatible min/full container images for the selected Triton release.']
    else:
        argv=['./build.py','-v']
        if not a.disable_logging: argv.append('--enable-logging')
        if a.enable_stats: argv.append('--enable-stats')
        if a.enable_metrics: argv.append('--enable-metrics')
        if a.enable_gpu_metrics: argv.append('--enable-gpu-metrics')
        if a.enable_cpu_metrics: argv.append('--enable-cpu-metrics')
        if a.enable_tracing: argv.append('--enable-tracing')
        if a.enable_nvtx: argv.append('--enable-nvtx')
        if a.enable_all: argv.append('--enable-all')
        if a.enable_gpu and not a.cpu_only: argv.append('--enable-gpu')
        if a.cpu_only: argv.append('--no-enable-gpu')
        for x in (a.endpoint or ['http','grpc']): argv += ['--endpoint',x]
        for x in a.backend: argv += ['--backend',x]
        for x in a.repoagent: argv += ['--repoagent',x]
        for x in a.cache: argv += ['--cache',x]
        for x in a.filesystem: argv += ['--filesystem',x]
        if a.build_type != 'Release': argv += ['--build-type', a.build_type]
        if a.no_container_build: argv.append('--no-container-build')
        if a.build_dir: argv += ['--build-dir', a.build_dir]
        if a.repo_tag: argv += ['--repo-tag', a.repo_tag]
        for x in a.extra_core_cmake_arg: argv += ['--extra-core-cmake-arg', x]
        for x in a.extra_backend_cmake_arg: argv += ['--extra-backend-cmake-arg', x]
        argv.append('--dryrun')
        notes += ['This is a dry-run planner unless you remove/override --dryrun in the printed command.', 'Run the printed command only from the Triton source tree selected for the build.', 'Expect source builds to be large and slow; inspect generated Dockerfiles/scripts before long builds.']
    out={'mode':a.mode,'dry_run_only':True,'commands':[{'label':a.mode+'-plan','argv':argv,'shell':q(argv)}],'warnings':warnings,'notes':notes}
    if a.json: print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(q(argv)); [print('warning:',w) for w in warnings]; [print('note:',n) for n in notes]
if __name__=='__main__': main()
