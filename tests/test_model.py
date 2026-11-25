import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
import model as m

H = m.load_history("data/cbs_82610ENG_wind.csv"); P = m.load_pipeline("data/rvo_pipeline.csv")
BASE = float(H.loc[H.year == 2025, "offshore_mw"].iloc[0])
S = pd.read_csv("scenarios.csv")

def run(row):
    p = m.scenario_path(P, BASE, row.delay, bool(row.gamma), row.undated_gw)
    return p, m.metrics(p, undated_gw=row.undated_gw)

def test_cbs_crosscheck():
    g = lambda y: int(H.loc[H.year == y, "offshore_mw"].iloc[0])
    assert (g(2023), g(2024), g(2025)) == (4110, 4748, 4748)
    assert H.year.min() == 2006 and H.year.max() == 2025 and len(H) == 20

def test_total_2025_matches_cbs_total():
    r = H[H.year == 2025].iloc[0]
    assert abs(r.offshore_mw + r.onshore_mw - 11782) <= 2        # CBS total wind 2025 (rounding)

def test_dated_pipeline_expected_finding():
    dated, undated = m.pipeline_split(P)
    assert abs(dated - 7520) < 1e-6 and abs(undated - 11400) < 1e-6
    assert abs((BASE + dated) / 1000 - 12.268) < 1e-9          # ~12.3 GW
    assert abs((21000 - BASE - dated) / 1000 - 8.732) < 1e-9   # ~8.7 GW needed from undated

def test_presets():
    r, d, c = [run(S.iloc[i]) for i in range(3)]
    assert abs(r[1]["cap2032_mw"] - 21068) < 1e-6 and r[1]["target_year"] == 2032 and r[1]["gap_mw"] == 0
    assert abs(d[1]["cap2032_mw"] - 12268) < 1e-6 and d[1]["target_year"] is None   # Gamma pushed to 2033 drops out
    assert abs(c[1]["cap2032_mw"] - 10268) < 1e-6 and c[1]["peak_year"] == 2031

def test_invariants():
    for _, row in S.iterrows():
        p, _ = run(row)
        assert (p.cumulative_mw.diff().dropna() >= -1e-9).all()
        assert abs(p.cumulative_mw.iloc[-1] - BASE - p.additions_mw.sum()) < 1e-6
    p0, _ = run(S.iloc[0]); p1 = m.scenario_path(P, BASE, 0, False, 8.8)
    assert p1.cumulative_mw.iloc[-1] == p0.cumulative_mw.iloc[-1] - 2000

def test_forecast_and_holdout():
    h = H[(H.year >= 2015)]
    fc, info = m.linear_forecast(h.year, h.offshore_mw)
    w = (fc.hi_mw - fc.lo_mw).values
    assert (w[1:] > w[:-1]).all()                     # band widens with horizon
    out, s = m.holdout(H, 2021)
    assert list(out.year) == [2022, 2023, 2024, 2025]
    assert s["mae_linear"] > 0 and s["mae_naive"] > 0

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("ok", n)
