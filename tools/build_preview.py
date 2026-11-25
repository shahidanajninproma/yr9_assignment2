"""Build preview.html (offline backup) by embedding the CSV/MD data into tools/preview_template.html.
Run after editing any CSV/MD:  python tools/build_preview.py"""
import json, math
from pathlib import Path
import pandas as pd

R = Path(__file__).resolve().parent.parent
clean = lambda df: json.loads(df.astype(object).where(df.notna(), None).to_json(orient="records"))
hist = pd.read_csv(R / "data/cbs_82610ENG_wind.csv")
pipe = pd.read_csv(R / "data/rvo_pipeline.csv")
pipe["year"] = pipe["year"].astype("Int64")
pipe = pipe.rename(columns={"tender_dependent": "tender"})
D = {"hist": clean(hist), "pipe": clean(pipe), "scen": clean(pd.read_csv(R / "scenarios.csv")),
     "lens": clean(pd.read_csv(R / "lenses.csv")), "pestle": clean(pd.read_csv(R / "content/pestle.csv")),
     "src": clean(pd.read_csv(R / "sources.csv")),
     "md": {p.stem: p.read_text(encoding="utf-8") for p in (R / "content").glob("*.md")}}
html = (R / "tools/preview_template.html").read_text(encoding="utf-8").replace("/*DATA*/null", json.dumps(D, ensure_ascii=False))
(R / "preview.html").write_text(html, encoding="utf-8")
print("preview.html written", len(html) // 1024, "KB")
