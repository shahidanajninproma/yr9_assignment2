# Dutch offshore wind to 2032: supplier decision dashboard
Business Intelligence (TSE, Autumn 2026), Assignment 2. Country: Netherlands. Industry: offshore wind. Primary user: an offshore wind **supplier** (installation, cables, vessels) deciding whether to invest in Dutch capacity to 2032. Comparison lenses: **Developer** (bid or not) and **Policymaker** (will the target be reached?).

## Open it (no paid account needed)
- **Windows, one click:** double-click **`run_windows.bat`**. First run creates a private `.venv`, installs the packages (needs internet and Python 3.10+) and opens the dashboard in your browser; later runs start in seconds. Close the black window to stop it.
- **Live, free:** deploy on Streamlit Community Cloud (see below).
- **Stable backup:** open `preview.html` in any browser. Self-contained, works offline (same logic in JS, data embedded).
- **Other systems:** `pip install -r requirements.txt` then `streamlit run app.py`.

## Deploy free on Streamlit Community Cloud
1. Create a free GitHub account; create a **public** repository and upload the contents of this folder (GitHub web: *Add file -> Upload files*; keep the `data/`, `content/`, `.streamlit/` folders).
2. Go to share.streamlit.io, sign in with GitHub, click **Create app**, choose the repository, branch `main`, main file path `app.py`, and click **Deploy**. Under *Advanced settings* choose Python 3.11 or 3.12.
3. Every commit made in the GitHub web editor redeploys automatically. Submit the app link plus `preview.html` as the stable backup. No paid plan or API keys are needed; the app makes no network calls at run time.

## Use it
The look follows the supplied `Netherlands_WindEnergy_Dashboard_v1.html` (dark theme, sidebar, KPI cards, capacity mix donut, stacked capacity bars, annual net change). A strip under the title and a sidebar box show the **data snapshot date and sources on every page**; the *Data & sources* tab lists every dataset with variables, units, coverage, access date, missing values, transformations, links, and CSV downloads.
Pick a preset in the sidebar (Roadmap delivered / Delayed build-out / Cost squeeze) or move the sliders; every tab updates. A "Custom" notice appears when sliders differ from the preset. Colours: **blue = observed data**, **gold dashed = model forecast**, **teal/green = scenario assumption**. Every chart shows units and source.

## Edit content without Python (GitHub web editor, pencil icon -> commit)
| File | What it controls |
|---|---|
| `scenarios.csv` | preset names, delay, Gamma yes/no (1/0), undated GW, drivers |
| `lenses.csv` | readout and action per lens x scenario (+ `no_regret` row). Placeholders `{cap2032} {gap} {year} {peak} {peak_year} {zero} {dated} {undated} {target}` are filled with live numbers |
| `content/*.md` | intro, summary, forecast note, method text |
| `content/pestle.csv` | PESTLE and Diamond rows tied to dashboard indicators |
| `sources.csv` | data log |
| `data/rvo_pipeline.csv` | RVO sites (leave `year` empty for "to be determined"; `tender_dependent`=1 for Gamma-A/B) |

Keep column headers unchanged. After CSV/MD edits, the coder runs `python tools/build_preview.py` to refresh `preview.html`.

## Data (dated snapshot, accessed 2026-11-25; not live)
- CBS StatLine table **82610ENG** (CC BY 4.0), OData API. Offshore = `E006638`, onshore = `E006637`; fields `ElectricalCapacityEndOfYear_8` (MW) and `GrossProductionOfElectricity_2` (mln kWh), 2006-2025. 2024-2025 are marked provisional (per team brief; confirm in CBS footnotes). Cross-check passed: offshore 2023/2024/2025 = 4110/4748/4748 MW.
- RVO Offshore Wind Energy Roadmap (May 2026): 14 sites; 6 have an expected year, 8 are "to be determined". 21 GW by end-2032: RVO planning note.
- Full log (units, coverage, missing values, transformations): `sources.csv`.

**Data revision note.** CBS revised 2025 after our first API pull: the current StatLine page (82610NED) shows onshore 2025 = 7,035 MW and offshore production 15,905 mln kWh (an earlier OData response showed 7,017 and 15,919). The repo uses the current values, which match the CBS wind longread. Offshore capacity (4,748 MW) is identical in both, so scenarios and forecasts are unaffected. Running `refresh_data.py` will overwrite the CSV with whatever the API returns at that time; re-check these two values afterwards.

## Refresh
`python refresh_data.py` re-downloads the CBS table, checks the 2023/2024 cross-check, and rewrites `data/cbs_82610ENG_wind.csv`. Then update `access_date` in `sources.csv` and run `python tools/build_preview.py`. The RVO pipeline is updated by hand in `data/rvo_pipeline.csv` from the RVO page.

## Method (details in the Data & method tab)
- **Scenario model** (`model.py`): 2025 base + dated RVO sites in expected year + delay (past 2032 drops out) + Gamma-A/B only if the tender succeeds + undated GW spread evenly 2030-2032. Preset values are **illustrative team assumptions**.
- **Forecast:** OLS trend on offshore capacity 2015-2025 with ~95% prediction band; holdout (train to a chosen year, default 2021) against a naive last-value benchmark. Capacity arrives in whole farms, so the trend is only a benchmark.
- **Tests:** `python tests/test_model.py` (model) and `python tests/parity_js.py` (JS equals Python; needs Node).

## Limitations
- The 21 GW target comes from an older RVO planning note; the May 2026 Roadmap states **23 GW**. The target is editable in the sidebar.
- Hollandse Kust (west) VI is "2026-2027" and is read as 2027. "About X GW" values are used as stated.
- Delay applies to dated sites only; undated GW is a direct input, with no site-level timing.
- Scenarios are possible futures, not predictions, and carry no probabilities.
- Few holdout points; results indicative only. LLM-generated text must not replace verified numbers.

## Tools and AI use
Python, pandas, numpy, Streamlit, Plotly; vanilla JS for the preview. Claude (Anthropic) was used to draft code and text; the team verified data against CBS/RVO sources and the code against tests (see `DEV_LOG.md`).
