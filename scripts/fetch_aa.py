import json, os, re, urllib.request
from datetime import datetime, timezone

API = "https://artificialanalysis.ai/api/v2/language/models/free"
PUBLISHED = "https://eyacademy.github.io/ai-guide/data/aa-index.json"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_site", "data", "aa-index.json")


def get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "ai-guide", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def version(name):
    # Ignore model sizes (120B, A23B) and dates (0309).
    nums = re.findall(r"(?<![\d.])(\d+(?:\.\d+)?)(?![\d.]*[bBtT]\b)", name)
    return tuple(float(x) for x in nums if float(x) < 100) or (0,)


def latest(models):
    # Keep only the newest version in each line: Claude Opus 5.5 over Claude Opus 5.
    families = {}
    for m in models:
        fam = (m["creator"], re.sub(r"[\d.\-\s]+", " ", m["name"].lower()).strip())
        if fam not in families or version(m["name"]) > version(families[fam]["name"]):
            families[fam] = m
    return list(families.values())

def fetch():
    key = os.environ["AA_API_KEY"]
    models, page = [], 1
    while page <= 10:
        body = get(f"{API}?page={page}", {"x-api-key": key})
        models += body.get("data") or []
        if not (body.get("pagination") or {}).get("has_more"):
            break
        page += 1
    best = {}
    for m in models:
        score = (m.get("evaluations") or {}).get("artificial_analysis_intelligence_index")
        if not isinstance(score, (int, float)):
            continue
        name = re.sub(r"\s*\([^)]*\)\s*$", "", m.get("name", "")).strip()
        if name not in best or score > best[name]["score"]:
            best[name] = {"name": name, "creator": (m.get("model_creator") or {}).get("name", ""), "score": round(score)}
    top = sorted(latest(best.values()), key=lambda x: -x["score"])[:20]
    if len(top) < 5:
        raise ValueError("too few models")
    return {"updated": datetime.now(timezone.utc).isoformat(), "models": top}


try:
    data = fetch()
    print("fetched", len(data["models"]), "models")
except Exception as e:
    print("API failed:", e)
    try:
        data = get(PUBLISHED)
        print("using published data from", data["updated"])
    except Exception as e2:
        print("no published data:", e2)
        data = None

if data:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
