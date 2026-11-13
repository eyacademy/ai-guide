import json, os, re, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone

API = "https://artificialanalysis.ai/api/v2/language/models"
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
        fam = (m["creator"], re.sub(r"[\d.\-\s]+", " ", re.sub(r"\bpreview\b", "", m["name"].lower())).strip())
        if fam not in families or version(m["name"]) > version(families[fam]["name"]):
            families[fam] = m
    return list(families.values())

def num(x):
    return x if isinstance(x, (int, float)) and x > 0 else None


def metrics(m):
    # Cost of a task and of the full Intelligence Index run. Pro keys also get time and output tokens.
    ic = m.get("artificial_analysis_intelligence_index_cost") or {}
    cost, total = num((ic.get("cost_per_task") or {}).get("total_cost")), num(ic.get("total_cost"))
    tokens_total = num((m.get("artificial_analysis_intelligence_index_token_counts") or {}).get("output_tokens"))
    tasks = total / cost if cost and total else None
    return {"cost": cost and round(cost, 4), "cost_total": total and round(total),
            "time": (t := num((m.get("performance_v3") or {}).get("time_per_task_seconds"))) and round(t),
            "tokens": round(tokens_total / tasks) if tokens_total and tasks else None,
            "tokens_total": tokens_total and round(tokens_total)}


BENCH = {"omni": "aa_omniscience_index", "acc": "aa_omniscience_accuracy", "nonhall": "aa_omniscience_non_hallucination_rate",
         "fin": "artificial_analysis_finance_and_accounting_index", "ops": "artificial_analysis_strategy_and_ops_index",
         "law": "artificial_analysis_legal_index", "med": "artificial_analysis_healthcare_and_medical_index",
         "eng": "artificial_analysis_engineering_index", "eco": "artificial_analysis_economics_index"}


def bench(ev):
    # Knowledge (Pro keys only) and per-field capability indexes. Rates become percentages.
    out = {}
    for k, f in BENCH.items():
        v = ev.get(f)
        if isinstance(v, (int, float)):
            out[k] = round(v * 100 if k in ("acc", "nonhall") else v, 1)
    if "nonhall" in out:
        out["hall"] = round(100 - out.pop("nonhall"), 1)
    return out


def pages(url, key):
    models, page = [], 1
    while page <= 10:
        body = get(f"{url}?page={page}", {"x-api-key": key})
        models += body.get("data") or []
        if not (body.get("pagination") or {}).get("has_more"):
            break
        page += 1
    return models


def fetch():
    key = os.environ["AA_API_KEY"]
    try:
        models = pages(API, key)
    except urllib.error.HTTPError as e:
        if e.code != 403:
            raise
        models = pages(API + "/free", key)
    year_ago = (datetime.now(timezone.utc) - timedelta(days=365)).date().isoformat()
    best, variants = {}, []
    for m in models:
        score = (m.get("evaluations") or {}).get("artificial_analysis_intelligence_index")
        if not isinstance(score, (int, float)):
            continue
        full = m.get("name", "").strip()
        name = re.sub(r"\s*\([^)]*\)\s*$", "", full).strip()
        effort = full[len(name):].strip(" ()").lower().split(",")[0].strip()
        creator = (m.get("model_creator") or {}).get("name", "")
        if (m.get("release_date") or "") >= year_ago:
            variants.append({"family": name, "effort": effort, "creator": creator, "score": round(score, 1), **metrics(m)})
        if name not in best or score > best[name]["score"]:
            pr = m.get("pricing") or {}
            best[name] = {"name": name, "creator": creator, "score": round(score), "effort": effort,
                          "bench": bench(m.get("evaluations") or {}),
                          "price": [num(pr.get("price_1m_input_tokens")), num(pr.get("price_1m_output_tokens"))],
                          "released": m.get("release_date") or "", **metrics(m)}
    current = sorted(latest(best.values()), key=lambda x: -x["score"])
    by_creator = {}
    for m in current:
        if m["released"] >= year_ago:
            by_creator.setdefault(m["creator"], []).append(m["name"])
    top = [{k: m[k] for k in ("name", "creator", "score", "effort")} for m in current[:30]]
    if len(top) < 5:
        raise ValueError("too few models")
    # Chart picker: every variant from the last year; the top current lines are ticked by default.
    variants = [v for v in variants if v["cost"] or v["time"]]
    default = [m["name"] for m in current if m["released"] >= year_ago and any(v["family"] == m["name"] for v in variants)][:12]
    # API list prices of current models, $ per million input/output tokens, for the subscription tables.
    prices = {m["name"]: m["price"] for m in current if all(m["price"])}
    benches = [{"name": m["name"], "creator": m["creator"], "effort": m["effort"], **m["bench"]}
               for m in current if m["bench"] and m["released"] >= year_ago]
    return {"updated": datetime.now(timezone.utc).isoformat(), "models": top, "by_creator": by_creator,
            "variants": variants, "default": default, "prices": prices, "bench": benches}

try:
    data = fetch()
    print("fetched", len(data["models"]), "models,", len(data["variants"]), "variants with cost or time")
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
