#!/usr/bin/env python3
"""Safe YOLOX export helper for ONNX and TorchScript."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
from typing import Any, Iterable, Tuple
NAMES=("yolox-nano","yolox-tiny","yolox-s","yolox-m","yolox-l","yolox-x","yolov3")

def posint(v):
    i=int(v)
    if i<=0: raise argparse.ArgumentTypeError('must be positive')
    return i

def parser():
    p=argparse.ArgumentParser(description='Export an installed YOLOX checkpoint to ONNX or TorchScript.')
    p.add_argument('--format',choices=('onnx','torchscript'),default='onnx')
    p.add_argument('-n','--name',choices=NAMES); p.add_argument('-f','--exp-file')
    p.add_argument('-c','--checkpoint'); p.add_argument('--output')
    p.add_argument('--batch-size',type=posint,default=1); p.add_argument('--dynamic',action='store_true')
    p.add_argument('--opset',type=posint,default=11); p.add_argument('--decode-in-inference',action='store_true')
    p.add_argument('--input-name',default='images'); p.add_argument('--output-name',default='output')
    p.add_argument('--simplify',action='store_true'); p.add_argument('--dry-run',action='store_true')
    p.add_argument('opts',nargs=argparse.REMAINDER,help='Optional YOLOX Exp.merge key/value overrides.')
    return p

def validate(p,args):
    if not args.name and not args.exp_file: p.error('provide --name or --exp-file')
    if args.exp_file and not Path(args.exp_file).is_file(): p.error('--exp-file does not exist: '+args.exp_file)
    if args.format=='torchscript' and (args.dynamic or args.simplify or args.opset!=11): p.error('--dynamic, --simplify, and --opset are ONNX-only')
    if not args.dry_run:
        if not args.checkpoint: p.error('--checkpoint is required for real export; use --dry-run without weights')
        if not Path(args.checkpoint).is_file(): p.error('--checkpoint does not exist: '+args.checkpoint)
    args.output_path=Path(args.output or ('yolox.onnx' if args.format=='onnx' else 'yolox.torchscript.pt'))
    if args.output_path.exists() and args.output_path.is_dir(): p.error('--output points to a directory')
    return args

def imports():
    import torch
    from torch import nn
    from yolox.exp import get_exp
    from yolox.models.network_blocks import SiLU
    from yolox.utils import replace_module
    return torch,nn,get_exp,SiLU,replace_module

def load_exp(get_exp,args):
    exp=get_exp(args.exp_file,args.name)
    if hasattr(exp,'merge'): exp.merge(args.opts or [])
    return exp

def test_size(exp)->Tuple[int,int]:
    s=getattr(exp,'test_size',None); t=tuple(s) if isinstance(s,Iterable) else ()
    if len(t)!=2 or not all(isinstance(x,int) and x>0 for x in t): raise ValueError('Exp must expose positive two-int test_size')
    return int(t[0]),int(t[1])

def model(exp):
    m=exp.get_model()
    if not hasattr(m,'head') or not hasattr(m.head,'decode_in_inference'): raise ValueError('model does not look like YOLOX')
    return m

def state(torch,path):
    ckpt=torch.load(str(path),map_location='cpu')
    if isinstance(ckpt,dict) and 'model' in ckpt: ckpt=ckpt['model']
    if not hasattr(ckpt,'keys'): raise ValueError('checkpoint must be state_dict or contain model state_dict')
    return ckpt

def print_dry(args,exp,m,hw):
    print('YOLOX export dry-run')
    print('  format:',args.format); print('  model selector:',args.exp_file or args.name); print('  experiment name:',getattr(exp,'exp_name','<unknown>'))
    print(f'  test size: {hw[0]}x{hw[1]}'); print('  parameters:',format(sum(p.numel() for p in m.parameters()),','))
    print('  batch size:',args.batch_size); print('  decode in inference:',bool(args.decode_in_inference)); print('  checkpoint supplied:',bool(args.checkpoint)); print('  output file:',args.output_path)
    if args.format=='onnx': print('  opset:',args.opset); print('  dynamic batch axes:',bool(args.dynamic)); print('  input/output tensor names:',args.input_name+'/'+args.output_name); print('  simplify:',bool(args.simplify))

def export_onnx(torch,nn,SiLU,replace_module,args,m,hw):
    m.eval(); m=replace_module(m,nn.SiLU,SiLU); m.head.decode_in_inference=bool(args.decode_in_inference)
    x=torch.randn(args.batch_size,3,hw[0],hw[1]); axes={args.input_name:{0:'batch'},args.output_name:{0:'batch'}} if args.dynamic else None
    args.output_path.parent.mkdir(parents=True,exist_ok=True)
    with torch.no_grad(): torch.onnx.export(m,x,str(args.output_path),input_names=[args.input_name],output_names=[args.output_name],dynamic_axes=axes,opset_version=args.opset)
    if args.simplify:
        import onnx
        from onnxsim import simplify
        om=onnx.load(str(args.output_path)); sm,ok=simplify(om); assert ok, 'onnx-simplifier validation failed'; onnx.save(sm,str(args.output_path))
    print('Exported ONNX:',args.output_path)

def export_ts(torch,args,m,hw):
    m.eval(); m.head.decode_in_inference=bool(args.decode_in_inference); x=torch.randn(args.batch_size,3,hw[0],hw[1]); args.output_path.parent.mkdir(parents=True,exist_ok=True)
    with torch.no_grad(): torch.jit.trace(m,x).save(str(args.output_path))
    print('Exported TorchScript:',args.output_path)

def main(argv=None):
    p=parser(); args=validate(p,p.parse_args(argv))
    try:
        torch,nn,get_exp,SiLU,replace_module=imports(); exp=load_exp(get_exp,args); hw=test_size(exp); m=model(exp)
        if args.dry_run: print_dry(args,exp,m,hw); return 0
        m.load_state_dict(state(torch,Path(args.checkpoint)))
        if args.format=='onnx': export_onnx(torch,nn,SiLU,replace_module,args,m,hw)
        else: export_ts(torch,args,m,hw)
        return 0
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
