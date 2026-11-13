import hashlib, html, json, os, re, runpy, shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, OUT = os.path.join(ROOT, "src"), os.path.join(ROOT, "_site")
BASE = "https://eyacademy.github.io/ai-guide/"

COLORS = {"anthropic": "#cc785c", "openai": "#1f1f1f", "google": "#34a853", "meta": "#0089f4", "xai": "#736cd3",
          "xiaomi": "#ff6900", "alibaba": "#ff7018", "qwen": "#ff7018", "z.ai": "#1c7ff8", "z ai": "#1c7ff8", "zhipu": "#1c7ff8",
          "stepfun": "#00c2b8", "moonshot": "#047afe", "kimi": "#047afe", "deepseek": "#2243e6",
          "minimax": "#eb3568", "mistral": "#fd6f00", "nvidia": "#76b900"}
LIGHT = {"#00c2b8", "#76b900"}
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]


LOGOS = json.load(open(os.path.join(SRC, "logos.json"), encoding="utf-8"))


def logo(creator, c, size=20):
    k = creator.lower()
    f = next((p for n, p in LOGOS.items() if n in k), None)
    if f:
        return f'<img src="{BASE}logos/{f}" width="{size}" height="{size}" alt="" loading="lazy">'
    return f'<b class="lgl" style="--c:{c}">{html.escape(creator[:1].upper())}</b>'


def color(creator):
    k = creator.lower()
    return next((c for n, c in COLORS.items() if n in k), "#9a9aa6")


def load_data():
    path = os.path.join(OUT, "data", "aa-index.json")
    if not os.path.exists(path):
        path = os.path.join(SRC, "aa-snapshot.json")
    return json.load(open(path, encoding="utf-8"))


def chart(data):
    models = data["models"][:30]
    top = max(m["score"] for m in models)
    bars, legend, seen = [], [], set()
    for i, m in enumerate(models, 1):
        c, creator = color(m["creator"]), html.escape(m["creator"])
        name = html.escape(m["name"] + (f' ({m["effort"]})' if m.get("effort") else ""))
        w = max(8, round(m["score"] / top * 100))
        bars.append(f'<li class="bar" title="{name} · {creator} · {m["score"]}"><span class="i">{i}</span><span class="lo">{logo(m["creator"], c)}</span><span class="n"><span>{name}</span><small>{creator}</small></span>'
                    f'<span class="t"><span class="f{" lt" if c in LIGHT else ""}" style="--c:{c};--w:{w}%">{m["score"]}</span></span></li>')
        if m["creator"] not in seen:
            seen.add(m["creator"])
            legend.append(f'<span><i style="background:{c}"></i>{creator}</span>')
    d = datetime.fromisoformat(data["updated"].replace("Z", "+00:00"))
    return len(models), "".join(bars), "".join(legend), f"Обновлено {d.day} {MONTHS[d.month - 1]} {d.year} · обновляется ежедневно"


TABS = [("cost", "Интеллект и цена", ("cost",),
         "Каждая точка — модель. Чем выше, тем умнее, чем левее, тем дешевле одна задача. "
         "Пунктир соединяет самые выгодные модели: за те же деньги умнее не найти."),
        ("time", "Время на задачу", ("time",),
         "Сколько минут модель в среднем тратит на одну задачу из рейтинга. Чем левее, тем быстрее. "
         "Пунктир соединяет модели, которые быстрее всех при своём уровне интеллекта."),
        ("tokens", "Токены и стоимость", ("tokens", "tokens_total", "cost", "cost_total"),
         "Сколько модель «думает» и во что это обходится. Меньше — лучше. "
         "Токены — это объём текста, который модель пишет, включая рассуждения.")]
SUBS = [("tokens", "Токены на задачу"), ("tokens_total", "Всего токенов"), ("cost", "Цена задачи"), ("cost_total", "Общая стоимость")]


def compare(data):
    rows = data.get("variants") or []
    has = lambda k: sum(1 for m in rows if m.get(k)) >= 5
    if not has("cost"):
        return ""
    tabs = [t for t in TABS if any(has(k) for k in t[2])]
    if not has("tokens"):
        tabs = [("tokens", "Стоимость", t[2], "Сколько стоит одна задача и весь прогон рейтинга по ценам API. Меньше — лучше.")
                if t[0] == "tokens" else t for t in tabs]
    tab_html = "".join(f'<button type="button" data-tab="{i}" data-note="{html.escape(note)}"{" class=on" if n == 0 else ""}>{t}</button>'
                       for n, (i, t, _, note) in enumerate(tabs))
    subs = [(k, t) for k, t in SUBS if has(k)]
    sub_html = "".join(f'<button type="button" data-sub="{k}"{" class=on" if n == 0 else ""}>{t}</button>' for n, (k, t) in enumerate(subs))
    colors = html.escape(json.dumps(COLORS, separators=(",", ":")), quote=True)
    return (f'<div class="cmp" data-colors="{colors}">'
            f'<div class="cmp-box"><div class="cmp-tabs">{tab_html}</div>'
            f'<div class="cmp-bar"><div class="cmp-subs" hidden>{sub_html}</div>'
            f'<div class="cmp-ctl"><span class="cmp-seg"><button type="button" data-scale="log" class=on>Лог</button>'
            f'<button type="button" data-scale="lin">Линейная</button></span>'
            f'<label class="cmp-par"><input type="checkbox" checked> Линия выгодности</label></div></div>'
            f'<p class="cmp-note">{html.escape(tabs[0][3])}</p>'
            f'<div class="cmp-wrap"><div class="cmp-main"><div class="cmp-plot"><p class="cmp-load">Загружаем данные…</p></div><div class="cmp-best"></div></div>'
            f'<aside class="cmp-side"><div class="cmp-side-h"><b>Модели</b><span class="cmp-count"></span></div>'
            f'<input class="cmp-q" type="search" placeholder="Найти модель" aria-label="Найти модель">'
            f'<div class="cmp-quick"><button type="button" data-q="top">Топ-12</button><button type="button" data-q="none">Снять все</button></div>'
            f'<label class="cmp-eff"><input type="checkbox" checked> Все уровни размышлений</label>'
            f'<div class="cmp-list"></div></aside></div></div></div>')


def rnd(v):
    """Round an estimate the way the slides do: 37 -> 35, 517 -> 520, 2585 -> 2 600."""
    step = 5 if v < 200 else 10 if v < 1000 else 100 if v < 20000 else 1000
    return max(step, round(v / step) * step)


def sp(v):
    return f"{v:,}".replace(",", "\u00a0")


def ver(name):
    return tuple(float(x) for x in re.findall(r"\d+(?:\.\d+)?", name)) or (0,)


def resolve(prices, pattern, fallback):
    hits = [n for n in prices if re.search(pattern, n)]
    return max(hits, key=ver) if hits else (fallback if fallback in prices else None)


def subscriptions(data):
    cfg = json.load(open(os.path.join(SRC, "plans.json"), encoding="utf-8"))
    prices = data.get("prices") or {}
    blend = lambda n: (3 * prices[n][0] + prices[n][1]) / 4
    base = resolve(prices, cfg["base"]["model"], cfg["base"]["fallback"])
    if not base:
        return "", ""
    cost = lambda n: cfg["base"]["response_usd"] * blend(n) / blend(base)
    short = lambda n: re.sub(r"^Claude ", "", n)
    rows, marks, tables = [], set(), []
    for pv in cfg["providers"]:
        dot = (f'<img class="pl-lg" src="{BASE}logos/{pv["logo"]}" width="22" height="22" alt="">' if pv.get("logo")
               else f'<i style="background:{pv["color"]}"></i>')
        rows.append(f'<tr class="pl-h"><th>{dot}{pv["name"]}</th><th>$/мес</th><th>API-эквивалент/мес</th><th>× цены</th></tr>')
        for pl in pv["plans"]:
            usd, star = pv["budget"] * pl["x"], "**" if pl.get("rough") else "*" if pl.get("unofficial") else ""
            marks.add(star)
            note = f' <small>({pl["note"]})</small>' if pl.get("note") else ""
            rows.append(f'<tr><td><b>{pv["name"]} {pl["name"]}</b>{note}</td><td class="pl-n">${pl["price"]}</td>'
                        f'<td>≈ ${sp(rnd(usd))}{star}</td><td><span class="pl-x" style="--c:{pv["color"]}">{round(usd / pl["price"])}×</span></td></tr>')
        # per-model table
        head = "".join(f'<th>{pl.get("short", pl["name"])}<br>${pl["price"]}</th>' for pl in pv["plans"])
        body = [f'<tr class="pl-lim"><td><b>{pv["limit_label"]}</b><small>{pv["limit_note"]}</small></td>'
                + "".join(f'<td>{pl["limit"]}</td>' for pl in pv["plans"]) + "</tr>"]
        resp = {}
        for m in pv["models"]:
            if "combo" in m:
                f_, o_ = (resolve(prices, x, None) for x in m["combo"])
                if not (f_ and o_):
                    continue
                cap = next((x.get("cap", 1) for x in pv["models"] if x.get("model") == m["combo"][0]), 1)
                title, cells = m["title"], []
                for i, pl in enumerate(pv["plans"]):
                    if i < m.get("from", 0):
                        cells.append('<td class="pl-no">—</td>')
                    else:
                        v = resp[f_][i] + (1 - cap) * resp[o_][i]
                        cells.append(f'<td><b>≈ {sp(rnd(v))}</b></td>')
            else:
                name = resolve(prices, m["model"], m.get("fallback"))
                if not name:
                    continue
                title, cells, n = short(name), [], len(pv["plans"])
                resp[name] = [pv["budget"] * pl["x"] * m.get("share", 1) / cost(name) for pl in pv["plans"]]
                free = m.get("free_from")
                for i, pl in enumerate(pv["plans"]):
                    if free is not None and i == free:
                        cells.append(f'<td colspan="{n - i}" class="pl-free">{m["free_text"]}</td>')
                        break
                    if i < m.get("from", 0):
                        lines = m.get("before") or ["нет"]
                        cells.append('<td class="pl-no">' + lines[0] + "".join(f"<small>{x}</small>" for x in lines[1:]) + "</td>")
                        continue
                    v, sub = resp[name][i], m.get("sub", "")
                    if m.get("tasks"):
                        sub = f"≈ {sp(rnd(pv['base_tasks'] * pl['x'] * cfg['base']['response_usd'] / cost(name)))} задач"
                    if m.get("sub_first") and i == m.get("from", 0):
                        o = next((k for k in resp if re.search(r"Opus", k)), None)
                        sub = m["sub_first"].replace("{ratio}", f"{v / resp[o][i]:.0f}") if o else ""
                    cells.append(f'<td><b>≈ {sp(rnd(v))}</b>' + (f"<small>{sub}</small>" if sub else "") + "</td>")
            body.append(f'<tr><td><b>{title}</b><small>{m["role"]}</small></td>{"".join(cells)}</tr>')
        tables.append(f'<div class="pl-wrap"><table class="pl pl-m"><thead><tr><th class="pl-p">{dot}{pv["name"]}</th>{head}</tr></thead>'
                      f'<tbody>{"".join(body)}</tbody></table></div>')
    summary = f'<div class="pl-wrap"><table class="pl pl-sum"><tbody>{"".join(rows)}</tbody></table></div>'
    foot = []
    if "*" in marks:
        foot.append("* Множители Pro неофициальные.")
    if "**" in marks:
        foot.append("** Для Go данных почти нет, это грубая оценка.")
    names = ["Сколько дают"] + [f'{pv["name"]} по моделям' for pv in cfg["providers"]]
    caps = ["API-эквивалент — сколько стоила бы та же работа по ценам API. " + " ".join(foot)] + [
        "Ответов агента в месяц: один ответ — один ход агента в Claude Code или Codex, в обычном чате сообщений получится больше. "
        "Числа пересчитываются каждый день по текущим ценам моделей."] * len(tables)
    panels = [summary] + tables
    caps[0] += f" Оценки по замерам пользователей на {cfg['as_of']}: компании не публикуют лимиты в долларах."
    tabs = "".join(f'<button type="button">{n}</button>' for n in names)
    body = "".join(f'<div class="pl-panel" hidden>{p}<p class="src">{caps[i]}</p></div>' for i, p in enumerate(panels))
    return tabs, body


RT = [("score", "Интеллект", [("score", "")],
       "Общий индекс: 10 тестов на агентные задачи, программирование, знания и научное мышление."),
      ("know", "Надёжность знаний", [("hall", "Галлюцинации"), ("acc", "Точность"), ("omni", "Итог")],
       "Вопросы на знания: за верный ответ плюс, за выдуманный минус, за честное «не знаю» ноль."),
      ("field", "По сферам", [("fin", "Финансы и учёт"), ("ops", "Стратегия и операции"), ("law", "Право"),
                              ("med", "Медицина"), ("eng", "Инженерия"), ("eco", "Экономика")],
       "Как модель справляется с рабочими задачами в отдельной сфере. Больше — лучше.")]


VALUE_NOTE = ("Какая модель выгоднее. Наведите на точку или столбец, чтобы увидеть подробности, справа можно выбрать модели "
              "и уровни размышлений. Цена задачи — средняя стоимость одной задачи из рейтинга по ценам API.")


def rating_tabs(data, value=False):
    rows = data.get("bench") or []
    has = lambda k: k == "score" or sum(1 for m in rows if m.get(k) is not None) >= 5
    tabs = [(i, t, [s for s in subs if has(s[0])], note) for i, t, subs, note in RT]
    tabs = [t for t in tabs if t[2]]
    if value:
        tabs.append(("value", "Цена и выгода", [], VALUE_NOTE))
    if len(tabs) < 2:
        return ""
    colors = html.escape(json.dumps(COLORS, separators=(",", ":")), quote=True)
    out = [f'<div class="rt" data-colors="{colors}"><div class="rt-tabs">']
    for n, (i, t, subs, note) in enumerate(tabs):
        out.append(f'<button type="button" data-rt="{i}" data-note="{html.escape(note)}"{" class=on" if n == 0 else ""}>{t}</button>')
    out.append("</div>")
    for i, t, subs, note in tabs:
        if len(subs) > 1:
            out.append(f'<div class="rt-subs" data-for="{i}" hidden>' + "".join(
                f'<button type="button" data-m="{k}"{" class=on" if n == 0 else ""}>{lbl}</button>' for n, (k, lbl) in enumerate(subs)) + "</div>")
    out.append(f'<p class="rt-note">{html.escape(tabs[0][3])}</p></div>')
    return "".join(out)


def h3_sub(t, cap):
    return f'<h3>{t}</h3><p class="cap">{cap}</p>'


data = load_data()
# Knowledge reliability comes from the API with a Pro key; until then from src/omniscience.json.
data["bench"] = [m for m in data.get("bench") or [] if not m.get("manual")]
data.pop("knowledge_note", None)
if sum(1 for m in data["bench"] if m.get("omni") is not None) < 5:
    manual = json.load(open(os.path.join(SRC, "omniscience.json"), encoding="utf-8"))
    data["bench"].extend(dict(m, manual=True) for m in manual["models"])
    d0 = datetime.fromisoformat(manual["as_of"])
    data["knowledge_note"] = f"Данные на {d0.day} {MONTHS[d0.month - 1]} {d0.year}"
data["logos"] = LOGOS
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
json.dump(data, open(os.path.join(OUT, "data", "aa-index.json"), "w", encoding="utf-8"), ensure_ascii=False)
body = runpy.run_path(os.path.join(SRC, "content.py"), init_globals={"MODELS": data.get("by_creator", {}), "BASE": BASE})["BODY"]
count, bars, legend, date = chart(data)
sub_tabs, sub_panels = subscriptions(data)
cmp_html = compare(data)
body = body.replace("{RATING_TABS}", rating_tabs(data, bool(cmp_html))).replace("{SUBS_TABS}", sub_tabs).replace("{SUBS_PANELS}", sub_panels).replace("{COMPARE}", cmp_html).replace("{CHART_N}", str(count)).replace("{CHART_BARS}", bars).replace("{CHART_LEGEND}", legend).replace("{CHART_DATE}", date)
css = open(os.path.join(SRC, "style.css"), encoding="utf-8").read()
version = hashlib.sha1((css + body).encode("utf-8")).hexdigest()[:12]
body = body.replace("{VERSION}", version, 1)
style = f'<style id="eyai-style">\n{css}</style>\n'
script = f'<script src="{BASE}script.js" defer></script>\n'

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "guide.html"), "w", encoding="utf-8").write(style + body)
# In Tilda the block stays hidden until script.js has swapped in the current version, so the old copy never flashes.
open(os.path.join(OUT, "tilda.html"), "w", encoding="utf-8").write(
    style + body.replace('<div id="eyai" ', '<div id="eyai" class="eyai-wait" ', 1) + "\n" + script)
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
    '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1">'
    '<title>Гид по ИИ-инструментам · Академия бизнеса EY</title>'
    '<meta name="robots" content="noindex"><link rel="canonical" href="https://eyacademyeurasia.com/ai-guide">'
    '<style>body{margin:0;background:#f6f6fa}#eyai{padding-top:0!important}</style></head><body>'
    + style + body + script + "</body></html>")
shutil.copy(os.path.join(SRC, "script.js"), os.path.join(OUT, "script.js"))
shutil.copytree(os.path.join(SRC, "logos"), os.path.join(OUT, "logos"), dirs_exist_ok=True)
print("version", version, "|", date)
