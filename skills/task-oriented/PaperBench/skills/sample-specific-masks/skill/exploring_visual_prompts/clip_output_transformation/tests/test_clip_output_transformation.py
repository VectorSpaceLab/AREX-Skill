
from clip_output_transformation import build_text_prompts, predict_label

def test_prompt_and_argmax():
    labels=['red','blue']
    assert build_text_prompts(labels)[0] == 'This is a photo of a red'
    pred=predict_label([1,0], [[1,0],[0,1]], labels)
    assert pred['label']=='red'
    assert abs(sum(pred['probabilities'])-1.0) < 1e-9


def test_custom_template_for_dataset_labels():
    from clip_output_transformation import build_text_prompts
    assert build_text_prompts(['three'], 'This is a photo of {label} objects') == ['This is a photo of three objects']
