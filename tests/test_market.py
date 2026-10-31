import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from market_study import CONFIG, innovations, simulate, train_experts

class MarketTests(unittest.TestCase):
    def setUp(self):
        self.cfg=dict(CONFIG,replicates=4,participants=6,steps=50,burn=10,shock_at=25)
        self.noise=innovations(self.cfg);self.weights=train_experts()
    def run_case(self,policy='evidence_gate',phi=.5,cfg=None,noise=None):
        return simulate(phi,.85,.8,3.,.08,policy,cfg or self.cfg,noise or self.noise,self.weights,True)
    def test_repeatability_and_finiteness(self):
        a,t=self.run_case();b,u=self.run_case();self.assertEqual(a,b);self.assertEqual(t,u)
        for row in a:
            for v in row.values():
                if isinstance(v,(float,int)):self.assertTrue(np.isfinite(v))
    def test_zero_participation_market_is_policy_invariant(self):
        _,a=self.run_case('ungated',0.);_,b=self.run_case('evidence_gate',0.)
        for x,y in zip(a,b):
            for k in ['price','fundamental','depth']:self.assertEqual(x[k],y[k])
    def test_future_innovations_cannot_change_past(self):
        _,a=self.run_case();noise={k:v.copy() for k,v in self.noise.items()}
        for k in noise:noise[k][30:]=noise[k][30:]*.3
        _,b=self.run_case(noise=noise)
        self.assertEqual(a[:30],b[:30])
    def test_self_financing_midpoint_identity(self):
        old_price=100.;new_price=103.;old_pos=2.;flow=-.5;cash=500.;fee=.12
        execution=(old_price+new_price)/2
        new_cash=cash-flow*execution-fee
        new_wealth=new_cash+(old_pos+flow)*new_price
        old_wealth=cash+old_pos*old_price
        self.assertAlmostEqual(new_wealth-old_wealth,(old_pos+.5*flow)*(new_price-old_price)-fee)

if __name__=='__main__':unittest.main()
