#!/usr/bin/env python3
"""Safely inspect a YOLOX Exp without starting training/evaluation."""
from __future__ import annotations
import argparse, json, os, sys, traceback
from collections import OrderedDict

class Reporter:
    def __init__(self): self.errors=[]; self.warnings=[]; self.notes=[]
    def error(self,m): self.errors.append(m); print('[ERROR] '+m)
    def warn(self,m): self.warnings.append(m); print('[WARN]  '+m)
    def note(self,m): self.notes.append(m); print('[INFO]  '+m)

def section(t): print('\n'+t); print('-'*len(t))
def abspath(p):
    if p is None: return None
    p=os.path.expandvars(os.path.expanduser(str(p)))
    return p if os.path.isabs(p) else os.path.abspath(p)
def looks_size(v): return isinstance(v,(tuple,list)) and len(v)==2 and all(isinstance(x,int) and x>0 for x in v)

def get_datadir(rep):
    try:
        from yolox.data import get_yolox_datadir
        return get_yolox_datadir()
    except Exception as e:
        rep.warn(f'Could not resolve YOLOX data dir helper: {e}'); return None

def load_exp(args, rep):
    try:
        import yolox
        from yolox.exp import get_exp
        print('YOLOX package version : {}'.format(getattr(yolox,'__version__','unknown')))
    except Exception as e:
        rep.error(f'Could not import YOLOX package: {e}'); return None
    if args.exp_file and args.name: rep.warn('Both --exp-file and --name supplied; YOLOX uses --exp-file first.')
    try: return get_exp(args.exp_file,args.name)
    except Exception as e:
        rep.error(f'Failed to load Exp: {e}')
        if args.show_traceback: traceback.print_exc()
        return None

def apply_opts(exp, opts, rep):
    if not opts: return
    if len(opts)%2: rep.error(f'--opts must contain key/value pairs; got {opts!r}'); return
    missing=[k for k in opts[0::2] if not hasattr(exp,k)]
    if missing: rep.warn('These --opts keys are not Exp attributes and may be ignored: '+', '.join(missing))
    try: exp.merge(opts); rep.note(f'Applied --opts: {opts!r}')
    except Exception as e: rep.error(f'Exp.merge failed: {e}')

def print_summary(exp,args):
    section('Loaded Exp summary')
    fields=OrderedDict([('exp class', exp.__class__.__module__+'.'+exp.__class__.__name__), ('source', args.exp_file or args.name)])
    for k in 'exp_name output_dir num_classes depth width act input_size test_size multiscale_range random_size data_dir train_ann val_ann test_ann data_num_workers max_epoch warmup_epochs no_aug_epochs basic_lr_per_img min_lr_ratio scheduler ema print_interval eval_interval save_history_ckpt mosaic_prob mixup_prob enable_mixup hsv_prob flip_prob test_conf nmsthre'.split():
        if hasattr(exp,k): fields[k]=getattr(exp,k)
    w=max(len(k) for k in fields)
    for k,v in fields.items(): print(f'{k:<{w}} : {v!r}' if not isinstance(v,str) else f'{k:<{w}} : {v}')

def validate(exp,rep):
    section('Configuration diagnostics')
    nc=getattr(exp,'num_classes',None)
    rep.note(f'num_classes is {nc}.') if isinstance(nc,int) and nc>0 else rep.error(f'exp.num_classes should be a positive integer; got {nc!r}.')
    inp=getattr(exp,'input_size',None); tst=getattr(exp,'test_size',None)
    if not looks_size(inp): rep.error(f'exp.input_size should be two positive ints; got {inp!r}.')
    elif inp[0]%32 or inp[1]%32: rep.error(f'exp.input_size should be divisible by 32; got {inp!r}.')
    else: rep.note(f'input_size is valid and divisible by 32: {inp!r}.')
    if not looks_size(tst): rep.warn(f'exp.test_size should be two positive ints; got {tst!r}.')
    elif looks_size(inp) and tuple(tst)!=tuple(inp): rep.warn(f'test_size {tst!r} differs from input_size {inp!r}; ensure this is deliberate.')
    else: rep.note(f'test_size is {tst!r}.')
    mr=getattr(exp,'multiscale_range',None); rs=getattr(exp,'random_size',None)
    if mr==0 and hasattr(exp,'random_size'): rep.warn(f'multiscale_range is 0 but random_size is set to {rs!r}; remove random_size for single-scale training.')
    if isinstance(getattr(exp,'max_epoch',None),int) and isinstance(getattr(exp,'no_aug_epochs',None),int) and exp.no_aug_epochs>=exp.max_epoch: rep.warn('no_aug_epochs is greater than or equal to max_epoch; mosaic may close from the start.')

def read_json(p,rep):
    try:
        with open(p,'r',encoding='utf-8') as f: return json.load(f)
    except Exception as e: rep.error(f'Could not read JSON {p}: {e}'); return None

def check_coco(exp,args,rep):
    section('COCO data checks')
    root=abspath(getattr(exp,'data_dir',None))
    if not root:
        d=get_datadir(rep); root=abspath(os.path.join(d,'COCO')) if d else None
    print('Resolved COCO root : {}'.format(root))
    if not root or not os.path.isdir(root): rep.error('COCO root does not exist; set YOLOX_DATADIR or exp.data_dir.'); return
    for split,ann in [('train2017',getattr(exp,'train_ann','instances_train2017.json')),('val2017',getattr(exp,'val_ann','instances_val2017.json'))]:
        imgdir=os.path.join(root,split); annp=os.path.join(root,'annotations',ann)
        if not os.path.isdir(imgdir): rep.error(f'Missing COCO image directory: {imgdir}')
        if not os.path.isfile(annp): rep.error(f'Missing COCO annotation file: {annp}'); continue
        data=read_json(annp,rep) or {}; cats=data.get('categories',[]); imgs=data.get('images',[])
        print(f'  {ann}: {len(imgs)} images, {len(cats)} categories')
        if cats and isinstance(getattr(exp,'num_classes',None),int) and len(cats)!=exp.num_classes: rep.warn(f'{ann} has {len(cats)} categories but exp.num_classes is {exp.num_classes}.')
        for im in imgs[:args.sample_images]:
            fn=im.get('file_name') if isinstance(im,dict) else None
            if fn and not os.path.isfile(os.path.join(imgdir,fn)): rep.error(f'Image referenced by {ann} not found: {os.path.join(imgdir,fn)}')

def check_voc(exp,args,rep):
    section('VOC data checks')
    root=abspath(getattr(exp,'data_dir',None))
    if not root:
        d=get_datadir(rep); root=abspath(os.path.join(d,'VOCdevkit')) if d else None
    print('Resolved VOC root : {}'.format(root))
    if not root or not os.path.isdir(root): rep.error('VOCdevkit root does not exist; set YOLOX_DATADIR or exp.data_dir.'); return
    if getattr(exp,'num_classes',None)!=20: rep.warn('Default VOC classes are 20; confirm custom class mapping/evaluator.')
    found=False
    for year,split in [('2007','trainval'),('2012','trainval'),('2007','test')]:
        base=os.path.join(root,'VOC'+year); sf=os.path.join(base,'ImageSets','Main',split+'.txt')
        if not os.path.isfile(sf): continue
        found=True; print(f'  VOC{year} {split}: {sf}')
        ids=[l.strip() for l in open(sf,encoding='utf-8') if l.strip()]
        for iid in ids[:args.sample_images]:
            for kind,path in [('annotation',os.path.join(base,'Annotations',iid+'.xml')),('image',os.path.join(base,'JPEGImages',iid+'.jpg'))]:
                if not os.path.isfile(path): rep.error(f'Missing VOC {kind}: {path}')
    if not found: rep.error('No common VOC split files were found.')

def build_model(exp,rep):
    section('Optional model-head check')
    try: model=exp.get_model()
    except Exception as e: rep.error(f'exp.get_model() failed: {e}'); return
    hn=getattr(getattr(model,'head',None),'num_classes',None); print('model.head.num_classes : {}'.format(hn))
    if hn is not None and hn!=getattr(exp,'num_classes',None): rep.error('model head class count does not match exp.num_classes')
    else: rep.note('Model head class count matches exp.num_classes.' if hn is not None else 'Model head count was not exposed.')

def parser():
    p=argparse.ArgumentParser(description='Inspect a YOLOX Exp safely without starting training/evaluation.')
    p.add_argument('--name','-n'); p.add_argument('--exp-file','-f'); p.add_argument('--opts',nargs='*')
    p.add_argument('--check-data',action='store_true'); p.add_argument('--expected-format',choices=['coco','voc','none'],default='none')
    p.add_argument('--sample-images',type=int,default=3); p.add_argument('--build-model',action='store_true'); p.add_argument('--show-traceback',action='store_true')
    return p

def main(argv=None):
    args=parser().parse_args(argv); rep=Reporter()
    if not args.name and not args.exp_file: rep.error('Provide --name or --exp-file.'); return 2
    exp=load_exp(args,rep)
    if exp is None: return 1
    apply_opts(exp,args.opts,rep); print_summary(exp,args); validate(exp,rep)
    section('Data checks')
    if args.check_data and args.expected_format=='coco': check_coco(exp,args,rep)
    elif args.check_data and args.expected_format=='voc': check_voc(exp,args,rep)
    elif args.check_data: rep.warn('--check-data set but --expected-format is none; no dataset layout checked.')
    else: rep.note('Skipped. Re-run with --check-data --expected-format {coco,voc} to validate common dataset paths.')
    if args.build_model: build_model(exp,rep)
    section('Summary'); print(f'errors   : {len(rep.errors)}'); print(f'warnings : {len(rep.warnings)}'); print(f'notes    : {len(rep.notes)}')
    if rep.errors: print('Result   : FAIL - fix errors before expensive training/evaluation.'); return 1
    if rep.warnings: print('Result   : PASS_WITH_WARNINGS - review warnings before full runs.'); return 0
    print('Result   : PASS'); return 0
if __name__=='__main__': sys.exit(main())
