"""Pure pandas/numpy model for the Dutch offshore wind dashboard (no Streamlit)."""
import numpy as np
import pandas as pd

BASE_YEAR, END_YEAR, TARGET_MW = 2025, 2032, 21000.0
UNDATED_WINDOW = (2030, 2031, 2032)
# two-sided 95% Student-t critical values, df 1..12 (df>12 uses 2.0 - 2.18 range; table to 30 below)
T975 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179,
        2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064,
        2.060, 2.056, 2.052, 2.048, 2.045, 2.042]


def load_history(path="data/cbs_82610ENG_wind.csv"):
    return pd.read_csv(path)


def load_pipeline(path="data/rvo_pipeline.csv"):
    df = pd.read_csv(path)
    df["mw"] = df["gw"] * 1000.0
    return df


def pipeline_split(pipe):
    """MW with an expected year vs MW still 'to be determined'."""
    dated = pipe["year"].notna()
    return pipe.loc[dated, "mw"].sum(), pipe.loc[~dated, "mw"].sum()


def scenario_path(pipe, base_mw, delay=0, gamma=True, undated_gw=0.0,
                  start=BASE_YEAR, end=END_YEAR, undated_window=UNDATED_WINDOW):
    """Year-by-year additions and cumulative MW.
    base + dated sites in (year+delay) + Gamma only if gamma + undated_gw spread evenly.
    Sites pushed past `end` drop out."""
    years = list(range(start, end + 1))
    add = pd.Series(0.0, index=years)
    d = pipe[pipe["year"].notna()]
    if not gamma:
        d = d[d["tender_dependent"] != 1]
    for y, mw in zip(d["year"].astype(int) + int(delay), d["mw"]):
        if y in add.index:
            add[y] += mw
    dated_in_window = float(add.sum())
    for y in undated_window:
        add[y] += undated_gw * 1000.0 / len(undated_window)
    cum = base_mw + add.cumsum()
    return pd.DataFrame({"year": years, "additions_mw": add.values, "cumulative_mw": cum.values,
                         "dated_mw": dated_in_window}).assign(base_mw=base_mw)


def metrics(path, target_mw=TARGET_MW, end=END_YEAR, undated_gw=0.0):
    p = path[path["year"] > BASE_YEAR]
    cap = float(path.loc[path["year"] == end, "cumulative_mw"].iloc[0])
    hit = path[path["cumulative_mw"] >= target_mw - 1e-9]
    peak = p.loc[p["additions_mw"].idxmax()]
    return {"cap2032_mw": cap, "gap_mw": max(target_mw - cap, 0.0),
            "target_year": int(hit["year"].iloc[0]) if len(hit) else None,
            "peak_year": int(peak["year"]) if peak["additions_mw"] > 0 else None,
            "peak_mw": float(peak["additions_mw"]),
            "zero_years": int((p["additions_mw"] <= 1e-9).sum()),
            "mw_added": cap - float(path["base_mw"].iloc[0]),
            "dated_mw": float(path["dated_mw"].iloc[0]), "undated_mw": undated_gw * 1000.0}


def fill_text(template, m, target_mw=TARGET_MW):
    """Fill {placeholders} in lenses.csv text with live numbers."""
    vals = {"cap2032": f"{m['cap2032_mw']/1000:.1f} GW", "gap": f"{m['gap_mw']/1000:.1f} GW",
            "year": str(m["target_year"]) if m["target_year"] else "not reached by 2032",
            "peak_year": str(m["peak_year"]) if m["peak_year"] else "none",
            "peak": f"{m['peak_mw']/1000:.1f} GW", "zero": str(m["zero_years"]),
            "target": f"{target_mw/1000:.0f} GW", "dated": f"{m['dated_mw']/1000:.1f} GW",
            "undated": f"{m['undated_mw']/1000:.1f} GW"}
    out = template
    for k, v in vals.items():
        out = out.replace("{" + k + "}", v)
    return out


def _fit(x, y):
    n = len(x); xb = x.mean(); sxx = ((x - xb) ** 2).sum()
    b = ((x - xb) * (y - y.mean())).sum() / sxx
    a = y.mean() - b * xb
    res = y - (a + b * x)
    s = np.sqrt((res ** 2).sum() / (n - 2))
    return a, b, s, n, xb, sxx


def linear_forecast(years, values, horizon_end=END_YEAR):
    """OLS trend + ~95% prediction interval (widens with distance from the data)."""
    x = np.asarray(years, float); y = np.asarray(values, float)
    a, b, s, n, xb, sxx = _fit(x, y)
    t = T975[n - 3] if n - 2 <= len(T975) else 1.96
    fy = np.arange(int(x.max()) + 1, horizon_end + 1)
    mid = a + b * fy
    half = t * s * np.sqrt(1 + 1 / n + (fy - xb) ** 2 / sxx)
    fit = a + b * x
    return pd.DataFrame({"year": fy, "forecast_mw": mid, "lo_mw": mid - half, "hi_mw": mid + half}), \
        {"slope_mw_per_year": b, "intercept": a, "resid_sd": s, "n": n, "t": t, "fitted": fit}


def holdout(hist, train_end=2021, start=2015, col="offshore_mw"):
    """Train on start..train_end, test on later years; compare with naive last-value."""
    tr = hist[(hist["year"] >= start) & (hist["year"] <= train_end)]
    te = hist[hist["year"] > train_end]
    fc, _ = linear_forecast(tr["year"], tr[col], te["year"].max())
    last = float(tr[col].iloc[-1])
    out = te[["year", col]].rename(columns={col: "actual_mw"}).merge(fc, on="year")
    out["naive_mw"] = last
    out["err_linear"] = out["forecast_mw"] - out["actual_mw"]
    out["err_naive"] = out["naive_mw"] - out["actual_mw"]
    out["inside_band"] = (out["actual_mw"] >= out["lo_mw"]) & (out["actual_mw"] <= out["hi_mw"])
    return out, {"mae_linear": float(out["err_linear"].abs().mean()),
                 "mae_naive": float(out["err_naive"].abs().mean()),
                 "coverage": float(out["inside_band"].mean())}
