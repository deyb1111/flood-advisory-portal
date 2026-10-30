import json, pathlib, requests

r = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={"q": "Pasig, Metro Manila, Philippines", "format": "geojson",
            "polygon_geojson": 1, "limit": 10},
    headers={"User-Agent": "bantay-daan-pasig/1.0"}, timeout=30)
r.raise_for_status()
feats = [f for f in r.json()["features"]
         if f["geometry"]["type"] in ("Polygon", "MultiPolygon")
         and f["properties"].get("category") == "boundary"
         and f["properties"].get("display_name", "").startswith("Pasig")]
assert feats, "No Pasig boundary polygon found"
print("Using:", feats[0]["properties"]["display_name"])
out = pathlib.Path("app/static/data"); out.mkdir(parents=True, exist_ok=True)
(out / "pasig.geojson").write_text(json.dumps(
    {"type": "FeatureCollection", "features": feats[:1]}))