"""05a-ii (decision 2 of the review): why do `paperA_corr` and `paperA_sh_mh` move 7-11 pp under the D5 swap? Hypothesis: in the real B* arm
every HP dwelling carries its own non-HP load, whose temperature slope is much larger than a generic filler's, and neither estimator
removes it. Test, from the D5 outputs only (no new run): the own-load slope per HP home is backed out of the pilot rows
(s0 of train fill + own load of the train HP homes, over 968 fill + 64 own), the expected shift of the estimate is
n_hp x (s_own - s_filler_swap) / m_h per test substation, and it is compared with the actual prediction difference real - swap.
Writes results/iter05a_pool/d5_paperA_diagnostic.md.

    python scripts/paperb/d5_own_load_diagnostic.py
"""
import io, sys
import pandas as pd, numpy as np
_out, _buf = sys.stdout, io.StringIO()
sys.stdout = _buf
b="results/iter05a_pool/overnight/"
pr={a:pd.read_csv(b+a+"/predictions.csv") for a in ("d5_real","d5_swap")}
pil={a:pd.read_csv(b+a+"/pilots.csv") for a in pr}
r=pil["d5_real"]
f=r[r.pilot=="s0:paperA_corr"].set_index("split_seed").s0
al=r[r.pilot=="s0:paperA_corr_all"].set_index("split_seed")
s_own=(al.s0*al.n_hh-f*968)/64
sw=pil["d5_swap"]; s_sw=sw[sw.pilot=="s0:paperA_corr"].set_index("split_seed").s0
m=r[r.pilot=="all"].set_index("split_seed").m
print("s0 fill (real) %.5f  s0 own-load per HP home %.5f (x%.1f)  s0 swap filler %.5f  m_h %.5f"%(f.mean(),s_own.mean(),s_own.mean()/f.mean(),s_sw.mean(),m.mean()))
print("own-load slope per HP home by seed: min %.4f max %.4f"%(s_own.min(),s_own.max()))
out=[]
for meth in ("paperA_sh_mh","paperA_corr"):
    a=pr["d5_real"].query("method==@meth and anchor=='none'" if False else "method==@meth")
    s=pr["d5_swap"].query("method==@meth")
    j=a.merge(s,on=["split_seed","sub_id"],suffixes=("_r","_s"))
    j=j.drop_duplicates(["split_seed","sub_id"])
    j["n_hp"]=np.maximum(1,np.round(j.p_r*j.size_r))
    j["N"]=j.size_r
    d=j.pred_r-j.pred_s
    own_term=j.n_hp*(j.split_seed.map(s_own)-j.split_seed.map(s_sw))/j.split_seed.map(m)
    # paperA_corr also differs by N*(s0_real - s0_swap)/m (different s0 subtracted)
    corr_term=j.N*(j.split_seed.map(f)-j.split_seed.map(s_sw))/j.split_seed.map(m) if meth=="paperA_corr" else 0
    exp=own_term-corr_term
    ok=(j.pred_r>0)&(j.pred_s>0)
    print(meth,"n",ok.sum(),"corr(actual diff, expected own-load diff) %.3f"%np.corrcoef(d[ok],exp[ok])[0,1],
          "median actual %.2f kW  expected %.2f kW  ratio %.2f"%(d[ok].median(),exp[ok].median(),(d[ok]/exp[ok]).median()),
          "expected shift as %% of mean y: %.1f"%(100*exp[ok].mean()/j.y_r[ok].mean()))
sys.stdout = _out
text = _buf.getvalue()
print(text)
NOTE = ("Reading: the own non-HP load of a B* HP home is about 3x as temperature-sensitive as a filler dwelling, and `paperA_corr` subtracts only N x s0 of the "
        "fillers (`paperA_sh_mh` subtracts nothing), so in the real arm each HP home leaves about 0.7 kW of extra apparent heat-pump capacity in the estimate "
        "(about 10 % of the mean HP_Peak). The swap removes it by giving every dwelling a filler, which is also how a GB-EoH substation is built. The expected shift "
        "explains the observed one (ratio actual / expected about 0.8). What the own load contains (electric water heating, direct heaters, back-up rods booked "
        "outside the HP submeter) was not examined; that is a hypothesis.\n")
HEAD = ("# 05a-ii: own non-HP load of the B* HP homes and the D5 shift of `paperA_corr` / `paperA_sh_mh`\n\n"
        "Source: `scripts/paperb/d5_own_load_diagnostic.py` (method in its docstring), D5 outputs in `overnight/d5_{real,swap}/`. Slopes in kW/K per dwelling.\n\n")
open("results/iter05a_pool/d5_paperA_diagnostic.md", "w", encoding="utf-8").write(HEAD + "```\n" + text + "```\n\n" + NOTE)
