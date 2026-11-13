import hashlib, html, json, math, os, re, runpy, shutil
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
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

# One source of text, two languages: src/en.json maps each Russian string to its English twin.
LANG, TR, MISS = "ru", {}, []
CYR = re.compile(r"[А-Яа-яЁё]")


def T(s):
    if LANG == "ru" or not isinstance(s, str) or not s:
        return s
    v = TR.get(s)
    if v is not None:
        return v
    if CYR.search(s) and s not in MISS:
        MISS.append(s)
    return s


def human_date(d):
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}" if LANG == "ru" else f"{MONTHS_EN[d.month - 1]} {d.day}, {d.year}"


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


def nice_step(top):
    """Round step for the scale behind the columns, same rule as in script.js."""
    raw = top / 5
    p = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    m = raw / p
    return (1 if m <= 1 else 2 if m <= 2 else 2.5 if m <= 2.5 else 5 if m <= 5 else 10) * p


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
    step, grid, v = nice_step(top), [], 0.0
    while v <= top + step / 2:                       # the page ships the scale; script.js redraws it per tab
        if v:                                        # no line at zero: it would run into the logos
            grid.append(f'<i style="--g:{v / top * 100:.2f}%"><b>{v:g}</b></i>')
        v += step
    d = datetime.fromisoformat(data["updated"].replace("Z", "+00:00"))
    return (len(models), "".join(bars), "".join(legend),
            T("Обновлено {date} · обновляется ежедневно").replace("{date}", human_date(d)), "".join(grid))


TABS = [("cost", "Интеллект и цена", ("cost",),
         "Каждая точка — модель. Чем выше, тем умнее, чем левее, тем дешевле одна задача. "
         "Пунктир соединяет самые выгодные модели: за те же деньги умнее не найти."),
        ("time", "Время на задачу", ("time",),
         "Сколько минут модель в среднем тратит на одну задачу из рейтинга. Чем левее, тем быстрее. "
         "Пунктир соединяет модели, которые быстрее всех при своём уровне интеллекта."),
        ("tokens", "Токены и стоимость", ("tokens", "tokens_total", "cost", "cost_total"),
         "Сколько модель «думает» и во что это обходится. Меньше — лучше. "
         "Токены — это объём текста, который модель пишет, включая рассуждения."),
        ("speed", "Скорость и задержка", ("speed", "ttft"),
         "Скорость вывода — сколько токенов в секунду модель выдаёт, больше — лучше. "
         "Задержка — сколько секунд проходит до первого токена ответа, меньше — лучше.")]
SUBS = {"tokens": [("tokens", "Токены на задачу"), ("tokens_total", "Всего токенов"), ("cost", "Цена задачи"), ("cost_total", "Общая стоимость")],
        "speed": [("speed", "Скорость вывода"), ("ttft", "Задержка")]}
SUB_NOTE = ("Цена задачи внутри подписки: часть цены тарифа, которая приходится на одну задачу при полном использовании лимита. "
            "Полые точки — модели, для которых нет данных о подписке; они показаны по цене API.")


def compare(data):
    rows = data.get("variants") or []
    has = lambda k: sum(1 for m in rows if m.get(k)) >= 5
    if not has("cost"):
        return ""
    tabs = [t for t in TABS if any(has(k) for k in t[2])]
    if not has("tokens"):
        tabs = [("tokens", T("Стоимость"), t[2], T("Сколько стоит одна задача и весь прогон рейтинга по ценам API. Меньше — лучше."))
                if t[0] == "tokens" else t for t in tabs]
    tab_html = "".join(f'<button type="button" data-tab="{i}" data-note="{html.escape(T(note))}"{" class=on" if n == 0 else ""}>{T(t)}</button>'
                       for n, (i, t, _, note) in enumerate(tabs))
    sub_html = ""
    for tab, items in SUBS.items():
        items = [(k, t) for k, t in items if has(k)]
        sub_html += "".join(f'<button type="button" data-sub="{k}" data-for="{tab}"{" class=on" if n == 0 else ""}>{T(t)}</button>'
                            for n, (k, t) in enumerate(items))
    price = "" if not data.get("subs") else (
        f'<span class="cmp-seg cmp-price"><button type="button" data-price="api">{T("По API")}</button>'
        f'<button type="button" data-price="sub" class=on>{T("По подписке")}</button></span>'
        f'<span class="cmp-seg cmp-tier"><button type="button" data-tier="basic" class=on>{T("Тариф $20")}</button>'
        f'<button type="button" data-tier="top">{T("Тариф $100+")}</button></span>')
    colors = html.escape(json.dumps(COLORS, separators=(",", ":")), quote=True)
    return (f'<div class="cmp" data-colors="{colors}">'
            f'<div class="cmp-box"><div class="cmp-tabs">{tab_html}</div>'
            f'<div class="cmp-bar"><div class="cmp-subs" hidden>{sub_html}</div>'
            f'<div class="cmp-ctl">{price}<span class="cmp-seg"><button type="button" data-scale="log" class=on>{T("Лог")}</button>'
            f'<button type="button" data-scale="lin">{T("Линейная")}</button></span>'
            f'<label class="cmp-par"><input type="checkbox" checked> {T("Линия выгодности")}</label></div></div>'
            f'<p class="cmp-note" data-sub-note="{html.escape(T(SUB_NOTE))}">{html.escape(T(tabs[0][3]))}</p>'
            f'<div class="cmp-wrap"><div class="cmp-main"><div class="cmp-plot"><p class="cmp-load">{T("Загружаем данные…")}</p></div><div class="cmp-best"></div></div>'
            f'<aside class="cmp-side"><div class="cmp-side-h"><b>{T("Модели")}</b><span class="cmp-count"></span></div>'
            f'<input class="cmp-q" type="search" placeholder="{T("Найти модель")}" aria-label="{T("Найти модель")}">'
            f'<div class="cmp-quick"><button type="button" data-q="top">{T("Топ-12")}</button><button type="button" data-q="none">{T("Снять все")}</button></div>'
            f'<label class="cmp-eff"><input type="checkbox" checked> {T("Все уровни размышлений")}</label>'
            f'<div class="cmp-list"></div></aside></div></div></div>')


def rnd(v):
    """Round an estimate the way the slides do: 37 -> 35, 517 -> 520, 2585 -> 2 600."""
    step = 5 if v < 200 else 10 if v < 1000 else 100 if v < 20000 else 1000
    return max(step, round(v / step) * step)


def sp(v):
    # thin space between thousands in Russian, a comma in English
    return f"{v:,}" if LANG != "ru" else f"{v:,}".replace(",", "\u00a0")


def ver(name):
    return tuple(float(x) for x in re.findall(r"\d+(?:\.\d+)?", name)) or (0,)


def resolve(prices, pattern, fallback, data=None, creator=None, rank=None, used=()):
    """Pick a model for a table row, surviving renamed model lines.

    Current models first, then the creator's Nth strongest, then any priced name.
    """
    hits = [n for n in prices if re.search(pattern, n) and n not in used]
    if hits:
        return max(hits, key=ver)
    if fallback in prices and fallback not in used:
        return fallback
    # The whole model line is gone: fall back to the creator's Nth strongest current model.
    cur = [m["name"] for m in (data or {}).get("models") or []
           if m.get("creator", "").lower() == (creator or "").lower() and m["name"] in prices]
    if rank and len(cur) >= rank and cur[rank - 1] not in used:
        print("resolve:", pattern, "->", cur[rank - 1], "(model line renamed)")
        return cur[rank - 1]
    return None


def sub_ratios(data):
    """Share of the API price a task costs inside a subscription, per model line and plan tier.

    {family: {"basic": [ratio, plan], "top": [ratio, plan]}}; ratio 0 means the plan barely spends
    its limit on that model, None that the plan does not include it. Lines with no plan data are left out.
    """
    cfg = json.load(open(os.path.join(SRC, "plans.json"), encoding="utf-8"))
    pt = cfg.get("per_task") or {}
    fams = sorted({v["family"] for v in data.get("variants") or []})
    out = {}
    for pv in cfg["providers"]:
        for tier, floor in (pt.get("tiers") or {}).items():
            i, pl = next(((i, pl) for i, pl in enumerate(pv["plans"]) if pl["price"] >= floor), (None, None))
            if pl is None:
                continue
            for m in pv["models"]:
                if "combo" in m:
                    continue
                if i < m.get("from", 0):
                    r = None
                elif m.get("free_from") is not None and i >= m["free_from"]:
                    r = 0
                else:
                    r = round(pl["price"] / (pv["budget"] * pl["x"] * m.get("share", 1)), 4)
                for f in fams:
                    if re.search(m["model"], f):
                        out.setdefault(f, {})[tier] = [r, f'{pv["name"]} {pl["name"]}']
    for o in pt.get("others") or []:
        for f in fams:
            if re.search(o["model"], f) and f not in out:
                out[f] = {t: [o["ratio"], o["plan"]] for t in pt.get("tiers") or {}}
    return out


def subscriptions(data):
    cfg = json.load(open(os.path.join(SRC, "plans.json"), encoding="utf-8"))
    prices = data.get("prices") or {}
    blend = lambda n: (3 * prices[n][0] + prices[n][1]) / 4
    base = resolve(prices, cfg["base"]["model"], cfg["base"]["fallback"], data, cfg["base"].get("creator"), cfg["base"].get("rank"))
    if not base:
        return "", ""
    cost = lambda n: cfg["base"]["response_usd"] * blend(n) / blend(base)
    short = lambda n: re.sub(r"^Claude ", "", n)
    rows, marks, tables = [], set(), []
    for pv in cfg["providers"]:
        dot = (f'<img class="pl-lg" src="{BASE}logos/{pv["logo"]}" width="22" height="22" alt="">' if pv.get("logo")
               else f'<i style="background:{pv["color"]}"></i>')
        rows.append(f'<tr class="pl-h"><th>{dot}{pv["name"]}</th><th>{T("$/мес")}</th><th>{T("API-эквивалент/мес")}</th><th>{T("× цены")}</th></tr>')
        for pl in pv["plans"]:
            usd, star = pv["budget"] * pl["x"], "**" if pl.get("rough") else "*" if pl.get("unofficial") else ""
            marks.add(star)
            note = f' <small>({T(pl["note"])})</small>' if pl.get("note") else ""
            rows.append(f'<tr><td><b>{pv["name"]} {pl["name"]}</b>{note}</td><td class="pl-n">${pl["price"]}</td>'
                        f'<td>≈ ${sp(rnd(usd))}{star}</td><td><span class="pl-x" style="--c:{pv["color"]}">{round(usd / pl["price"])}×</span></td></tr>')
        # per-model table
        head = "".join(f'<th>{pl.get("short", pl["name"])}<br>${pl["price"]}</th>' for pl in pv["plans"])
        body = [f'<tr class="pl-lim"><td><b>{T(pv["limit_label"])}</b><small>{T(pv["limit_note"])}</small></td>'
                + "".join(f'<td>{T(pl["limit"])}</td>' for pl in pv["plans"]) + "</tr>"]
        resp, used = {}, {}
        for m in pv["models"]:
            if "combo" in m:
                f_, o_ = (used.get(x) for x in m["combo"])  # names the rows above actually used
                if not (f_ and o_):
                    continue
                cap = next((x.get("cap", 1) for x in pv["models"] if x.get("model") == m["combo"][0]), 1)
                title, cells = T(m["title"]), []
                for i, pl in enumerate(pv["plans"]):
                    if i < m.get("from", 0):
                        cells.append('<td class="pl-no">—</td>')
                    else:
                        v = resp[f_][i] + (1 - cap) * resp[o_][i]
                        cells.append(f'<td><b>≈ {sp(rnd(v))}</b></td>')
            else:
                name = resolve(prices, m["model"], m.get("fallback"), data, pv.get("creator"), m.get("rank"), set(used.values()))
                if not name:
                    continue
                used[m["model"]] = name
                title, cells, n = short(name), [], len(pv["plans"])
                resp[name] = [pv["budget"] * pl["x"] * m.get("share", 1) / cost(name) for pl in pv["plans"]]
                free = m.get("free_from")
                for i, pl in enumerate(pv["plans"]):
                    if free is not None and i == free:
                        cells.append(f'<td colspan="{n - i}" class="pl-free">{T(m["free_text"])}</td>')
                        break
                    if i < m.get("from", 0):
                        lines = m.get("before") or ["нет"]
                        cells.append('<td class="pl-no">' + T(lines[0]) + "".join(f"<small>{T(x)}</small>" for x in lines[1:]) + "</td>")
                        continue
                    v, sub = resp[name][i], T(m.get("sub", ""))
                    if m.get("tasks"):
                        sub = f"≈ {sp(rnd(pv['base_tasks'] * pl['x'] * cfg['base']['response_usd'] / cost(name)))} {T("задач")}"
                    if m.get("sub_first") and i == m.get("from", 0):
                        ref = resp.get(base)
                        sub = T(m["sub_first"]).replace("{ratio}", f"{v / ref[i]:.0f}") if ref else ""
                    cells.append(f'<td><b>≈ {sp(rnd(v))}</b>' + (f"<small>{sub}</small>" if sub else "") + "</td>")
            body.append(f'<tr><td><b>{title}</b><small>{T(m["role"])}</small></td>{"".join(cells)}</tr>')
        tables.append(f'<div class="pl-wrap"><table class="pl pl-m"><thead><tr><th class="pl-p">{dot}{pv["name"]}</th>{head}</tr></thead>'
                      f'<tbody>{"".join(body)}</tbody></table></div>')
    summary = f'<div class="pl-wrap"><table class="pl pl-sum"><tbody>{"".join(rows)}</tbody></table></div>'
    foot = []
    if "*" in marks:
        foot.append(T("* Множители Pro неофициальные."))
    if "**" in marks:
        foot.append(T("** Для Go данных почти нет, это грубая оценка."))
    names = [T("Сколько дают")] + [f'{pv["name"]} {T("по моделям")}' for pv in cfg["providers"]]
    caps = [T("API-эквивалент — сколько стоила бы та же работа по ценам API.") + " " + " ".join(foot)] + [
        T("Ответов агента в месяц: один ответ — один ход агента в Claude Code или Codex, в обычном чате сообщений получится больше. "
          "Числа пересчитываются каждый день по текущим ценам моделей.")] * len(tables)
    panels = [summary] + tables
    caps[0] += " " + T("Оценки по замерам пользователей на {when}: компании не публикуют лимиты в долларах.").replace("{when}", T(cfg["as_of"]))
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
        tabs.append(("value", T("Цена и выгода"), [], VALUE_NOTE))
    order = ["score", "field", "value", "know"]
    tabs.sort(key=lambda t: order.index(t[0]))
    if len(tabs) < 2:
        return ""
    colors = html.escape(json.dumps(COLORS, separators=(",", ":")), quote=True)
    out = [f'<div class="rt" data-colors="{colors}"><div class="rt-tabs">']
    for n, (i, t, subs, note) in enumerate(tabs):
        out.append(f'<button type="button" data-rt="{i}" data-note="{html.escape(T(note))}"{" class=on" if n == 0 else ""}>{T(t)}</button>')
    dl = ('<svg class="dli" viewBox="0 0 24 24" width="15" height="15" aria-hidden="true">'
          '<path fill="currentColor" d="M12 3a1 1 0 0 1 1 1v8.59l2.3-2.3a1 1 0 1 1 1.4 1.42l-4 4a1 1 0 0 1-1.4 0l-4-4a1 1 0 1 1 1.4-1.42l2.3 2.3V4a1 1 0 0 1 1-1z"/>'
          '<path fill="currentColor" d="M4 15a1 1 0 0 1 1 1v3h14v-3a1 1 0 1 1 2 0v4a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1z"/></svg>')
    out.append(f'<button type="button" class="rt-dl" title="{T("Скачать картинку со ссылкой на источник")}">{dl}{T("Скачать картинку")}</button></div>')
    for i, t, subs, note in tabs:
        if len(subs) > 1:
            out.append(f'<div class="rt-subs" data-for="{i}" hidden>' + "".join(
                f'<button type="button" data-m="{k}"{" class=on" if n == 0 else ""}>{T(lbl)}</button>' for n, (k, lbl) in enumerate(subs)) + "</div>")
    out.append(f'<p class="rt-note">{html.escape(T(tabs[0][3]))}</p></div>')
    return "".join(out)


def h3_sub(t, cap):
    return f'<h3>{t}</h3><p class="cap">{cap}</p>'


UTM = "utm_source=ey-academy"
# App stores and our own pages keep their links clean.
NO_UTM = ("eyacademyeurasia.com", "eyacademy.github.io", "play.google.com", "apps.apple.com")


def tag_links(body):
    def one(m):
        url = m.group(1)
        if "utm_source=" in url or any(d in url for d in NO_UTM):
            return m.group(0)
        head, _, frag = url.partition("#")
        head += ("&" if "?" in head else "?") + UTM
        return f'href="{head}' + (f"#{frag}" if frag else "") + '"'
    return re.sub(r'href="(https?://[^"]+)"', one, body)


UI = {"locale": "ru-RU", "sec": " с", "min": " мин", "hour": " ч", "k": " тыс.", "M": " млн", "B": " млрд",
      "level": "уровень ", "score": "Интеллект", "cost": "Цена задачи", "cost_total": "Общая стоимость",
      "time": "Время на задачу", "tokens": "Токены на задачу", "tokens_total": "Всего токенов", "axisY": "↑ Интеллект",
      "speed": "Скорость вывода", "ttft": "Задержка", "tps": " ток/с", "subCost": "Цена задачи по подписке",
      "plan": "Тариф", "apiPrice": "нет данных о подписке, по цене API", "notInPlan": "не входит в тариф, по цене API", "nearFree": "≈ 0",
      "pick": "Выберите модели в списке справа.", "noData": "Не удалось загрузить данные. Обновите страницу.",
      "capScore": "Топ-{n} моделей, баллы из 100", "capOmni": "Итоговый балл от −100 до 100",
      "capAcc": "Доля верных ответов", "capHall": "Доля выдуманных ответов, меньше — лучше", "capField": "Баллы из 100",
      "noteOmni": "За верный ответ балл начисляется, за выдуманный — вычитается, за ответ «не знаю» — ноль. Значение ниже нуля означает, что модель чаще выдумывает ответ, чем отвечает верно.",
      "noteAcc": "Сколько вопросов на знания модель ответила верно. Больше — лучше.",
      "noteHall": "Как часто модель выдумывает ответ вместо ответа «не знаю». Меньше — лучше.",
      "bestCost": "Самые выгодные: ", "bestTime": "Самые быстрые для своего уровня: ",
      "bestHint": ". Наведите курсор на точку, чтобы увидеть цену и уровень размышлений.",
      "of": " из ", "showAll": "Показать все ", "collapse": "Свернуть", "preparing": "Подготовка…",
      "nothing": "Ничего не найдено", "ratingTitle": "Рейтинг моделей", "valueTitle": "Какая модель выгоднее",
      "credit1": "Источник: Artificial Analysis · artificialanalysis.ai",
      "credit2": "Гид по ИИ-инструментам Академии бизнеса EY · eyacademyeurasia.com/ai-guide"}

PAGE = {"ru": ("Гид по ИИ-инструментам · Академия бизнеса EY", "https://eyacademyeurasia.com/ai-guide"),
        "en": ("Guide to AI tools · EY Academy of Business", "https://en.eyacademyeurasia.com/ai-guide")}


data = load_data()
# Knowledge reliability comes from the API with a Pro key; until then from src/omniscience.json.
data["bench"] = [m for m in data.get("bench") or [] if not m.get("manual")]
data.pop("knowledge_note", None)
if sum(1 for m in data["bench"] if m.get("omni") is not None) < 5:
    manual = json.load(open(os.path.join(SRC, "omniscience.json"), encoding="utf-8"))
    data["bench"].extend(dict(m, manual=True) for m in manual["models"])
    d0 = datetime.fromisoformat(manual["as_of"])
    data["knowledge_as_of"] = manual["as_of"]
data["logos"] = LOGOS
data["subs"] = sub_ratios(data)
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
json.dump(data, open(os.path.join(OUT, "data", "aa-index.json"), "w", encoding="utf-8"), ensure_ascii=False)
def render(lang):
    """Build one language: the guide page, the Tilda copy and a standalone page."""
    global LANG, TR, MISS
    LANG, MISS = lang, []
    TR = json.load(open(os.path.join(SRC, "en.json"), encoding="utf-8")) if lang != "ru" else {}
    body = runpy.run_path(os.path.join(SRC, "content.py"),
                          init_globals={"MODELS": data.get("by_creator", {}), "MEDIA": data.get("media", {}),
                                        "EXTRA": data.get("extra", {}), "BASE": BASE, "LANG": LANG, "T": T})["BODY"]
    count, bars, legend, date, grid = chart(data)
    sub_tabs, sub_panels = subscriptions(data)
    cmp_html = compare(data)
    body = (body.replace("{RATING_TABS}", rating_tabs(data, bool(cmp_html))).replace("{SUBS_TABS}", sub_tabs)
            .replace("{SUBS_PANELS}", sub_panels).replace("{COMPARE}", cmp_html).replace("{CHART_N}", str(count))
            .replace("{CHART_BARS}", bars).replace("{CHART_GRID}", grid).replace("{CHART_LEGEND}", legend).replace("{CHART_DATE}", date))

    ui = {k: T(v) for k, v in UI.items()}
    ui["locale"] = "ru-RU" if lang == "ru" else "en-US"
    if data.get("knowledge_as_of"):
        d0 = datetime.fromisoformat(data["knowledge_as_of"])
        ui["knowledgeNote"] = T("Данные на {date}").replace("{date}", human_date(d0))
    attrs = f' lang="{lang}" data-lang="{lang}"'
    if lang != "ru":
        attrs += ' data-i18n="' + html.escape(json.dumps(ui, ensure_ascii=False), quote=True) + '"'
    body = body.replace('<div id="eyai" ', f'<div id="eyai"{attrs} ', 1)

    body = tag_links(body)
    version = hashlib.sha1((css + body).encode("utf-8")).hexdigest()[:12]
    body = body.replace("{VERSION}", version, 1)
    style = f'<style id="eyai-style">\n{css}</style>\n'
    script = f'<script src="{BASE}script.js" defer></script>\n'
    title, canonical = PAGE[lang]

    out = OUT if lang == "ru" else os.path.join(OUT, lang)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "guide.html"), "w", encoding="utf-8").write(style + body)
    # In Tilda the block stays hidden until script.js has swapped in the current version, so the old copy never flashes.
    open(os.path.join(out, "tilda.html"), "w", encoding="utf-8").write(
        style + body.replace('<div id="eyai" ', '<div id="eyai" class="eyai-wait" ', 1) + "\n" + script)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(
        f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{html.escape(title)}</title>'
        f'<meta name="robots" content="noindex"><link rel="canonical" href="{canonical}">'
        '<style>body{margin:0;background:#f6f6fa}#eyai{padding-top:0!important}</style></head><body>'
        + style + body + script + "</body></html>")
    if MISS:
        print(f"  {lang}: {len(MISS)} strings without a translation")
        json.dump(MISS, open(os.path.join(OUT, f"missing-{lang}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  {lang}: version {version} | {date}")
    return version


css = open(os.path.join(SRC, "style.css"), encoding="utf-8").read()
os.makedirs(OUT, exist_ok=True)
for code in ("ru", "en"):
    render(code)
shutil.copy(os.path.join(SRC, "script.js"), os.path.join(OUT, "script.js"))
shutil.copytree(os.path.join(SRC, "logos"), os.path.join(OUT, "logos"), dirs_exist_ok=True)
