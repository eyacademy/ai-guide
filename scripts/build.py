import hashlib, html, json, os, runpy, shutil
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


def color(creator):
    k = creator.lower()
    return next((c for n, c in COLORS.items() if n in k), "#9a9aa6")


def load_data():
    path = os.path.join(OUT, "data", "aa-index.json")
    if not os.path.exists(path):
        path = os.path.join(SRC, "aa-snapshot.json")
    return json.load(open(path, encoding="utf-8"))


def chart(data):
    models = data["models"][:20]
    top = max(m["score"] for m in models)
    bars, legend, seen = [], [], set()
    for i, m in enumerate(models, 1):
        c, name, creator = color(m["creator"]), html.escape(m["name"]), html.escape(m["creator"])
        w = max(8, round(m["score"] / top * 100))
        bars.append(f'<li class="bar"><span class="i">{i}</span><span class="n">{name}<small>{creator}</small></span>'
                    f'<span class="t"><span class="f{" lt" if c in LIGHT else ""}" style="--c:{c};width:{w}%">{m["score"]}</span></span></li>')
        if m["creator"] not in seen:
            seen.add(m["creator"])
            legend.append(f'<span><i style="background:{c}"></i>{creator}</span>')
    d = datetime.fromisoformat(data["updated"].replace("Z", "+00:00"))
    return "".join(bars), "".join(legend), f"Обновлено {d.day} {MONTHS[d.month - 1]} {d.year} · обновляется ежедневно"


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
            f'<h3>Какая модель выгоднее</h3><p class="cap">Наведите на точку или столбец, чтобы увидеть подробности. '
            f'Справа можно выбрать модели и уровни размышлений. Цена задачи — средняя стоимость одной задачи из рейтинга по ценам API.</p>'
            f'<div class="cmp-box"><div class="cmp-tabs">{tab_html}</div>'
            f'<div class="cmp-subs" hidden>{sub_html}</div><p class="cmp-note">{html.escape(tabs[0][3])}</p>'
            f'<div class="cmp-wrap"><div class="cmp-main"><div class="cmp-plot"><p class="cmp-load">Загружаем данные…</p></div><div class="cmp-best"></div></div>'
            f'<aside class="cmp-side"><div class="cmp-side-h"><b>Модели</b><span class="cmp-count"></span></div>'
            f'<input class="cmp-q" type="search" placeholder="Найти модель" aria-label="Найти модель">'
            f'<div class="cmp-quick"><button type="button" data-q="top">Топ-12</button><button type="button" data-q="none">Снять все</button></div>'
            f'<label class="cmp-eff"><input type="checkbox" checked> Все уровни размышлений</label>'
            f'<div class="cmp-list"></div></aside></div></div></div>')


data = load_data()
body = runpy.run_path(os.path.join(SRC, "content.py"), init_globals={"MODELS": data.get("by_creator", {})})["BODY"]
bars, legend, date = chart(data)
body = body.replace("{COMPARE}", compare(data)).replace("{CHART_BARS}", bars).replace("{CHART_LEGEND}", legend).replace("{CHART_DATE}", date)
css = open(os.path.join(SRC, "style.css"), encoding="utf-8").read()
version = hashlib.sha1((css + body).encode("utf-8")).hexdigest()[:12]
body = body.replace("{VERSION}", version, 1)
style = f'<style id="eyai-style">\n{css}</style>\n'
script = f'<script src="{BASE}script.js" defer></script>\n'

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "guide.html"), "w", encoding="utf-8").write(style + body)
open(os.path.join(OUT, "tilda.html"), "w", encoding="utf-8").write(style + body + "\n" + script)
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
    '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1">'
    '<title>Гид по ИИ-инструментам · Академия бизнеса EY</title>'
    '<meta name="robots" content="noindex"><link rel="canonical" href="https://eyacademyeurasia.com/ai-guide">'
    '<style>body{margin:0;background:#f6f6fa}#eyai{padding-top:0!important}</style></head><body>'
    + style + body + script + "</body></html>")
shutil.copy(os.path.join(SRC, "script.js"), os.path.join(OUT, "script.js"))
print("version", version, "|", date)
