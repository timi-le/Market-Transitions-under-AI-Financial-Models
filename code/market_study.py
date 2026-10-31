"""Reduced-form market-feedback diagnostic. Synthetic, not a calibrated exchange.
Run from release root: python code/market_study.py
All price paths respond to orders. No private strategy or external service used.
"""
from pathlib import Path
import itertools, json, hashlib, platform
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONFIG = dict(seed=20260920, replicates=64, participants=24, steps=360,
              burn=60, shock_at=180, kappa=.06, impact=.012,
              fee=.0002, spread=.0005, stress_threshold=.10,
              persistence=5, recovery_band=.02, minimum_depth=.12, return_cap=.25)
POLICIES = ['ungated','risk_only','evidence_gate','wrong_evidence']

def train_experts():
    """Two fixed-hidden-layer tanh networks; output layers fit by ridge.
    Oracle-labelled synthetic training regimes are separate from market tests.
    """
    rng=np.random.default_rng(1806)
    x=rng.uniform(-3,3,4096)
    w=rng.normal(size=12); b=rng.normal(size=12)
    h=np.column_stack([np.ones(len(x)), np.tanh(x[:,None]*w+b)])
    y=np.column_stack([x,-x])+.15*rng.normal(size=(len(x),2))
    v=np.linalg.solve(h.T@h+.01*np.eye(13),h.T@y)
    return w,b,v

def neural_forecasts(x, weights):
    w,b,v=weights
    h=np.concatenate([np.ones(x.shape+(1,)),np.tanh(x[...,None]*w+b)],axis=-1)
    return h@v

def innovations(cfg):
    rng=np.random.default_rng(cfg['seed'])
    r,n,t=cfg['replicates'],cfg['participants'],cfg['steps']
    return dict(x=rng.normal(size=(t,r)), z=rng.random((t,r)),
                emit=rng.normal(size=(t,r)), common=rng.normal(size=(t,r)),
                private=rng.normal(size=(t,r,n)), noise=rng.normal(size=(t,r)),
                stale=rng.random((t,r,n)))

def simulate(phi, similarity, speed, leverage, shock, policy, cfg, noise, weights, trace=False):
    r,n,T=cfg['replicates'],cfg['participants'],cfg['steps']
    F=np.zeros(r); p=np.zeros(r); last_r=np.zeros(r); depth=np.ones(r)
    pos=np.zeros((r,n)); cash=np.ones((r,n)); z=np.zeros(r,dtype=int)
    q=np.full(r,.5); forecast_err=np.ones((r,n))
    cost_total=np.zeros(r); turn_total=np.zeros(r); obs=0
    peak=np.ones(r); dd=np.zeros(r); low=np.ones(r)
    breaches=np.zeros(r,dtype=int); crash=np.zeros(r,dtype=bool)
    down_breaches=np.zeros(r,dtype=int); downside=np.zeros(r,dtype=bool)
    market_peak=np.zeros(r); market_dd=np.zeros(r); dd_breaches=np.zeros(r,dtype=int); dd_event=np.zeros(r,dtype=bool)
    recovery=np.full(r,-1,dtype=int); recover_count=np.zeros(r,dtype=int)
    mse=np.zeros(r); coverage=np.zeros(r); action_sync=np.zeros(r); intensity=np.zeros(r)
    censored_clip=np.zeros(r,dtype=int); traces=[]
    for t in range(T):
        oldp=p.copy(); oldpos=pos.copy(); oldwealth=cash+pos*np.exp(p)[:,None]
        # Current public emission and surprise arrive before orders; outcome after.
        z=np.where(noise['z'][t]<.03,1-z,z)
        obs_m=(2*z-1)*.7+1.3*noise['emit'][t]
        prior=.03+.94*q
        l0=np.exp(-.5*((obs_m+.7)/1.3)**2)
        l1=np.exp(-.5*((obs_m-.7)/1.3)**2)
        q=prior*l1/((1-prior)*l0+prior*l1)
        x=noise['x'][t]
        correlated=np.sqrt(similarity)*noise['common'][t,:,None]+np.sqrt(1-similarity)*noise['private'][t]
        measured=x[:,None]+.35*correlated
        pred2=neural_forecasts(measured,weights)
        # Expert zero estimates +x, one estimates -x; state zero uses +x.
        qi=q if policy!='wrong_evidence' else 1-q
        forecast=(1-qi[:,None])*pred2[:,:,0]+qi[:,None]*pred2[:,:,1]
        confidence=np.maximum(q,1-q)[:,None]
        timely=noise['stale'][t]>.05
        eligible=timely & (confidence>=.65) & (forecast_err<2.5)
        macro=np.tanh(forecast)
        # Same momentum term for all architectures. Evidence contracts regulate
        # macro proposal admission; liquidity risk is a separately ablated cap.
        momentum=np.tanh(last_r[:,None]/.008+correlated*.1)
        signal=.5*macro+.5*momentum
        if policy in ('evidence_gate','wrong_evidence'):
            signal=np.where(eligible,signal,0.)
        risk_cap=np.ones(r) if policy=='ungated' else np.minimum(1.,depth/.5)
        target=leverage*risk_cap[:,None]*np.tanh(signal*1.5)
        # Approximate leverage target against current positive marked wealth.
        target=target*np.maximum(oldwealth,.01)/np.exp(p)[:,None]
        target=np.where(oldwealth>.5,target,0.)
        pos=oldpos+speed*(target-oldpos)
        flow=pos-oldpos
        impact=cfg['impact']*phi*flow.mean(axis=1)/depth
        fundamental_step=.001*np.where(z==0,1.,-1.)*x+.0005*noise['noise'][t]
        shock_step=-shock if t==cfg['shock_at'] else 0.
        F=F+fundamental_step+shock_step
        # Background stabilizing supply decreases as model participation grows.
        raw_r=fundamental_step+shock_step-cfg['kappa']*(1-.7*phi)*(p-(F-fundamental_step-shock_step))+impact
        rr=np.clip(raw_r,-cfg['return_cap'],cfg['return_cap']); censored_clip+=(raw_r!=rr)
        p=p+rr
        execution=(np.exp(oldp)+np.exp(p))/2
        cost=np.abs(flow)*execution[:,None]*(cfg['fee']+cfg['spread']/depth[:,None])
        cash=cash-flow*execution[:,None]-cost
        wealth=cash+pos*np.exp(p)[:,None]
        port=wealth.mean(axis=1)
        if t==cfg['burn']-1:
            anchor=port.copy(); peak=port.copy()
        if t>=cfg['burn']:
            obs+=1
            peak=np.maximum(peak,port); dd=np.minimum(dd,port/peak-1)
            cost_total+=cost.mean(axis=1); turn_total+=np.abs(flow).mean(axis=1)
            low=np.minimum(low,depth); mse+=(forecast-np.where(z==0,1.,-1.)[:,None]*x[:,None]).__pow__(2).mean(axis=1)
            coverage+=eligible.mean(axis=1)
            action_sync+=np.abs(np.sign(flow).mean(axis=1))
            intensity+=np.abs(flow).mean(axis=1)
        # Liquidity is an endogenous stress proxy, not measured book depth.
        depth=np.clip(depth+.08*(1-depth)-3*np.abs(rr)-.012*phi*np.abs(flow).mean(axis=1),cfg['minimum_depth'],1.)
        if t>=cfg['burn']: low=np.minimum(low,depth)
        displacement=p-F
        if t>=cfg['burn']:
            breaches=np.where(np.abs(displacement)>=cfg['stress_threshold'],breaches+1,0)
            crash|=breaches>=cfg['persistence']
            down_breaches=np.where(displacement<=-cfg['stress_threshold'],down_breaches+1,0)
            downside|=down_breaches>=cfg['persistence']
            market_peak=np.maximum(market_peak,p)
            current_dd=np.exp(p-market_peak)-1
            market_dd=np.minimum(market_dd,current_dd)
            dd_breaches=np.where(current_dd<=-.15,dd_breaches+1,0)
            dd_event|=dd_breaches>=cfg['persistence']
        else: market_peak=p.copy()
        if t>=cfg['shock_at']:
            ok=(np.abs(displacement)<cfg['recovery_band']) & (depth>=.8)
            recover_count=np.where(ok,recover_count+1,0)
            newly=(recover_count>=5)&(recovery<0)
            recovery[newly]=t-cfg['shock_at']
        outcome=np.where(z==0,1.,-1.)[:,None]*x[:,None]+.5*noise['noise'][t,:,None]
        forecast_err=.95*forecast_err+.05*(forecast-outcome)**2
        last_r=rr
        if trace and t%1==0:
            traces.append(dict(t=t,price=float(np.exp(p[0])),fundamental=float(np.exp(F[0])),depth=float(depth[0]),equity=float(port[0]),coverage=float(eligible[0].mean())))
    # Liquidate at the terminal midpoint, charging stated spread and fee.
    terminal_cost=np.abs(pos)*np.exp(p)[:,None]*(cfg['fee']+cfg['spread']/depth[:,None])
    final=(cash+pos*np.exp(p)[:,None]-terminal_cost).mean(axis=1)
    dd=np.minimum(dd,final/peak-1)
    rows=[]
    for i in range(r):
        rows.append(dict(phi=phi,similarity=similarity,speed=speed,leverage=leverage,shock=shock,policy=policy,replicate=i,
          net_return=final[i]/anchor[i]-1,max_drawdown=dd[i],minimum_depth=low[i],
          stress_event=int(crash[i]),downside_dislocation=int(downside[i]),price_drawdown_event=int(dd_event[i]),market_drawdown=market_dd[i],recovery=recovery[i],unrecovered=int(recovery[i]<0),
          forecast_mse=mse[i]/obs,coverage=coverage[i]/obs,order_synchrony=action_sync[i]/obs,
          cost=cost_total[i]+terminal_cost[i].mean(),turnover=turn_total[i],clip_count=censored_clip[i]))
    return rows,traces

def main():
    root=ROOT/'results';root.mkdir(exist_ok=True)
    weights=train_experts(); noise=innovations(CONFIG)
    np.savez(root/'neural_experts.npz',w=weights[0],b=weights[1],v=weights[2])
    records=[]; traces=[]
    grid=list(itertools.product([0.,.25,.5,.75],[0.,.85],[.1,.8],[1.,3.],[0.,.08],POLICIES))
    for k,args in enumerate(grid):
        rows,trace=simulate(*args,CONFIG,noise,weights,trace=(args[:5]==(.75,.85,.8,3.,.08)))
        records.extend(rows)
        for row in trace: row['policy']=args[5]
        traces.extend(trace)
    raw=pd.DataFrame(records);raw.to_csv(root/'market_replicates.csv',index=False)
    group=['phi','similarity','speed','leverage','shock','policy']
    metrics=['net_return','max_drawdown','minimum_depth','stress_event','downside_dislocation','price_drawdown_event','market_drawdown','unrecovered','forecast_mse','coverage','order_synchrony','cost','turnover','clip_count']
    summary=raw.groupby(group,sort=False)[metrics].agg(['mean','std'])
    summary.columns=['_'.join(c) for c in summary.columns]
    for m in metrics:summary[m+'_mcse']=summary[m+'_std']/np.sqrt(CONFIG['replicates'])
    summary.reset_index().to_csv(root/'market_summary.csv',index=False)
    pd.DataFrame(traces).to_csv(root/'market_traces.csv',index=False)
    # Pair within seed and scenario; avoid treating time steps as independent.
    pairs=[]
    for keys,d in raw.groupby(group[:-1]):
        for a,b in [('evidence_gate','ungated'),('evidence_gate','risk_only'),('wrong_evidence','evidence_gate')]:
            aa=d[d.policy==a].set_index('replicate');bb=d[d.policy==b].set_index('replicate')
            for m in ['net_return','stress_event','minimum_depth','forecast_mse']:
                v=aa[m]-bb[m]
                pairs.append(dict(zip(group[:-1],keys),contrast=a+' - '+b,metric=m,mean=float(v.mean()),mcse=float(v.std(ddof=1)/np.sqrt(len(v)))))
    pd.DataFrame(pairs).to_csv(root/'market_paired.csv',index=False)
    manifest=dict(config=CONFIG,scenario_count=len(grid),trajectory_count=len(raw),
       scenario_grid={k:v for k,v in zip(group,[[0,.25,.5,.75],[0,.85],[.1,.8],[1,3],[0,.08],POLICIES])},
       python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,
       scope='synthetic reduced-form diagnostic; not production CMTF or calibrated crisis forecast',
       randomization='common innovations reused for matched scenarios; fixed trained neural experts',
       code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (root/'market_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({k:manifest[k] for k in ['scenario_count','trajectory_count','scope']},indent=2))
    print(raw.groupby('policy')[metrics].mean().to_string())

if __name__=='__main__':main()
