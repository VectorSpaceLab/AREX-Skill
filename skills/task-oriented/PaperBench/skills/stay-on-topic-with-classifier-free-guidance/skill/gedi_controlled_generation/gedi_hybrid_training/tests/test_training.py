import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from gedi_train_proxy import losses, tiny_optimizer_step

l0 = losses(1.0, 0.0, 7.0, lam=0.0)
assert abs(l0['hybrid_loss'] - l0['discriminative_loss']) < 1e-12
l1 = losses(1.0, 0.0, 7.0, lam=1.0)
assert abs(l1['hybrid_loss'] - 7.0) < 1e-12

trace = tiny_optimizer_step(lam=0.6, lr=0.2)
assert trace['optimizer_step_executed']
assert trace['params_before'] != trace['params_after']
assert trace['loss_after'] < trace['loss_before']
assert 'params_before' in trace and 'params_after' in trace
print('gedi_hybrid_training tests passed')
