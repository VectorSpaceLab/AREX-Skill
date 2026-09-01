try:
    from guided_score import guided_score
except Exception:
    def guided_score(cond, uncond, w):
        return (1 + w) * cond - w * uncond

def sample_proxy(noises, class_mean, global_mean, w, steps=5, step_size=0.25):
    xs=list(noises); trace=[]
    for t in range(steps):
        new=[]
        for x in xs:
            cond=x-class_mean
            uncond=x-global_mean
            g=guided_score(cond, uncond, w)
            x2=x-step_size*g
            trace.append({'step':t,'x_before':x,'eps_cond':cond,'eps_uncond':uncond,'eps_guided':g,'x_after':x2})
            new.append(x2)
        xs=new
    return {'samples':xs,'trace':trace,'w':w,'steps':steps}
