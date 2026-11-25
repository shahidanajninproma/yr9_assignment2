"""WINDSCOPE-style Streamlit dashboard. All logic lives in model.py; text lives in CSV/MD files."""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import model as M

OBS, FC, SCN, ONS = "#54b8fa", "#f0bb65", "#40d7b0", "#8aa0bd"   # observed / model forecast / scenario / onshore
pio.templates.default = "plotly_dark"
st.set_page_config(page_title="WINDSCOPE | Dutch offshore wind to 2032", page_icon="🌬️", layout="wide")

st.markdown("""<style>
.stApp{background:#090f1e}[data-testid=stSidebar]{background:#0c1628;border-right:1px solid #25354e}
.block-container{max-width:1500px;padding-top:2rem}
.brand{font-weight:800;font-size:19px;letter-spacing:-.4px}.brand span{color:#55d7ba}.sub{font-size:11px;color:#96a9c5;letter-spacing:.4px}
.kick{color:#40d7b0;letter-spacing:2.2px;font-weight:800;font-size:10px;text-transform:uppercase}
h1.t{font-size:clamp(26px,3vw,38px);letter-spacing:-1.2px;line-height:1.15;margin:6px 0 8px}
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:14px 0 8px}
.kpi{background:linear-gradient(160deg,#142139,#101b2f);border:1px solid #25354e;border-radius:17px;padding:18px 20px}
.kpi .l{font-size:11px;color:#96a9c5;text-transform:uppercase;letter-spacing:.6px;font-weight:650}
.kpi .v{font-size:clamp(22px,2.2vw,32px);font-weight:800;letter-spacing:-1px;margin-top:6px}.kpi .n{font-size:11px;color:#92a9c5;margin-top:4px}
.snap{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 4px}
.pill{border:1px solid #25354e;background:#122039;border-radius:100px;padding:4px 11px;color:#bcd0e8;font-size:11.5px}
.pill.ok{border-color:#1c786a;background:#123b3a;color:#83edd3}.pill.warn{border-color:#625b38;background:#30291a;color:#f5d99c}
.panel{background:linear-gradient(160deg,#142139,#101b2f);border:1px solid #25354e;border-radius:17px;padding:16px 20px;margin:8px 0}
.panel p{color:#96a9c5;font-size:13px;margin:4px 0}.side-snap{border-top:1px solid #25354e;padding-top:12px;margin-top:14px;font-size:11.5px;color:#96a9c5}
@media(max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}}
</style>""", unsafe_allow_html=True)


@st.cache_data
def load():
    r = pd.read_csv
    return (M.load_history(), M.load_pipeline(), r("scenarios.csv"), r("lenses.csv"), r("content/pestle.csv"), r("sources.csv"))


H, P, SC, LEN, PES, SRC = load()
BASE = float(H.loc[H.year == 2025, "offshore_mw"].iloc[0])
S_ = SRC.set_index("id")
md = lambda n: Path(f"content/{n}.md").read_text(encoding="utf-8")
src = lambda i: f"{S_.loc[i, 'dataset']} ({S_.loc[i, 'table']})"
SNAP = SRC.access_date.max()
CAP, RVO = src("cbs_cap"), src("rvo_road")


def apply_preset():
    r = SC.set_index("id").loc[st.session_state.preset]
    st.session_state.delay, st.session_state.gamma, st.session_state.undated = int(r.delay), bool(r.gamma), float(r.undated_gw)


if "preset" not in st.session_state:
    st.session_state.preset = SC.id.iloc[0]; apply_preset()

sb = st.sidebar
sb.markdown('<div class="brand">WIND<span>SCOPE</span></div><div class="sub">NETHERLANDS · OFFSHORE · 2032</div>', unsafe_allow_html=True)
sb.markdown("##### Scenario (drives every tab)")
sb.radio("Preset", list(SC.id), format_func=lambda i: SC.set_index("id").loc[i, "label"], key="preset", on_change=apply_preset)
sb.slider("Delay to dated sites (years)", 0, 3, key="delay")
sb.checkbox("Gamma-A/B tender succeeds", key="gamma")
sb.slider("Undated capacity built 2030-2032 (GW)", 0.0, 11.4, step=0.1, key="undated")
sb.number_input("Target capacity end-2032 (GW)", 10.0, 30.0, 21.0, 0.5, key="target",
                help="21 GW per RVO 2024 planning note; the May 2026 Roadmap states 23 GW.")
pr = SC.set_index("id").loc[st.session_state.preset]
if (st.session_state.delay, st.session_state.gamma, round(st.session_state.undated, 1)) != (int(pr.delay), bool(pr.gamma), round(pr.undated_gw, 1)):
    sb.warning("Custom: sliders differ from the preset. Lens text shows the preset's wording; numbers are live.")
sb.caption("Scenario inputs are illustrative team assumptions, not data.")
sb.markdown(f'<div class="side-snap"><span class="pill ok">● Data snapshot {SNAP}</span><br><br>Sources: CBS StatLine 82610ENG (CC BY 4.0) · RVO Offshore Wind Roadmap (May 2026)<br>2024-2025 CBS values provisional · not live data</div>', unsafe_allow_html=True)

TGT = st.session_state.target * 1000
PATH = M.scenario_path(P, BASE, st.session_state.delay, st.session_state.gamma, st.session_state.undated)
MET = M.metrics(PATH, TGT, undated_gw=st.session_state.undated)

st.markdown('<div class="kick">Dutch renewable energy intelligence</div><h1 class="t">Should a supplier invest in Dutch offshore wind capacity to 2032?</h1>', unsafe_allow_html=True)
st.markdown(f'<div class="snap"><span class="pill ok">Snapshot, not live · accessed {SNAP}</span><span class="pill">CBS StatLine 82610ENG · history 2006-2025</span>'
            f'<span class="pill">RVO Offshore Wind Roadmap · May 2026</span><span class="pill warn">2024-2025 provisional</span>'
            f'<span class="pill">Scenarios = assumptions</span></div>', unsafe_allow_html=True)
last = H.iloc[-1]; tot = last.offshore_mw + last.onshore_mw
kp = [("Total wind installed, 2025", f"{tot/1000:.2f} GW", "Observed · CBS · provisional"),
      ("Offshore, 2025", f"{last.offshore_mw/1000:.2f} GW", f"{last.offshore_mw/tot:.1%} of total · observed"),
      ("Onshore, 2025", f"{last.onshore_mw/1000:.2f} GW", f"{last.onshore_mw/tot:.1%} of total · observed"),
      ("Offshore end-2032 (scenario)", f"{MET['cap2032_mw']/1000:.1f} GW", f"gap to {TGT/1000:.0f} GW: {MET['gap_mw']/1000:.1f} GW · assumption")]
st.markdown('<div class="kpis">' + "".join(f'<div class="kpi"><div class="l">{a}</div><div class="v">{b}</div><div class="n">{c}</div></div>' for a, b, c in kp) + "</div>", unsafe_allow_html=True)


def style(fig, title, ytitle, source, h=430):
    fig.update_layout(title=title, yaxis_title=ytitle, height=h, margin=dict(b=120), legend=dict(orientation="h", y=-0.18),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#bcd0e8"),
                      xaxis=dict(gridcolor="#25354e"), yaxis=dict(gridcolor="#25354e"))
    fig.add_annotation(text=f"Source: {source}", xref="paper", yref="paper", x=0, y=-0.34, showarrow=False, font=dict(size=10, color="#8aa0bd"))
    return fig


def lens_text(lens):
    row = LEN[(LEN.lens == lens) & (LEN.scenario == st.session_state.preset)].iloc[0]
    st.info(M.fill_text(row.readout, MET, TGT)); st.success("**Action:** " + M.fill_text(row.action, MET, TGT))


def cum_chart(show_fc=False):
    f = go.Figure()
    f.add_scatter(x=H.year, y=H.offshore_mw, name="Observed (CBS)", line=dict(color=OBS))
    p = PATH[PATH.year >= 2025]
    f.add_scatter(x=p.year, y=p.cumulative_mw, name="Scenario (assumption)", line=dict(color=SCN, width=3))
    if show_fc:
        h = H[H.year >= 2015]; fc, _ = M.linear_forecast(h.year, h.offshore_mw)
        f.add_scatter(x=fc.year, y=fc.forecast_mw, name="Linear trend (model)", line=dict(color=FC, dash="dash"))
    f.add_hline(y=TGT, line_dash="dot", annotation_text=f"Target {TGT/1000:.0f} GW")
    return style(f, "Offshore wind capacity: observed vs scenario", "MW installed, end of year", f"{CAP}; {RVO}; scenario = team assumptions")


T = st.tabs(["Supplier lens", "Scenarios", "Developer lens", "Policymaker lens", "Forecast", "History",
             "Context", "Summary", "Data & sources"])

with T[0]:
    st.subheader("Supplier: invest in Dutch capacity to 2032?")
    c = st.columns(3)
    c[0].metric("MW added per year (avg 2026-32)", f"{MET['mw_added']/7:,.0f}")
    c[1].metric("Busiest year", f"{MET['peak_year']} ({MET['peak_mw']:,.0f} MW)" if MET["peak_year"] else "none")
    c[2].metric("Zero-build years (of 7)", MET["zero_years"])
    lens_text("supplier")
    oa = H.assign(a=H.offshore_mw.diff()).dropna(); p = PATH[PATH.year > 2025]
    f = go.Figure()
    f.add_bar(x=oa.year, y=oa.a, name="Observed additions (CBS)", marker_color=OBS)
    f.add_bar(x=p.year, y=p.additions_mw, name="Scenario additions (assumption)", marker_color=SCN)
    st.plotly_chart(style(f, "Capacity added per year", "MW added in year", f"{CAP}; {RVO}; scenario = team assumptions"), use_container_width=True)

with T[1]:
    st.subheader("Scenarios")
    st.plotly_chart(cum_chart(True), use_container_width=True)
    st.dataframe(SC[["label", "delay", "gamma", "undated_gw", "drivers", "assumption_note"]], hide_index=True)
    inc = P.assign(included_in_2032=lambda d: d.year.notna() & (d.year + st.session_state.delay <= 2032) & ((d.tender_dependent == 0) | st.session_state.gamma))
    st.caption(f"RVO pipeline ({RVO}, snapshot {SNAP}) and whether each dated site counts under the current settings. Undated sites are covered by the slider.")
    st.dataframe(inc[["site", "gw", "commissioning_text", "year", "included_in_2032"]], hide_index=True)

with T[2]:
    st.subheader("Developer: bid in tenders or not?")
    c = st.columns(3)
    c[0].metric("Dated pipeline in window", f"{MET['dated_mw']:,.0f} MW"); c[1].metric("Undated assumed built", f"{MET['undated_mw']:,.0f} MW")
    c[2].metric("Undated share of additions", f"{MET['undated_mw']/MET['mw_added']:.0%}" if MET["mw_added"] else "n/a")
    lens_text("developer")
    d_all, u_all = M.pipeline_split(P); x = ["RVO roadmap (all sites)", "Selected scenario"]
    f = go.Figure()
    f.add_bar(x=x, y=[d_all, MET["dated_mw"]], name="Dated sites (RVO)", marker_color=OBS)
    f.add_bar(x=x, y=[u_all, MET["undated_mw"]], name="Undated sites", marker_color=SCN)
    f.update_layout(barmode="stack")
    st.plotly_chart(style(f, "Dated vs undated pipeline", "MW", f"{RVO}; scenario = team assumptions"), use_container_width=True)

with T[3]:
    st.subheader("Policymaker: will the target be reached by 2032?")
    c = st.columns(3)
    c[0].metric("Capacity end-2032", f"{MET['cap2032_mw']/1000:.1f} GW"); c[1].metric(f"Gap to {TGT/1000:.0f} GW", f"{MET['gap_mw']/1000:.1f} GW")
    c[2].metric("Year target reached", MET["target_year"] or "Not by 2032")
    lens_text("policymaker")
    st.plotly_chart(cum_chart(), use_container_width=True)

with T[4]:
    st.subheader("Forecast and validation")
    h = H[H.year >= 2015]; fc, info = M.linear_forecast(h.year, h.offshore_mw)
    f = go.Figure()
    f.add_scatter(x=h.year, y=h.offshore_mw, name="Observed (CBS)", line=dict(color=OBS))
    f.add_scatter(x=fc.year, y=fc.hi_mw, line=dict(width=0), showlegend=False, hoverinfo="skip")
    f.add_scatter(x=fc.year, y=fc.lo_mw, fill="tonexty", fillcolor="rgba(240,187,101,.2)", line=dict(width=0), name="~95% band")
    f.add_scatter(x=fc.year, y=fc.forecast_mw, name="Linear trend (model)", line=dict(color=FC, dash="dash"))
    st.plotly_chart(style(f, "Linear trend 2015-2025 extended to 2032", "MW installed", f"{CAP}; OLS in model.py"), use_container_width=True)
    st.markdown(md("forecast_note"))
    ty = st.slider("Holdout: train to year", 2018, 2024, 2021)
    out, s = M.holdout(H, ty)
    c = st.columns(3); c[0].metric("MAE linear (MW)", f"{s['mae_linear']:,.0f}"); c[1].metric("MAE naive last value (MW)", f"{s['mae_naive']:,.0f}")
    c[2].metric("Actuals inside band", f"{s['coverage']:.0%}")
    g = go.Figure(); hh = H[H.year >= 2015]
    g.add_scatter(x=hh.year, y=hh.offshore_mw, name="Actual (CBS)", line=dict(color=OBS))
    g.add_scatter(x=out.year, y=out.forecast_mw, name="Linear (trained to holdout)", line=dict(color=FC, dash="dash"))
    g.add_scatter(x=out.year, y=out.naive_mw, name="Naive last value", line=dict(color="#8aa0bd", dash="dot"))
    st.plotly_chart(style(g, f"Holdout test: train 2015-{ty}, test {ty+1}-2025", "MW installed", CAP), use_container_width=True)
    st.caption("Few test points and step-like data: treat the comparison as indicative.")
    st.dataframe(out.round(0), hide_index=True)

with T[5]:
    st.subheader("History: Dutch wind capacity")
    y0 = st.selectbox("From year", list(H.year[:-1]), index=9, format_func=lambda y: f"{y} onwards")
    Hh = H[H.year >= y0]; pv = Hh[Hh.provisional == 1]
    f = go.Figure()
    f.add_scatter(x=Hh.year, y=Hh.offshore_mw + Hh.onshore_mw, name="Total", line=dict(color=OBS))
    f.add_scatter(x=Hh.year, y=Hh.onshore_mw, name="Onshore", line=dict(color=ONS))
    f.add_scatter(x=Hh.year, y=Hh.offshore_mw, name="Offshore", line=dict(color=SCN))
    f.add_scatter(x=pv.year, y=pv.offshore_mw + pv.onshore_mw, mode="markers", name="Provisional (2024-25)", marker=dict(symbol="circle-open", size=12, color=OBS))
    st.plotly_chart(style(f, "Installed wind capacity", "MW, end of year", CAP), use_container_width=True)
    a, b = st.columns([3, 2])
    with a:
        g = go.Figure(); g.add_bar(x=Hh.year, y=Hh.onshore_mw, name="Onshore", marker_color=ONS); g.add_bar(x=Hh.year, y=Hh.offshore_mw, name="Offshore", marker_color=SCN)
        g.update_layout(barmode="stack"); st.plotly_chart(style(g, "Onshore + offshore (stacked)", "MW, end of year", CAP, 400), use_container_width=True)
    with b:
        d = go.Figure(go.Pie(labels=["Onshore", "Offshore"], values=[last.onshore_mw, last.offshore_mw], hole=.62, marker_colors=[ONS, SCN], sort=False))
        st.plotly_chart(style(d, "Capacity mix, 2025", "", CAP, 400), use_container_width=True)
    ch = H.assign(t=H.offshore_mw + H.onshore_mw); ch["d"] = ch.t.diff(); ch = ch.dropna(subset=["d"])
    g = go.Figure(go.Bar(x=ch.year, y=ch.d, marker_color=[OBS if v >= 0 else "#f08a8a" for v in ch.d]))
    st.plotly_chart(style(g, "Annual net change in total wind capacity", "MW change vs previous year", CAP, 380), use_container_width=True)
    g = go.Figure(go.Bar(x=H.year, y=H.offshore_prod_mln_kwh, marker_color=OBS))
    st.plotly_chart(style(g, "Offshore wind gross electricity production", "mln kWh", src("cbs_prod"), 380), use_container_width=True)

with T[6]:
    st.subheader("Context: PESTLE and Porter's Diamond")
    st.markdown(md("context_intro"))
    for fw in ["PESTLE", "Diamond"]:
        st.markdown(f"**{"PESTLE" if fw == "PESTLE" else "Porter's Diamond"}**")
        st.dataframe(PES[PES.framework == fw][["factor", "driver", "indicator", "source_id"]], hide_index=True)

with T[7]:
    st.subheader("Summary")
    st.markdown(md("summary"))
    st.success(LEN[LEN.lens == "no_regret"].iloc[0].action)

with T[8]:
    st.subheader("Data snapshot and sources")
    st.markdown(f'<div class="panel"><b>Snapshot, not live.</b> Data were downloaded on <b>{SNAP}</b> and are stored in <code>data/</code>. '
                f'CBS 2024-2025 values are provisional and can be revised. Scenario inputs are team assumptions and are kept apart from observed data. '
                f'To refresh: run <code>refresh_data.py</code> (CBS) and edit <code>data/rvo_pipeline.csv</code> (RVO).</div>', unsafe_allow_html=True)
    for _, r in SRC.iterrows():
        st.markdown(f'<div class="panel"><b>{r.dataset}</b> <span class="pill">{r["table"]}</span> <span class="pill">{r.licence}</span>'
                    f'<p><b>Variables:</b> {r.variables} · <b>Units:</b> {r.units} · <b>Coverage:</b> {r.coverage} · <b>Accessed:</b> {r.access_date}</p>'
                    f'<p><b>Missing values:</b> {r.missing_values}</p><p><b>Transformations:</b> {r.transformations}</p>'
                    f'<p><a href="{r.url}" target="_blank" rel="noopener">{r.url} ↗</a></p></div>', unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    d1.download_button("↓ CBS history snapshot (CSV)", H.to_csv(index=False), "cbs_82610ENG_wind_snapshot.csv", "text/csv")
    d2.download_button("↓ RVO pipeline snapshot (CSV)", P.drop(columns="mw").to_csv(index=False), "rvo_pipeline_snapshot.csv", "text/csv")
    d3.download_button("↓ Sources log (CSV)", SRC.to_csv(index=False), "sources.csv", "text/csv")
    st.markdown(md("method"))
    st.dataframe(H.assign(status=H.provisional.map({1: "provisional", 0: "final"})).drop(columns="provisional"), hide_index=True)

st.caption(f"WINDSCOPE · university project (Turku School of Economics, BI 2026) · CBS 82610ENG · RVO Roadmap May 2026 · snapshot {SNAP} · not investment advice")
