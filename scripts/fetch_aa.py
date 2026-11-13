import json, os, re, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone

API = "https://artificialanalysis.ai/api/v2/language/models"
# Arena rankings for pictures, video and sound; the free tier returns name, creator and elo.
MEDIA = {"image": "text-to-image", "video": "text-to-video", "speech": "text-to-speech", "music": "music/instrumental"}
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
            "tokens_total": tokens_total and round(tokens_total),
            "speed": (v := pick(m, SPEED)) and round(v, 1), "ttft": (v := pick(m, TTFT)) and round(v, 2)}


# Output speed (tokens/s) and wait for the first token (s). The field names differ between API
# versions, so try the known spellings at the top level and inside performance_v3.
SPEED = ("median_output_tokens_per_second", "output_tokens_per_second", "output_speed_tokens_per_second", "output_speed")
TTFT = ("median_time_to_first_token_seconds", "time_to_first_token_seconds", "ttft_seconds", "time_to_first_token")


def pick(m, names):
    for src in (m.get("performance_v3") or {}, m):
        for n in names:
            v = num(src.get(n))
            if v:
                return v
    return None


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


def media(key):
    """Model names of one media arena, best first. Empty when the tier has no access."""
    out = {}
    for kind, path in MEDIA.items():
        try:
            body = get(f"https://artificialanalysis.ai/api/v2/media/{path}/models/free", {"x-api-key": key})
            rows = body.get("data") or []
        except Exception as e:
            print("media", kind, "failed:", e)
            continue
        best = {}
        for m in rows:
            name = re.sub(r"\s*\([^)]*\)\s*$", "", m.get("name") or "").strip()
            elo = m.get("elo")
            if name and isinstance(elo, (int, float)) and elo > best.get(name, -1):
                best[name] = elo
        out[kind] = sorted(best, key=lambda n: -best[n])
    return out


# Models no benchmark ranks; the version comes from the article's own text.
WIKI = {"midjourney": ("Midjourney", r"\bV(\d+(?:\.\d+)?)\b", "V")}


def wiki_versions():
    out = {}
    for key, (title, pat, prefix) in WIKI.items():
        try:
            body = get("https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content"
                       f"&rvslots=main&format=json&titles={title}")
            txt = next(iter(body["query"]["pages"].values()))["revisions"][0]["slots"]["main"]["*"]
            found = [float(v) for v in re.findall(pat, txt)]
            if found:
                top = max(found)
                out[key] = prefix + (f"{top:g}" if top % 1 else f"{int(top)}")
        except Exception as e:
            print("wiki", key, "failed:", e)
    return out


def fetch():
    key = os.environ["AA_API_KEY"]
    try:
        models = pages(API, key)
    except urllib.error.HTTPError as e:
        if e.code != 403:
            raise
        models = pages(API + "/free", key)
    if models:  # field names for the log, to check speed and latency are found
        print("model fields:", sorted(models[0]), "| performance_v3:", sorted((models[0].get("performance_v3") or {})))
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
    return {"updated": datetime.now(timezone.utc).isoformat(), "models": top, "by_creator": by_creator, "media": media(key),
            "variants": variants, "default": default, "prices": prices, "bench": benches, "extra": wiki_versions()}

try:
    data = fetch()
    print("fetched", len(data["models"]), "models,", len(data["variants"]), "variants with cost or time")
    print("media:", {k: len(v) for k, v in (data.get("media") or {}).items()}, "| extra:", data.get("extra"))
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
