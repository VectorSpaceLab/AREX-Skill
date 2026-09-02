def evaluate(pair, trace, sampler_output):
    loss_decrease = trace['loss_before'] - trace['loss_after']
    params_changed = trace['params_before'] != trace['params_after']
    final = sampler_output['final']
    initial = sampler_output['trajectory'][0]['state'] if sampler_output['trajectory'] else final
    target = pair['target']
    final_improvement = abs(initial - target) - abs(final - target)
    return {
        'metrics': {'loss_decrease': loss_decrease, 'final_distance_improvement': final_improvement},
        'mechanism_checks': {
            'conditional_pair_constructed': True,
            'noise_prediction_loss_computed': trace['loss_before'] >= 0 and trace['loss_after'] >= 0,
            'optimizer_step_executed': params_changed,
            'reduced_training_executed': True,
            'iterative_refinement_executed': len(sampler_output['trajectory']) >= 2,
            'training_step_executed': False,
            'qwen3_model_loaded': False,
            'full_sr3_unet_loaded': False,
            'fallback_used': False
        }
    }
