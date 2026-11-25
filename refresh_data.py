"""Refresh data/cbs_82610ENG_wind.csv from the CBS OData API (CC BY 4.0).
Usage: python refresh_data.py   (needs internet; stdlib + pandas only)."""
import json, urllib.request
import pandas as pd

URL = "https://opendata.cbs.nl/ODataApi/OData/82610ENG/TypedDataSet"
OFF, ON = "E006638", "E006637"
PROVISIONAL = (2024, 2025)  # per team brief; confirm in CBS table footnotes


def fetch(url=URL):
    rows = []
    while url:
        with urllib.request.urlopen(url, timeout=60) as r:
            d = json.load(r)
        rows += d["value"]; url = d.get("odata.nextLink")
    return rows


def parse(rows):
    df = pd.DataFrame(rows)
    df["code"] = df["EnergySourcesTechniques"].str.strip()      # values carry a trailing space
    df["year"] = df["Periods"].str[:4].astype(int)              # '2025JJ00' -> 2025
    off = df[df.code == OFF].set_index("year"); on = df[df.code == ON].set_index("year")
    out = pd.DataFrame({"offshore_mw": off["ElectricalCapacityEndOfYear_8"],
                        "offshore_prod_mln_kwh": off["GrossProductionOfElectricity_2"],
                        "onshore_mw": on["ElectricalCapacityEndOfYear_8"]}).dropna(subset=["offshore_mw"]).reset_index()
    out["provisional"] = out["year"].isin(PROVISIONAL).astype(int)
    return out.astype({"offshore_mw": int, "offshore_prod_mln_kwh": int, "onshore_mw": int})


if __name__ == "__main__":
    out = parse(fetch())
    g = lambda y: int(out.loc[out.year == y, "offshore_mw"].iloc[0])
    assert (g(2023), g(2024)) == (4110, 4748), "Cross-check failed: CBS values changed; review before overwriting"
    out.to_csv("data/cbs_82610ENG_wind.csv", index=False)
    print(f"Wrote {len(out)} rows ({out.year.min()}-{out.year.max()}). Update access_date in sources.csv.")
