"""Declared post-audit numerical-cap sensitivity, not a tuned primary result."""
from pathlib import Path
import pandas as pd
from market_study import CONFIG, POLICIES, innovations, train_experts, simulate

if __name__=='__main__':
    noise=innovations(CONFIG);weights=train_experts();rows=[]
    for cap in [.125,.25,.5]:
        for shock in [0.,.08]:
            for policy in POLICIES:
                result,_=simulate(.75,.85,.8,3.,shock,policy,dict(CONFIG,return_cap=cap),noise,weights)
                for r in result:r['return_cap']=cap
                rows.extend(result)
    pd.DataFrame(rows).to_csv(Path(__file__).resolve().parents[1]/'results/cap_sensitivity.csv',index=False)
