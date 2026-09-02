from fit_accuracy_line import fit_accuracy_line

def test_known_line_fit():
    records=[{'model_id':str(i),'id_accuracy':x,'ood_accuracy':0.8*x+0.1} for i,x in enumerate([0.5,0.6,0.7,0.8])]
    result=fit_accuracy_line(records)
    assert abs(result['slope'] - 0.8) < 1e-9
    assert abs(result['intercept'] - 0.1) < 1e-9
    assert result['pearson_r'] > 0.999999
    assert result['mean_absolute_residual'] < 1e-12

def test_zero_variance_rejected():
    try:
        fit_accuracy_line([{'model_id':'a','id_accuracy':0.7,'ood_accuracy':0.5},{'model_id':'b','id_accuracy':0.7,'ood_accuracy':0.6}])
    except ValueError as exc:
        assert 'variance' in str(exc)
    else:
        raise AssertionError('zero variance accepted')


def test_noisy_line_keeps_high_correlation():
    records=[
        {'model_id':'a','id_accuracy':0.60,'ood_accuracy':0.50},
        {'model_id':'b','id_accuracy':0.70,'ood_accuracy':0.58},
        {'model_id':'c','id_accuracy':0.80,'ood_accuracy':0.67},
        {'model_id':'d','id_accuracy':0.90,'ood_accuracy':0.76},
    ]
    result=fit_accuracy_line(records)
    assert result['pearson_r'] > 0.99
    assert result['mean_absolute_residual'] < 0.01
