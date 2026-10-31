
from pathlib import Path
import json, shutil, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"results"; M=ROOT/"manuscript"; S=M/"sections"; F=M/"figures"
LABEL={"ungated":"Ungated","risk_only":"Risk only","evidence_gate":"Evidence gate","wrong_evidence":"Wrong evidence"}
ORDER=list(LABEL)
COLORS=["#8B98A5","#BD713A","#167A89","#735A86"]
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False,"pdf.fonttype":42})

def tex_table(path,header,rows,cols,caption=None):
    out=[r"\begin{table}[htbp]\centering\small",r"\begin{tabular}{"+cols+r"}\toprule",header+r"\\\midrule"]
    out.extend(" & ".join(map(str,row))+r"\\" for row in rows)
    out += [r"\bottomrule\end{tabular}"]
    if caption:out += [r"\caption{"+caption+"}"]
    out += [r"\end{table}"]
    path.write_text("\n".join(out))

def long_table(path,header,rows,cols,note):
    out=[note,r"\begingroup\footnotesize\setlength{\tabcolsep}{4pt}",
         r"\begin{longtable}{"+cols+r"}\toprule",header+r"\\\midrule\endfirsthead",
         r"\toprule "+header+r"\\\midrule\endhead",r"\bottomrule\endfoot"]
    out.extend(" & ".join(map(str,row))+r"\\" for row in rows)
    out += [r"\end{longtable}\endgroup"]
    path.write_text("\n".join(out))

def main():
    S.mkdir(exist_ok=True);F.mkdir(exist_ok=True)
    syn=pd.read_csv(R/"synthetic_summary.csv")
    methods=["Pooled available adjustment","Filtered hard gate","Filtered soft gate","Oracle state gate"]
    rows=[]
    for name,d in syn.groupby("scenario",sort=False):
        row=[name]+[f"{d[d.method==m].iloc[0].mean_mse:.4f}" for m in methods]
        rows.append(row)
    tex_table(S/"synthetic_table.tex","Setting & Pooled & Hard & Soft & Oracle",rows,"lrrrr",
              "Mean coefficient MSE over 200 replications. Full losses and Monte Carlo errors appear in the appendix.")
    long_table(S/"synthetic_full.tex","Setting / method & MSE & MCSE & MAE",
       [[str(x.scenario)+" / "+str(x.method),f"{x.mean_mse:.6f}",f"{x.mcse_mse:.6f}",f"{x.mean_mae:.6f}"] for x in syn.itertuples()],
       "p{.63\\linewidth}rrr","All synthetic estimators, including negative and misspecified cases.")
    shutil.copy2(R/"synthetic_results.pdf",F/"synthetic_results.pdf")
    raw=pd.read_csv(R/"market_replicates.csv");g=raw.groupby("policy").mean(numeric_only=True)
    tex_table(S/"market_table.tex","Policy & Net return (\\%) & Dislocation (\\%) & No recovery (\\%) & MSE",
       [[LABEL[p],f"{100*g.loc[p,'net_return']:.2f}",f"{100*g.loc[p,'stress_event']:.2f}",f"{100*g.loc[p,'unrecovered']:.2f}",f"{g.loc[p,'forecast_mse']:.3f}"] for p in ORDER],
       "lrrrr","Descriptive averages across the 64 base parameter settings per policy. These settings receive equal weight; this is not an estimated real-market distribution.")
    sel=raw[(raw.phi==.75)&(raw.similarity==.85)&(raw.speed==.8)&(raw.leverage==3)&(raw.shock==.08)]
    fig,axs=plt.subplots(2,2,figsize=(10,6.8),layout="constrained")
    for ax,metric,title,mult in zip(axs.flat,["net_return","stress_event","unrecovered","forecast_mse"],
                                     ["Net return (%)","Persistent dislocation (%)","No joint recovery (%)","Forecast MSE"],[100,100,100,1]):
        v=sel.groupby("policy")[metric].mean().reindex(ORDER)*mult
        se=sel.groupby("policy")[metric].std().reindex(ORDER)/8*mult
        # Binary panels use point rates only: normal intervals mislead at zero.
        err=1.96*se if metric in ["net_return","forecast_mse"] else None
        ax.bar(range(4),v,color=COLORS,yerr=err,capsize=3)
        ax.set_xticks(range(4),list(LABEL.values()),rotation=15,ha="right")
        ax.set_title(title,loc="left");ax.axhline(0,color="#667788",lw=.6)
    fig.savefig(F/"market_comparison.pdf");plt.close(fig)
    traces=pd.read_csv(R/"market_traces.csv")
    fig,axs=plt.subplots(3,1,figsize=(10,8),sharex=True,layout="constrained")
    for p,c in zip(ORDER,COLORS):
        d=traces[traces.policy==p]
        for ax,metric in zip(axs,["price","depth","equity"]):ax.plot(d.t,d[metric],color=c,label=LABEL[p])
    d=traces[traces.policy=="ungated"]
    axs[0].plot(d.t,d.fundamental,color="black",ls=":",label="Fundamental proxy")
    for ax,label in zip(axs,["Price","Normalized depth","Marked wealth"]):
        ax.set_ylabel(label);ax.axvline(180,color="gray",ls="--",lw=.8);ax.grid(alpha=.12)
    axs[0].legend(ncol=3,fontsize=8,loc="upper left")
    axs[-1].set_xlabel("Simulation step (no calibrated time unit)")
    fig.savefig(F/"market_paths.pdf");plt.close(fig)
    cap=pd.read_csv(R/"cap_sensitivity.csv")
    cs=cap[cap.shock==.08].groupby(["return_cap","policy"]).mean(numeric_only=True)
    tex_table(S/"cap_table.tex","Return cap & Policy & Net return (\\%) & Dislocation (\\%) & Clipped steps",
       [[f"{c:.3f}",LABEL[p],f"{100*x.net_return:.2f}",f"{100*x.stress_event:.2f}",f"{x.clip_count:.3f}"] for (c,p),x in cs.iterrows()],
       "rlrrr","Post-audit cap sensitivity in the high-coupling shock case. Clipped steps count the entire trajectory, including initialization.")
    summary=pd.read_csv(R/"market_summary.csv")
    rows1=[];rows2=[]
    for x in summary.itertuples():
        key=[f"{x.phi:g}",f"{x.similarity:g}",f"{x.speed:g}",f"{x.leverage:g}",f"{x.shock:g}",LABEL[x.policy]]
        rows1.append(key+[f"{100*x.net_return_mean:.2f}",f"{100*x.net_return_mcse:.2f}",f"{100*x.max_drawdown_mean:.2f}",f"{x.minimum_depth_mean:.3f}"])
        rows2.append(key+[f"{100*x.stress_event_mean:.1f}",f"{100*x.downside_dislocation_mean:.1f}",f"{100*x.price_drawdown_event_mean:.1f}",f"{100*x.unrecovered_mean:.1f}"])
    header=r"$\phi$ & $\rho$ & $\eta$ & $\ell$ & Shock & Policy"
    long_table(S/"full_returns.tex",header+r" & Return & MCSE & Drawdown & Depth",rows1,"rrrrrlrrrr",
       r"All 256 configurations. Return, its Monte Carlo standard error (MCSE), and drawdown are in percent. Depth is dimensionless. Each row uses 64 replications.")
    long_table(S/"full_events.tex",header+r" & Abs. & Down & Price DD & Censored",rows2,"rrrrrlrrrr",
       r"Event rates in percent. Abs.: persistent absolute displacement; Down: persistent downside displacement; Price DD: persistent 15\% price drawdown; Censored: no joint recovery by horizon. Definitions differ and must not be merged into one crash statistic.")
    pairs=pd.read_csv(R/"market_paired.csv")
    prows=[]
    for x in pairs[pairs.metric=="net_return"].itertuples():
        prows.append([f"{x.phi:g}",f"{x.similarity:g}",f"{x.speed:g}",f"{x.leverage:g}",f"{x.shock:g}",
                      x.contrast.replace("evidence_gate","Gate").replace("risk_only","Risk").replace("wrong_evidence","Wrong").replace("ungated","Ungated"),
                      f"{100*x.mean:.3f}",f"{100*x.mcse:.3f}"])
    long_table(S/"full_pairs.tex",header.replace("Policy","Contrast")+r" & Difference & MCSE",prows,"rrrrrlrr",
               "Paired net-return differences in percentage points. Replication indices are matched; positive values favor the first policy. No multiple-comparison significance threshold is asserted.")
    # Aggregate contrasts by seed first, preserving cross-scenario dependence.
    keys=["phi","similarity","speed","leverage","shock","replicate"]
    wide=raw.pivot(index=keys,columns="policy",values="net_return")
    result=[]
    for a,b in [("evidence_gate","ungated"),("evidence_gate","risk_only"),("wrong_evidence","evidence_gate")]:
        d=(wide[a]-wide[b]).groupby("replicate").mean()
        result.append(dict(contrast=a+" - "+b,grid_mean=float(d.mean()),mcse=float(d.std(ddof=1)/np.sqrt(len(d)))))
    (R/"grid_paired_summary.json").write_text(json.dumps(result,indent=2))
    (R/"figure_manifest.json").write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in F.glob("*.pdf")},indent=2))
    print("Generated tables and vector figures from result files.")
if __name__=="__main__":main()

