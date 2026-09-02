from prompt_render import render_template, render_many


def test_render_and_label_consistency():
    ex={'id':'s1','dataset_id':'sentiment','text':'Great food','label':'positive'}
    templates=[{'dataset_id':'sentiment','task_family':'sentiment','template_id':'t1','input_format':'Review: {text} Sentiment?','target_field':'label'}, {'dataset_id':'sentiment','task_family':'sentiment','template_id':'t2','input_format':'Is this positive or negative: {text}','target_field':'label'}]
    out=render_many([ex], templates)
    assert len(out)==2
    assert {r['target'] for r in out}=={'positive'}
    assert out[0]['source'] != out[1]['source']


def test_missing_field_fails():
    try:
        render_template({'dataset_id':'x','label':'yes'}, {'dataset_id':'x','template_id':'t','input_format':'{text}','target_field':'label'})
    except KeyError as e:
        assert 'missing fields' in str(e)
    else:
        raise AssertionError('expected KeyError')
