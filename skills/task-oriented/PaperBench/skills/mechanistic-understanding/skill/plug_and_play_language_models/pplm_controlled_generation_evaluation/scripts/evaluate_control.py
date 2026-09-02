import math

def evaluate(base_probs, controlled_probs, target_indices, gain_threshold=0.25, max_kl=1.5):
    eps=1e-12
    before=sum(base_probs[i] for i in target_indices); after=sum(controlled_probs[i] for i in target_indices)
    gain=after-before
    kl=sum(ci*math.log(max(ci,eps)/max(bi,eps)) for ci,bi in zip(controlled_probs,base_probs))
    return {'target_mass_before':before,'target_mass_after':after,'target_mass_gain':gain,'kl_to_base':kl,'passed': gain >= gain_threshold and kl <= max_kl}
