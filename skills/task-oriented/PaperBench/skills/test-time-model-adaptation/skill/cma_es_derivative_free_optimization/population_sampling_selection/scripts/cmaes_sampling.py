import math, random

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def mat_vec(m,v): return [sum(row[j]*v[j] for j in range(len(v))) for row in m]
def add(a,b): return [x+y for x,y in zip(a,b)]
def scale(s,v): return [s*x for x in v]
def outer(a,b): return [[x*y for y in b] for x in a]
def eye(n): return [[1.0 if i==j else 0.0 for j in range(n)] for i in range(n)]
def cholesky_spd_2(c):
    a=max(c[0][0],1e-12); b=c[1][0]; d=max(c[1][1],1e-12)
    l00=math.sqrt(a); l10=b/l00; rem=max(d-l10*l10,1e-12); l11=math.sqrt(rem)
    return [[l00,0.0],[l10,l11]]

def sample_and_select(mean, sigma, covariance, params, objective, rng):
    mean=list(map(float, mean)); n=len(mean)
    transform=cholesky_spd_2(covariance) if n==2 else eye(n)
    records=[]
    normal = rng.gauss if hasattr(rng, 'gauss') else random.gauss
    for _ in range(int(params['lambda'])):
        z=[normal(0.0,1.0) for _ in range(n)]
        y=mat_vec(transform,z)
        x=add(mean, scale(float(sigma), y))
        records.append({'x':x,'y':y,'z':z,'fitness':float(objective(x))})
    records.sort(key=lambda r:r['fitness'])
    mu=int(params['mu']); weights=list(map(float, params['weights']))
    selected_y=[records[i]['y'] for i in range(mu)]; selected_z=[records[i]['z'] for i in range(mu)]
    y_w=[sum(weights[i]*selected_y[i][j] for i in range(mu)) for j in range(n)]
    new_mean=add(mean, scale(float(params.get('cm',1.0))*float(sigma), y_w))
    return {'records':records,'selected_y':selected_y,'selected_z':selected_z,'y_w':y_w,'new_mean':new_mean,'best_fitness':records[0]['fitness']}
