"""Confirm preview.html (JS) gives the same numbers as model.py (Python). Needs Node.  Run: python tests/parity_js.py"""
import itertools, json, re, subprocess, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd, model as M

html = open("preview.html", encoding="utf-8").read()
core = re.search(r"//--CORE--(.*?)//--/CORE--", html, re.S).group(1)
data = json.loads(re.search(r"const D=(\{.*?\});\n//--CORE--", html, re.S).group(1))
H, P = M.load_history(), M.load_pipeline(); BASE = float(H.loc[H.year == 2025, "offshore_mw"].iloc[0])

cases = [(d, g, u) for d, g, u in itertools.product([0, 1, 2, 3], [True, False], [0, 2.0, 5.5, 8.8, 11.4])]
js = f"""const D={json.dumps(data)};{core}
const P=D.pipe,H=D.hist,B={BASE},out={{sc:[],fc:null,ho:{{}},split:pipelineSplit(P)}};
for(const [d,g,u] of {json.dumps(cases)}){{const p=scenarioPath(P,B,d,g,u);out.sc.push({{cum:p.cum,add:p.add,m:metrics(p,21000,u)}})}}
const h=H.filter(r=>r.year>=2015);out.fc=linearForecast(h.map(r=>r.year),h.map(r=>r.offshore_mw),2032).rows;
for(let y=2018;y<=2024;y++){{const o=holdout(H,y,2015);out.ho[y]={{mae_linear:o.mae_linear,mae_naive:o.mae_naive,coverage:o.coverage}}}}
console.log(JSON.stringify(out))"""
J = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)

close = lambda a, b: abs(a - b) < 1e-6
n = 0
for (d, g, u), r in zip(cases, J["sc"]):
    p = M.scenario_path(P, BASE, d, g, u); m = M.metrics(p, 21000, undated_gw=u)
    assert all(close(a, b) for a, b in zip(p.cumulative_mw, r["cum"])) and all(close(a, b) for a, b in zip(p.additions_mw, r["add"]))
    for k in m:
        a, b = m[k], r["m"][k]
        assert (a is None and b is None) or close(a, b), (d, g, u, k, a, b)
    n += 1
fc, _ = M.linear_forecast(H[H.year >= 2015].year, H[H.year >= 2015].offshore_mw)
for (_, a), b in zip(fc.iterrows(), J["fc"]):
    assert all(close(a[k], b[k]) for k in ["forecast_mw", "lo_mw", "hi_mw"])
for y in range(2018, 2025):
    _, s = M.holdout(H, y)
    assert all(close(s[k], J["ho"][str(y)][k]) for k in s), y
assert close(J["split"][0], 7520) and close(J["split"][1], 11400)
print(f"PARITY OK: {n} scenario settings, forecast (7 yrs), 7 holdout years; dated/undated = {J['split']}")

# headless render of all 9 tabs with a stub DOM
stub = f"""const els={{}};global.document={{getElementById:id=>els[id]||(els[id]={{}}),querySelectorAll:()=>[]}};
const src={json.dumps(html)};const code=src.slice(src.indexOf('<script>')+8,src.lastIndexOf('</script>'));
const code2=code.replace('draw()}}\\n','draw();for(let i=0;i<9;i++){{S.tab=i;draw();if(!els.out.innerHTML.includes("<h3>"))throw new Error("tab "+i)}}console.log("RENDER OK",els.out.innerHTML.length)}}\\n');
eval(code2)"""
print(subprocess.run(["node", "-e", stub], capture_output=True, text=True).stdout or "render stub failed")
