#!/usr/bin/env python3
import json, argparse

def trainable_map(names, bias='none'):
    result={}
    for name in names:
        if 'lora_' in name:
            result[name]=True
        elif bias == 'all' and name.endswith('bias'):
            result[name]=True
        elif bias == 'lora_only' and name.endswith('bias') and 'lora_' in name:
            result[name]=True
        else:
            result[name]=False
    return result

def lora_state_dict(params, bias='none'):
    keep={}
    trainable=trainable_map(params.keys(), bias)
    for name, value in params.items():
        if 'lora_' in name or (bias != 'none' and trainable.get(name, False)):
            keep[name]=value
    return keep

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input', required=True); ap.add_argument('--bias', default='none')
    ns=ap.parse_args(); data=json.load(open(ns.input))
    params=data['parameters']
    print(json.dumps({'trainable':trainable_map(params.keys(), ns.bias),'checkpoint':lora_state_dict(params, ns.bias)}, indent=2))
if __name__ == '__main__': main()
