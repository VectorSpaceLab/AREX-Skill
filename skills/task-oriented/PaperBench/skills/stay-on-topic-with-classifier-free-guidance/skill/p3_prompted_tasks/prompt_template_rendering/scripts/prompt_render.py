import re
from string import Formatter


def required_fields(fmt):
    return [name for _, name, _, _ in Formatter().parse(fmt) if name]


def render_template(example, template):
    missing=[f for f in required_fields(template['input_format']) if f not in example]
    if missing:
        raise KeyError('missing fields: '+','.join(missing))
    source=template['input_format'].format(**example)
    raw=example[template['target_field']]
    choices=template.get('answer_choices') or {}
    target=choices.get(str(raw), choices.get(raw, raw))
    return {'dataset_id':template['dataset_id'],'task_family':template.get('task_family','unknown'),'example_id':example.get('id',''), 'template_id':template['template_id'],'source':source,'target':str(target),'label':str(raw)}


def render_many(examples, templates):
    return [render_template(ex,t) for ex in examples for t in templates if t['dataset_id']==ex['dataset_id']]
