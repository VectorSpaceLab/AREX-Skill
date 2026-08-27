#!/usr/bin/env python3
"""Check an installed PyMuPDF environment without external files or network access."""
from __future__ import annotations
import argparse, importlib.util, json, shutil, subprocess, sys
from importlib import metadata
from pathlib import Path

def opt(name): return 'available' if importlib.util.find_spec(name) else 'missing'

def main():
    ap=argparse.ArgumentParser(description='Check PyMuPDF import, metadata, CLI help, optional components, and a tiny API smoke.')
    ap.add_argument('--json', action='store_true'); ap.add_argument('--output-pdf'); ap.add_argument('--cli-timeout', type=float, default=10.0)
    args=ap.parse_args(); report={'python':sys.version.split()[0]}
    try:
        import pymupdf
        report['distribution']={'name':metadata.metadata('pymupdf')['Name'],'version':metadata.version('pymupdf'),'requires_python':metadata.metadata('pymupdf').get('Requires-Python')}
        report['import']={'status':'passed','version':getattr(pymupdf,'__version__',None)}
        report['legacy_fitz']={'status':'available-deprecated' if importlib.util.find_spec('fitz') else 'missing-not-required'}
        cp=subprocess.run([sys.executable,'-m','pymupdf','--help'], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=args.cli_timeout)
        report['cli']={'status':'passed' if cp.returncode==0 and 'Subcommands' in cp.stdout else 'failed','returncode':cp.returncode,'stdout_preview':cp.stdout[:300],'stderr_preview':cp.stderr[:300]}
        doc=pymupdf.open(); page=doc.new_page(width=200,height=120); page.insert_text((36,72),'PyMuPDF environment smoke')
        reopened=pymupdf.open(stream=doc.tobytes(garbage=3,deflate=True), filetype='pdf'); text=reopened[0].get_text().strip(); pix=reopened[0].get_pixmap(dpi=72)
        if args.output_pdf: Path(args.output_pdf).parent.mkdir(parents=True, exist_ok=True); reopened.save(args.output_pdf, garbage=3, deflate=True)
        report['api_smoke']={'status':'passed' if text=='PyMuPDF environment smoke' and pix.width>0 else 'failed','text':text,'pixmap':[pix.width,pix.height]}
        report['optional_components']={'pymupdf4llm':opt('pymupdf4llm'),'pymupdf.pro':opt('pymupdf.pro'),'Pillow':opt('PIL'),'fontTools':opt('fontTools'),'pandas':opt('pandas'),'tabulate':opt('tabulate'),'tesseract_binary':shutil.which('tesseract') or 'missing'}
    except Exception as e:
        report['error']=repr(e)
    report['status']='passed' if report.get('import',{}).get('status')=='passed' and report.get('cli',{}).get('status')=='passed' and report.get('api_smoke',{}).get('status')=='passed' else 'failed'
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else 'PyMuPDF environment check: '+report['status']+'\n'+json.dumps(report, indent=2, sort_keys=True))
    return 0 if report['status']=='passed' else 2
if __name__=='__main__': raise SystemExit(main())
