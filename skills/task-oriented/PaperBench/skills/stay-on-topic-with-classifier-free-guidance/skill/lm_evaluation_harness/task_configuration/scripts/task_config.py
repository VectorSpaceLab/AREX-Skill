def render_template(template, doc):
    out = str(template)
    for k, v in doc.items():
        out = out.replace('{{'+k+'}}', str(v))
    if '{{' in out or '}}' in out:
        raise ValueError('unresolved template placeholder')
    return out

def validate_task_config(cfg):
    required=['task','output_type','doc_to_text','doc_to_target','metric_list']
    missing=[k for k in required if k not in cfg]
    if missing: raise ValueError('missing fields: '+','.join(missing))
    if cfg['output_type']=='multiple_choice' and 'doc_to_choice' not in cfg:
        raise ValueError('multiple_choice requires doc_to_choice')
    return True

def format_instance(cfg, doc):
    validate_task_config(cfg)
    inst={'task':cfg['task'],'context':render_template(cfg['doc_to_text'],doc),'output_type':cfg['output_type'],'metrics':list(cfg['metric_list']),'metadata':cfg.get('metadata',{})}
    target=cfg['doc_to_target']
    inst['target']=doc[target] if isinstance(target,str) and target in doc else render_template(target,doc)
    if 'doc_to_choice' in cfg:
        key=cfg['doc_to_choice']; inst['choices']=list(doc[key] if isinstance(key,str) and key in doc else key)
    return inst
