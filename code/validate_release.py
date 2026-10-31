"""Validate release result structure, paired arithmetic, and PDF identity."""
from pathlib import Path
import hashlib,json,re
import numpy as np
import pandas as pd
import fitz
ROOT=Path(__file__).resolve().parents[1]
def main():
    r=ROOT/"results"
    market=pd.read_csv(r/"market_replicates.csv")
    assert len(market)==16384 and market.policy.nunique()==4
    keys=["phi","similarity","speed","leverage","shock","policy"]
    assert market.groupby(keys).size().eq(64).all()
    assert np.isfinite(market.select_dtypes(include="number")).all().all()
    assert market.minimum_depth.between(.12-1e-12,1+1e-12).all()
    assert market.coverage.between(0,1).all()
    assert market.groupby("policy").net_return.mean().lt(0).all()
    syn=pd.read_csv(r/"synthetic_replicates.csv")
    assert len(syn)==4000 and syn.groupby(["scenario","method"]).size().eq(200).all()
    assert (syn[["mse","mae"]]>=0).all().all()
    nominal=syn[syn.scenario=="Observed confounder"].groupby("method").mse.mean()
    assert abs(nominal["Filtered soft gate"]-.3733677743)<1e-8
    grouped=market.groupby(keys).net_return.mean()
    reported=pd.read_csv(r/"market_summary.csv").set_index(keys).net_return_mean
    assert np.allclose(grouped.sort_index(),reported.sort_index(),atol=1e-12)
    pdfs=[ROOT/"manuscript.pdf"]
    assert pdfs[0].exists()
    identity=[]
    for p in pdfs:
        d=fitz.open(p)
        assert len(d)>40
        assert d.metadata["author"]=="Timilehin Olapade"
        assert "Market Transitions" in d.metadata["title"]
        assert "Timilehin Olapade" in d.get_xml_metadata()
        assert "Timilehin Olapade" in d[0].get_text()
        text="\n".join(x.get_text() for x in d)
        assert "??" not in text
        urls=sorted({a["uri"] for page in d for a in page.get_links() if "uri" in a})
        identity.append(dict(file=p.name,pages=len(d),author=d.metadata["author"],title=d.metadata["title"],external_links=urls))
    report=dict(result="passed",checks=["primary grid shape","finite outcomes","depth bounds","eligibility bounds","negative grid-average returns retained","structural study shape","nonnegative losses","reference coefficient MSE","summary arithmetic","PDF author/title/XMP/text/cross references"],pdfs=identity,
        scope="Computational and document checks; not independent scientific peer review or broker-account verification.")
    (r/"release_validation.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()

