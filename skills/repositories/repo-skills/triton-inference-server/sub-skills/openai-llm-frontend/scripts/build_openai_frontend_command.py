#!/usr/bin/env python3
"""Build a Triton OpenAI-compatible frontend launch command without running it."""
from __future__ import annotations
import argparse, json, shlex


def q(argv): return ' '.join(shlex.quote(str(x)) for x in argv)


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--python', default='python3')
    p.add_argument('--entrypoint', default='openai_frontend/main.py')
    p.add_argument('--model-repository', required=True)
    p.add_argument('--tokenizer')
    p.add_argument('--backend', choices=['vllm','tensorrtllm'])
    p.add_argument('--host', default='0.0.0.0')
    p.add_argument('--openai-port', type=int, default=9000)
    p.add_argument('--uvicorn-log-level', choices=['debug','info','warning','error','critical','trace'], default='info')
    p.add_argument('--model-control-mode', choices=['none','explicit'], default='none')
    p.add_argument('--load-model', action='append')
    p.add_argument('--enable-kserve-frontends', action='store_true')
    p.add_argument('--kserve-http-port', type=int, default=8000)
    p.add_argument('--kserve-grpc-port', type=int, default=8001)
    p.add_argument('--http-max-input-size', type=int)
    p.add_argument('--lora-separator')
    p.add_argument('--tool-call-parser', choices=['llama3','mistral'])
    p.add_argument('--max-tool-call-parse-bytes', type=int)
    p.add_argument('--chat-template')
    p.add_argument('--restricted-api', action='append', help='Format APIs:key:value, e.g. inference,model-repository:admin-key:secret')
    p.add_argument('--json', action='store_true')
    a=p.parse_args(); warnings=[]
    argv=[a.python,a.entrypoint,'--model-repository',a.model_repository,'--host',a.host,'--openai-port',str(a.openai_port),'--uvicorn-log-level',a.uvicorn_log_level,'--model-control-mode',a.model_control_mode]
    if a.tokenizer: argv += ['--tokenizer', a.tokenizer]
    if a.backend: argv += ['--backend', a.backend]
    if a.load_model:
        if a.model_control_mode != 'explicit': warnings.append('--load-model requires --model-control-mode explicit.')
        if '*' in a.load_model and len(a.load_model)>1: warnings.append('--load-model=* must be the only --load-model value.')
        for m in a.load_model: argv += ['--load-model', m]
    if a.enable_kserve_frontends: argv += ['--enable-kserve-frontends','--kserve-http-port',str(a.kserve_http_port),'--kserve-grpc-port',str(a.kserve_grpc_port)]
    if a.http_max_input_size: argv += ['--http-max-input-size', str(a.http_max_input_size)]
    if a.lora_separator: argv += ['--lora-separator', a.lora_separator]
    if a.tool_call_parser: argv += ['--tool-call-parser', a.tool_call_parser]
    if a.max_tool_call_parse_bytes: argv += ['--max-tool-call-parse-bytes', str(a.max_tool_call_parse_bytes)]
    if a.chat_template: argv += ['--chat-template', a.chat_template]
    for item in a.restricted_api or []:
        parts=item.split(':',2)
        if len(parts)!=3: warnings.append(f'could not parse restricted-api {item!r}; expected APIs:key:value')
        else: argv += ['--openai-restricted-api', parts[0], parts[1], parts[2]]
    out={'argv':argv,'shell':q(argv),'warnings':warnings,'notes':['Command plan only; run inside an approved Triton OpenAI frontend runtime/container with the selected backend and model repository.']}
    print(json.dumps(out, indent=2, sort_keys=True) if a.json else out['shell'])
    if not a.json:
        [print('warning:',w) for w in warnings]; [print('note:',n) for n in out['notes']]
    return 1 if warnings else 0

if __name__=='__main__': raise SystemExit(main())
