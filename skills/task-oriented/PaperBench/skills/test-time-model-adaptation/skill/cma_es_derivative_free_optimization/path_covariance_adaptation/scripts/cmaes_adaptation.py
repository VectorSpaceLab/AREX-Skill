import math

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a))
def add(a,b): return [x+y for x,y in zip(a,b)]
def scale(s,v): return [s*x for x in v]
def outer(a,b): return [[x*y for y in b] for x in a]
def mat_add(a,b): return [[a[i][j]+b[i][j] for j in range(len(a))] for i in range(len(a))]
def mat_scale(s,a): return [[s*x for x in row] for row in a]
def eigvals_2(c):
    tr=c[0][0]+c[1][1]; det=c[0][0]*c[1][1]-c[0][1]*c[1][0]
    disc=max(tr*tr-4*det,0.0); r=math.sqrt(disc)
    return [max((tr-r)/2,1e-12), max((tr+r)/2,1e-12)]

def sym_floor_2(c):
    c=[[0.5*(c[i][j]+c[j][i]) for j in range(2)] for i in range(2)]
    vals=eigvals_2(c)
    if min(vals) < 1e-10:
        bump=1e-10-min(vals)
        c[0][0]+=bump; c[1][1]+=bump
        vals=eigvals_2(c)
    return c, vals

def adapt_paths_covariance(p_sigma, p_c, sigma, covariance, y_w, selected_y, selected_z, params):
    weights=list(map(float, params['weights'])); n=len(y_w)
    z_w=[sum(weights[i]*selected_z[i][j] for i in range(len(weights))) for j in range(n)]
    cs, ds, cc, c1, cmu, mueff = [float(params[k]) for k in ['cs','ds','cc','c1','cmu','mueff']]
    p_sigma_new=add(scale(1.0-cs, p_sigma), scale(math.sqrt(cs*(2.0-cs)*mueff), z_w))
    sigma_new=float(sigma)*math.exp((cs/ds)*((norm(p_sigma_new)/float(params['expected_norm']))-1.0))
    p_c_new=add(scale(1.0-cc, p_c), scale(math.sqrt(cc*(2.0-cc)*mueff), y_w))
    rank_mu=[[0.0 for _ in range(n)] for _ in range(n)]
    for w,y in zip(weights, selected_y): rank_mu=mat_add(rank_mu, mat_scale(w, outer(y,y)))
    c_new=mat_add(mat_add(mat_scale(1.0-c1-cmu, covariance), mat_scale(c1, outer(p_c_new,p_c_new))), mat_scale(cmu, rank_mu))
    vals=[]
    if n==2: c_new, vals=sym_floor_2(c_new)
    else: vals=[max(c_new[i][i],1e-12) for i in range(n)]
    return {'p_sigma':p_sigma_new,'p_c':p_c_new,'sigma':sigma_new,'covariance':c_new,'eigenvalues':vals,'condition_number':max(vals)/min(vals),'sigma_changed':abs(sigma_new-float(sigma))>1e-15,'covariance_changed':c_new!=covariance}
