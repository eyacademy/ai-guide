import html, re
from urllib.parse import urlparse

def dom(u):
    d = urlparse(u).netloc.replace("www.", "")
    p = urlparse(u).path.strip("/")
    return d + ("/" + p if p and len(d + p) < 26 and p.count("/") == 0 else "")

import json, os
BASE = globals().get("BASE") or ""
T = globals().get("T") or (lambda x: x)
LOGO = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cardlogos.json"), encoding="utf-8"))


def logo(name, cls="cl", size=20):
    f = LOGO.get(name)
    return f'<img class="{cls}" src="{BASE}logos/{f}" width="{size}" height="{size}" alt="" loading="lazy">' if f else ""


def card(name, desc, url, tag=None, gray=False, small=None):
    t = f'<span class="tag{" g" if gray else ""}">{T(tag)}</span>' if tag else ""
    return (f'<a class="card" href="{url}" target="_blank" rel="noopener"><b>{logo(name)}{T(name)}{t}</b>'
            f'<p>{T(desc)}</p><small>{small or dom(url)}</small></a>')

def grid(items):
    return '<div class="grid">\n' + "\n".join(card(*i) if isinstance(i, tuple) else i for i in items) + "\n</div>"

# Link rows get the logo of the product they lead to; otherwise the vendor's.
ROW_LOGO = [("Notebook", "Gemini Notebook"), ("Labs", "Google Labs"), ("AI Studio", "Google AI Studio"), ("Claude Code", "Claude Code"),
            ("Codex", "Codex"), ("Copilot Chat", "Copilot"), ("Личный Copilot", "Copilot"), ("Higgsfield", "Higgsfield")]


def links(items, brand=None):
    def row(t):
        key = next((k for w, k in ROW_LOGO if w in t), brand)
        return logo(key, "ll", 16) if key else ""
    return '<ul class="links">' + "".join(
        f'<li><a href="{u}" target="_blank" rel="noopener"><em>{row(t)}{T(t)}</em> <span>{s}</span></a></li>' for t, u, s in items) + "</ul>"

MODELS = globals().get("MODELS") or {}


def models(creator, fallback, n=4):
    return (MODELS.get(creator) or fallback)[:n]


def model(creator, fallback):
    return models(creator, [fallback], 1)[0]


# Pictures, video and sound: names come from the Artificial Analysis arenas, newest version wins.
MEDIA = globals().get("MEDIA") or {}
EXTRA = globals().get("EXTRA") or {}


# Speed and resolution variants of the same model: "Veo 3.1 Fast", "Kling 3.0 1080p".
VARIANT = re.compile(r"\s+(fast|lite|mini|turbo|flex|klein|quality|preview|beta|\d{3,4}p)\b.*$", re.I)


def _ver(name):
    return tuple(float(x) for x in re.findall(r"\d+(?:\.\d+)?", name)) or (0,)


def media(kind, pattern, fallback):
    """Newest model of a line: latest version, plainest name, best place in the arena."""
    hits = [n for n in MEDIA.get(kind) or [] if re.search(pattern, n, re.I)]
    if hits:
        top = max(_ver(n) for n in hits)
        same = [n for n in hits if _ver(n) == top]
        name = min(same, key=lambda n: (len(n.split()), hits.index(n)))
        at = re.search(pattern, name, re.I)          # drop a hosting prefix: "Dreamina Seedance 2.5"
        name = VARIANT.sub("", name[at.start():] if at else name)
    else:
        name = fallback
    if fallback and fallback in LOGO:
        LOGO.setdefault(name, LOGO[fallback])
    return name


def retitle(old, new):
    """A card keeps its logo when a new model version changes its title."""
    if old in LOGO:
        LOGO.setdefault(new, LOGO[old])
    return new


def place(kind, pattern, what, default=""):
    """«первое место в рейтинге видео …», пусто за пределами топ-5."""
    for i, n in enumerate(MEDIA.get(kind) or [], 1):
        if re.search(pattern, n, re.I):
            return f"первое место в рейтинге {what} Artificial Analysis" if i == 1 else (
                f"{i}-е место в рейтинге {what} Artificial Analysis" if i <= 5 else "")
    return default


VENDORS = []


def vendor(by, name, text, pills, lk):
    # Each big assistant becomes a tab: description and models on the left, links on the right.
    p = "".join(f'<span class="pill{" top" if i == 0 else ""}">{T(x)}</span>' for i, x in enumerate(pills))
    VENDORS.append((name, f'<div class="vd"><div><span class="by">{T(by)}</span><p>{T(text)}</p><div class="pills">{p}</div></div>{links(lk, name)}</div>'))
    return ""


def vendor_tabs(extra):
    tabs = VENDORS + extra
    btns = "".join(f'<button type="button"{" class=on" if i == 0 else ""}>{logo(n, "tl", 16)}{T(n)}</button>' for i, (n, _) in enumerate(tabs))
    panels = "".join(f'<div class="pl-panel"{" hidden" if i else ""}>{b}</div>' for i, (_, b) in enumerate(tabs))
    return f'<div class="pl-box"><div class="pl-tabs">{btns}</div>{panels}</div>'

def sec(id_, num, title, lead, body):
    l = f'<p class="sec-lead">{T(lead)}</p>' if lead else ""
    return f'<section id="eyai-{id_}">\n<div class="sec-h"><span class="num">{num}</span><h2>{T(title)}</h2></div>\n{l}\n{body}\n</section>\n'

SHORT = {"Агенты в рабочих чатах команды": "Командные агенты", "Агенты на вашем компьютере": "Локальные агенты",
         "Агенты в облаке, 24/7": "Облачные агенты 24/7", "Агенты на сервере компании": "Серверные агенты",
         "MCP: подключение ИИ к вашим системам": "MCP-интеграции", "Автоматизация без программирования": "Автоматизация процессов",
         "Аватары и перевод видео": "Аватары и перевод", "Сайты и приложения без программирования": "Сайты и приложения",
         "Документы, презентации, инфографика": "Документы и презентации",
         "Изображения, видео и аудио": "Изображения, видео, аудио", "Проверка на плагиат": "Антиплагиат",
         "Свой стек на сервере": "Своя инфраструктура", "Запуск на своём компьютере": "Локальный запуск", "Дообучение моделей": "Дообучение"}


def short_label(heading):
    """Headings arrive already translated, so match the short label in the same language."""
    for ru, short in SHORT.items():
        if T(ru) == heading:
            return T(short)
    return heading


def tabify(body):
    """Turn a run of h3 + caption + cards into one framed block with a tab per subsection."""
    tabs = []
    for part in [x for x in re.split(r"(?=<h3>)", body) if x.strip()]:
        m = re.match(r'<h3>(.*?)</h3>(?:<p class="cap">(.*?)</p>)?', part, re.S)
        tabs.append((m.group(1), m.group(2), part[m.end():]))
    btns = "".join(f'<button type="button"{" class=on" if i == 0 else ""}>{short_label(t)}</button>' for i, (t, _, _) in enumerate(tabs))
    panels = "".join(f'<div class="pl-panel"{" hidden" if i else ""}>' + (f'<p class="pcap">{c}</p>' if c else "") + b + "</div>"
                     for i, (_, c, b) in enumerate(tabs))
    return f'<div class="pl-box"><div class="pl-tabs">{btns}</div>{panels}</div>'


def h3(t, cap=None):
    return f"<h3>{T(t)}</h3>" + (f'<p class="cap">{T(cap)}</p>' if cap else "")

NAV = [("rating", "Рейтинг"), ("llm", "Чат-боты"), ("agents", "ИИ-агенты"),
       ("media", "Медиаконтент"), ("tools", "Прикладные сервисы"), ("company", "Внедрение ИИ"), ("detect", "Детекторы")]

out = ['<div id="eyai" data-v="{VERSION}">', '<div class="toc"><div class="w">' +
       "".join(f'<a href="#eyai-{i}"><span>{n}</span>{T(t)}</a>' for n, (i, t) in enumerate(NAV, 1))
       + f'<a class="toc-cta" href="{T("https://eyacademyeurasia.com/ai/chatgpt")}?utm_source=ai-guide" target="_blank" rel="noopener">{T("Тренинг по ИИ")} &rarr;</a>'
       + "</div></div>",
       '<div class="w">']

# 2. rating
rating = ('<div class="chart">{RATING_TABS}<div class="rt-main"><div class="chart-top"><span class="rt-cap">'
          + T("Топ-{n} моделей, баллы из 100").replace("{n}", "{CHART_N}")
          + '</span><span class="rt-date">{CHART_DATE}</span></div>'
          '<div class="plot"><div class="rt-grid">{CHART_GRID}</div><ol class="bars cut">{CHART_BARS}</ol></div>'
          '<button type="button" class="rt-more">' + T("Показать все") + '</button>'
          '<div class="legend">{CHART_LEGEND}</div></div><div class="rt-value" hidden>{COMPARE}</div></div>'
          '<p class="src">' + T("Источник:") + ' <a href="https://artificialanalysis.ai" target="_blank" rel="noopener">Artificial Analysis</a></p>')
out.append(sec("rating", "01", "Рейтинг моделей",
               "Artificial Analysis Intelligence Index. Независимая лаборатория оценивает модели по 10 тестам: агентные задачи, программирование, знания, научное мышление. Чем выше балл, тем лучше модель справляется со сложной работой.",
               rating))

# 3. chat
v = ""
v += vendor("OpenAI", "ChatGPT",
            "Универсальный помощник. Chat подходит для вопросов, текстов и файлов, Work берёт длинную задачу и возвращает готовые документы, таблицы и презентации. В приложении для компьютера есть режим Codex для работы с кодом. Самые сильные модели открыты в Work, Codex и платных тарифах.",
            models("OpenAI", ["GPT-6 Astra", "GPT-6.1 Sol", "GPT-5.6 Terra", "GPT-6 Luna"]),
            [("Чат", "https://chatgpt.com", "chatgpt.com"),
             ("Приложение для компьютера: Chat, Work, Codex", "https://openai.com/chatgpt/download/", "openai.com"),
             ("Codex в браузере", "https://chatgpt.com/codex", "chatgpt.com/codex"),
             ("API", "https://platform.openai.com", "platform.openai.com")])
v += vendor("Anthropic", "Claude",
            "Точно понимает формулировку задачи и пишет естественным языком, поэтому текст требует меньше правок. Сильные стороны — программирование, длинные документы и длительная самостоятельная работа.",
            models("Anthropic", ["Claude Opus 5.5", "Claude Sonnet 5.5", "Claude Fable 5.1", "Claude Haiku 4.5"]),
            [("Чат", "https://claude.ai", "claude.ai"),
             ("Приложение для компьютера: Cowork, Claude Code", "https://claude.com/download", "claude.com/download"),
             ("Claude в Excel, Word и PowerPoint", "https://claude.com/claude-for-microsoft-365", "claude.com"),
             ("API", "https://platform.claude.com", "platform.claude.com")])
v += vendor("Google", "Gemini",
            "Выбор для компаний на Google Workspace: встроен в Gmail, Docs, Sheets и Meet. Большое контекстное окно, удобен для объёмных документов.",
            models("Google", ["Gemini 4 Argon", "Gemini 3.8 Flash", "Gemini 3.1 Pro"]),
            [("Чат", "https://gemini.google.com/app", "gemini.google.com"),
             ("Gemini Notebook (бывший NotebookLM)", "https://notebook.google.com", "notebook.google.com"),
             ("Gemini в Gmail, Docs и Sheets", "https://workspace.google.com/solutions/ai/", "workspace.google.com"),
             ("Google Labs: экспериментальные ИИ-инструменты", "https://labs.google", "labs.google"),
             ("API и AI Studio", "https://aistudio.google.com", "aistudio.google.com")])
v += vendor("Microsoft", "Copilot",
            "Выбор для компаний на Microsoft 365. Copilot Chat бесплатно входит в подписку M365: чат, файлы, поиск в интернете. Платный Microsoft 365 Copilot работает внутри Word, Excel, PowerPoint, Outlook и Teams и через Work IQ видит вашу почту, встречи и документы.",
            ["Microsoft 365 Copilot", "Copilot Chat"],
            [("Microsoft 365 Copilot", "https://www.microsoft.com/en-us/microsoft-365/copilot", "microsoft.com"),
             ("Copilot Chat для организаций", "https://www.microsoft.com/en-us/copilot/features/chat", "microsoft.com"),
             ("Личный Copilot", "https://copilot.microsoft.com", "copilot.microsoft.com")])
llm = v
# Subscriptions: kinds, value, per-model limits and privacy in one tabbed block.
# One table: the two kinds of plans side by side, no repeated cards.
PLAN_ROWS = [("ChatGPT", "Free, Go $8, Plus $20, Pro от $100", "Да, отключается", "Business $20–25"),
             ("Claude", "Free, Pro $20, Max $100, Ultra $200", "По согласию пользователя; хранение до 5 лет", "Team $20–25"),
             ("Gemini", "Free, AI Plus $5, AI Pro $20, Ultra от $100", "Да, отключается", "Google Workspace от $7, Gemini включён"),
             ("Copilot", "Free, Microsoft 365 Personal $10, Premium $20", "Нет (в новом приложении)",
              "Copilot Chat бесплатно с M365, Microsoft 365 Copilot $21–30 + лицензия M365")]
kinds = ('<p class="pcap">' + T("Личная подписка может обучать модели на вашей переписке, пока эта настройка не отключена, и не даёт компании контроля над данными. "
         "Бизнес-подписка не обучает модели на ваших данных, предусматривает администратора, вход через корпоративный аккаунт и единый счёт; подключается от 2 пользователей.") + '</p>'
         f'<div class="pl-wrap"><table class="pl pl-k"><tbody><tr class="pl-h"><th>{T("Сервис")}</th><th>{T("Личные тарифы")}</th>'
         f'<th>{T("Обучение на данных пользователей")}</th><th>{T("Бизнес-тарифы")}</th></tr>'
         + "".join(f'<tr><td><b>{logo(n, "pl-lg", 16)}{n}</b></td><td>{T(a)}</td><td>{T(t)}</td><td>{T(b)}</td></tr>' for n, a, t, b in PLAN_ROWS)
         + f'<tr><td><b>API</b></td><td>{T("Оплата по объёму запросов")}</td>'
         f'<td>{T("Нет по умолчанию (кроме бесплатного уровня Gemini API)")}</td><td>—</td></tr>'
         f'</tbody></table></div><p class="src">{T("Цены за пользователя в месяц в долларах США. У бизнес-тарифов меньшая цена при оплате за год.")}</p>')
privacy = '<div class="grid">' + "".join(f'<div class="card"><b>{logo(a)}{a}</b><p>{T(t)}</p></div>' for a, t in [
    ("ChatGPT", "Settings → Data controls → выключить «Improve the model for everyone». Временные чаты не используются для обучения."),
    ("Claude", "Settings → Privacy → выключить «Help improve Claude». Чаты в режиме инкогнито не используются для обучения."),
    ("Gemini", "Activity → выключить «Keep Activity». Временные чаты не используются для обучения."),
]) + "</div>"
llm += h3("Тарифы и лимиты", "Типы тарифов, их стоимость и объём использования. Для работы с документами компании рекомендуем бизнес-тариф: "
          "он сопоставим по цене с личным, а данные остаются под контролем компании.")
llm += ('<div class="pl-box"><div class="pl-tabs"><button type="button" class="on">' + T("Типы тарифов") + '</button>{SUBS_TABS}'
        '<button type="button">' + T("Отключение обучения") + '</button></div>'
        f'<div class="pl-panel">{kinds}</div>' + "{SUBS_PANELS}" + f'<div class="pl-panel" hidden>{privacy}</div></div>')
others = grid([
    ("DeepSeek", f"Сильная китайская модель {model('DeepSeek', 'DeepSeek V4.1 Flash')}. Бесплатный чат, веса можно скачать и запустить у себя.", "https://chat.deepseek.com", "открытые веса"),
    ("Perplexity", "Поиск в интернете с источниками под каждым ответом.", "https://www.perplexity.ai"),
    ("Grok", f"Модель {model('SpaceXAI', 'Grok 4.7')} от SpaceXAI. Встроен в соцсеть X.", "https://grok.com"),
    ("Genspark", "Чат, презентации, таблицы и исследования в одном месте.", "https://www.genspark.ai"),
    ("Meta AI", f"Ассистент на модели {model('Meta', 'Muse Spark 1.3')}. В Казахстане удобнее всего через WhatsApp.", "https://www.meta.ai"),
    ("Mistral Vibe", "Европейский чат-бот, до мая 2026 назывался Le Chat.", "https://chat.mistral.ai", "открытые веса"),
    ("Qwen", f"Модели Alibaba. Флагман {model('Alibaba', 'Qwen3.8 Max')}.", "https://chat.qwen.ai", "открытые веса"),
    ("Z.ai (GLM)", f"{model('Z AI', 'GLM-5.3')}, одна из сильнейших открытых моделей.", "https://chat.z.ai", "открытые веса"),
    ("Kimi", f"{model('Kimi', 'Kimi K3')} от Moonshot AI. Запускает группу агентов для крупных задач.", "https://www.kimi.com", "открытые веса"),
    ("t3.chat", "Одна подписка на модели разных компаний в одном окне.", "https://t3.chat"),
])
llm = vendor_tabs([("Другие чат-боты", others)]) + llm
out.append(sec("llm", "02", "Чат-боты и модели",
               "Для большинства задач достаточно одного из четырёх сервисов ниже. У всех есть бесплатный тариф, но самые сильные модели доступны только в платных.", llm))

# 4. agents
ag = h3("Агенты в рабочих чатах команды", "Агент работает там же, где и команда, и выполняет задачи по запросу, расписанию или событию.")
ag += grid([
    ("ChatGPT Workspace Agents", "Общие агенты команды: отчёты, ответы, подготовка документов. Работают в ChatGPT и Slack, по расписанию.", "https://chatgpt.com", "Business", True, "chatgpt.com"),
    ("Claude Tag", "Claude как участник Slack-канала: любой сотрудник упоминает @Claude и поручает задачу. Помнит контекст канала и напоминает о важных вопросах.", "https://claude.com/product/tag", "Team", True),
    ("Copilot Agent Builder", "Простой агент внутри Microsoft 365: отвечает на вопросы и выполняет задачи по расписанию.", "https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder", None, False, "learn.microsoft.com"),
    ("Copilot Studio", "Агенты, которые реагируют на события и выполняют действия во внешних системах.", "https://copilotstudio.microsoft.com"),
])
ag += h3("Агенты на вашем компьютере", "Работают с вашими файлами, программами и браузером. Вы видите, что делает агент, и подтверждаете важные шаги.")
ag += grid([
    ("ChatGPT Work", "Режим ChatGPT для длинных задач: исследует, собирает документы, таблицы и презентации.", "https://chatgpt.com"),
    ("Claude Cowork", "Агент для офисной работы: файлы, программы, браузер. Готовит docx, xlsx, pptx, выполняет задачи по расписанию.", "https://claude.com/product/cowork"),
    ("Manus", "Универсальный агент: исследования, отчёты, сайты по одной задаче.", "https://manus.im"),
])
ag += h3("Агенты в облаке, 24/7", "Новый класс агентов: у каждого свой облачный компьютер с браузером. Ничего не нужно устанавливать, задачи выполняются даже при выключенном компьютере. Данные хранятся у поставщика.")
ag += grid([
    ("dots", "OpenAI, сентябрь 2026. Постоянные агенты на самой сильной модели OpenAI в ChatGPT, Slack и Teams. Работают в фоновом режиме и сами предлагают помощь.", "https://openai.com/index/introducing-dots/", "Pro", True, "openai.com"),
    ("Grok Bot", "SpaceXAI, август 2026. Команда ботов на одном облачном компьютере. Задачу можно показать, и бот запомнит порядок действий.", "https://x.ai/bot", "SuperGrok", True, "x.ai/bot"),
    ("Muse", "Meta, сентябрь 2026. Личный агент с отдельной виртуальной машиной. Агент Sentinel пропускает в интернет только одобренные действия.", "https://muse.ai", "только США", True),
    ("Gemini Spark", "Google. Агент работает круглосуточно, задачи можно ставить письмом в Gmail.", "https://gemini.google/overview/agent/spark/", "доступен не во всех странах", True, "gemini.google"),
])
ag += h3("Агенты на сервере компании", "Открытый код: устанавливаются на ваш сервер или компьютер, данные не передаются поставщику. Работают с любой моделью, в том числе локальной. Установку и безопасность обеспечивает ИТ-отдел.")
ag += grid([
    ("OpenClaw", "Самый популярный открытый агент, около 390 тыс. звёзд на GitHub. Браузер, файлы, терминал; общается через WhatsApp, Telegram, Slack и другие мессенджеры.", "https://openclaw.ai", "открытый код", False),
    ("Hermes Agent", "Nous Research. Устанавливается одной командой, сам создаёт навыки из выполненных задач и помнит контекст. 20+ каналов, включая Telegram и Teams.", "https://hermes-agent.nousresearch.com", "открытый код", False, "nousresearch.com"),
    ("NVIDIA NemoClaw", "OpenClaw в защищённой среде NVIDIA с моделями Nemotron и правилами безопасности.", "https://www.nvidia.com/en-us/ai/nemoclaw/", "открытый код", False),
])
ag += h3("Агенты для разработки")
ag += grid([
    ("Codex", "Агент OpenAI для кода: режим в приложении ChatGPT и версия в браузере.", "https://chatgpt.com/codex", None, False, "chatgpt.com/codex"),
    ("Claude Code", "Агент Anthropic: терминал, IDE, приложение для компьютера, браузер.", "https://claude.com/product/claude-code"),
    ("Cursor", "Редактор кода на базе VS Code со встроенными агентами.", "https://cursor.com"),
    ("Google Antigravity", "Среда разработки Google, построенная вокруг агентов.", "https://antigravity.google"),
    ("GitHub Copilot", "Помощник и агент в IDE, терминале и на GitHub.", "https://github.com/features/copilot"),
    ("Devin Desktop", "Бывший Windsurf. Управляет локальными и облачными агентами Devin.", "https://devin.ai/desktop"),
])
ag += h3("MCP: подключение ИИ к вашим системам")
ag += grid([
    ("Документация MCP", "Официальное описание протокола и примеры.", "https://modelcontextprotocol.io"),
    ("MCP Registry", "Официальный реестр публичных MCP-серверов.", "https://registry.modelcontextprotocol.io", None, False, "modelcontextprotocol.io"),
    ("Smithery", "Каталог MCP-серверов с установкой в несколько кликов.", "https://smithery.ai"),
    ("Glama", "Самый большой каталог MCP-серверов с поиском.", "https://glama.ai/mcp/servers"),
    ("mcp.so", "Большой открытый каталог MCP-серверов от сообщества.", "https://mcp.so"),
])
ag += '<p class="note">' + T("<b>Агенты и MCP-серверы действуют автономно.</b> Перед подключением к рабочим данным ограничьте права доступа и проверьте, кто автор сервера.") + "</p>"
ag += h3("Автоматизация без программирования", "Цепочки действий между сервисами: пришло письмо — ИИ его разобрал — задача появилась в CRM.")
ag += grid([
    ("n8n", "Гибкий конструктор с ИИ-агентами. Можно развернуть на серверах компании.", "https://n8n.io"),
    ("Zapier", "Облачная автоматизация для 9000+ приложений, свои агенты и MCP.", "https://zapier.com"),
    ("Make", "Визуальный конструктор сценариев с ветками и условиями.", "https://www.make.com/en", None, False, "make.com"),
])
out.append(sec("agents", "03", "ИИ-агенты",
               "Чат-бот отвечает на вопросы. Агент сам выполняет задачу: планирует шаги, пользуется инструментами и доводит работу до результата.", tabify(ag)))

# 5. media
m = h3("Комплексные платформы", "Платформы, где в одной подписке собраны модели для изображений, видео и аудио.")
m += grid([
    ("Higgsfield", "Казахстанская компания-единорог: фото, видео и звук в одном сервисе. Ведущие модели (Seedance, Kling, Veo, Nano Banana, Wan) и собственные инструменты: Cinema Studio, Soul ID, Speak. Популярен у маркетологов для социальных сетей.", "https://higgsfield.ai", "из Казахстана"),
    ("Adobe Firefly", "Модели Adobe, Google, OpenAI и FLUX в одной подписке, безопасно для коммерческого использования.", "https://firefly.adobe.com"),
    ("Freepik", "Фотосток и ИИ-инструменты для картинок, видео и озвучки.", "https://www.freepik.com"),
])
m += h3("Изображения")
m += grid([
    (retitle("ChatGPT Images 2.5", media("image", r"^(GPT|ChatGPT) Image", "ChatGPT Images 2.5")),
     "Генерация и точное редактирование прямо в ChatGPT. Читаемый текст на изображениях, в том числе на кириллице.", "https://chatgpt.com"),
    (retitle("Nano Banana 2 и Pro", media("image", r"^Nano Banana", "Nano Banana 2")),
     "Модель Google для изображений, работает в приложении Gemini.", "https://deepmind.google/models/gemini-image/"),
    ("Midjourney", f"Художественная генерация с сильным стилем. Версия {EXTRA.get('midjourney') or 'V8.2'}.", "https://www.midjourney.com"),
    ("Grok Imagine", "Изображения и видео от SpaceXAI" + (lambda p: f", {p}" if p else "")(place("image", r"grok|imagine", "картинок", "в топ-5 рейтинга Artificial Analysis")) + ".", "https://grok.com/imagine"),
    ("FLUX", "Модели Black Forest Labs" + (lambda n: f", актуальная {n}" if n else "")(media("image", r"^FLUX", "")) + ". Есть открытые веса и API.", "https://bfl.ai"),
])
m += h3("Видео")
m += grid([
    (retitle("Veo 3.1 и Google Flow", f"{media('video', r'^Veo', 'Veo 3.1')} и Google Flow"),
     "Видео со звуком по тексту и изображениям. Flow — студия Google для монтажа сцен.", "https://flow.google.com"),
    (retitle("Gemini Omni Flash", media("video", r"^Gemini", "Gemini Omni Flash")),
     "Создание и правка видео в диалоге: «убери человека слева», «сделай закат».", "https://deepmind.google/models/gemini-omni/"),
    (retitle("Seedance 2.5", media("video", r"Seedance", "Seedance 2.5")),
     "Модель ByteDance: ролики до 30 секунд. Доступна в Dreamina (CapCut) и Higgsfield.", "https://dreamina.capcut.com"),
    ("Kling", f"Реалистичное видео и «оживление» фото. Актуальная модель — {media('video', r'^Kling', 'Kling 3.0')}.", "https://kling.ai"),
    (retitle("Wan 3.0", media("video", r"^Wan", "Wan 3.0")),
     "Модель Alibaba" + (lambda p: f", {p}" if p else "")(place("video", r"^Wan", "видео", "первое место в рейтинге видео Artificial Analysis")) + ". Ролики до 30 секунд со звуком.", "https://wan.video"),
    ("Hailuo", f"Модель {media('video', r'^(MiniMax|Hailuo)', 'MiniMax H3')}: ролики в 2K до 15 секунд со стереозвуком.", "https://hailuoai.video"),
    ("Runway", "Профессиональный видеоредактор с ИИ.", "https://runway.com"),
    ("CapCut", "Популярный видеоредактор с ИИ-инструментами: субтитры, эффекты, монтаж.", "https://www.capcut.com"),
    ("VEED", "Видеоредактор в браузере: автосубтитры, перевод и озвучка, ИИ-аватары, шумоподавление. Удобен для роликов в социальных сетях.", "https://www.veed.io"),
])
m += h3("Аватары и перевод видео")
m += grid([
    ("HeyGen", "Цифровые аватары, дубляж и перевод видео на 175+ языков.", "https://www.heygen.com"),
    ("Synthesia", "Корпоративные обучающие видео с аватарами на 140+ языках.", "https://www.synthesia.io"),
    ("D-ID", "Говорящие аватары из фотографии и ИИ-агенты с лицом для сайта.", "https://www.d-id.com"),
])
m += h3("Аудио и музыка")
m += grid([
    ("ElevenLabs", "Озвучка, клонирование голоса, дубляж" + (lambda p: f", {p}" if p else "")(place("speech", r"eleven", "речи", "лучшая модель речи в рейтинге")) + ". Распознаёт казахскую речь.", "https://elevenlabs.io"),
    ("Suno", f"Песни и фоновая музыка по описанию. Версия {media('music', r'^Suno', 'Suno v6').replace('Suno ', '')}.", "https://suno.com"),
])
m += h3("Дизайн")
m += grid([
    ("Canva", "Шаблоны и Canva AI: посты, баннеры, презентации.", "https://www.canva.com"),
    ("Claude Design", "Слайды, одностраничники и прототипы по описанию. Экспорт в PPTX, PDF и Canva.", "https://claude.ai/design", None, False, "claude.ai/design"),
    ("Figma Make", "Кликабельный прототип интерфейса по описанию.", "https://www.figma.com/make/"),
])
out.append(sec("media", "04", "Медиаконтент: изображения, видео, аудио",
               "Многие сервисы работают на моделях сторонних разработчиков, поэтому одна и та же модель встречается в разных местах. Выбирайте по удобству и цене.", tabify(m)))

# 6. tools
t = h3("Сайты и приложения без программирования")
t += grid([
    ("Lovable", "По текстовому описанию создаёт рабочий сайт с базой данных. Публикация в один клик.", "https://lovable.dev"),
    ("Base44", "Бизнес-приложения по описанию: CRM, заявки, внутренние порталы.", "https://base44.com"),
    ("Google AI Studio Build", "Приложение по описанию с базой, авторизацией и публикацией в Google Cloud.", "https://aistudio.google.com/apps", None, False, "aistudio.google.com"),
    ("Claude Artifacts", "Интерактивные страницы и мини-приложения прямо в чате Claude.", "https://claude.ai"),
    ("v0", "Агент Vercel для веб-приложений и интерфейсов.", "https://v0.app"),
    ("Replit", "Облачная среда: агент пишет приложение и сразу публикует.", "https://replit.com"),
])
t += h3("Документы, презентации, инфографика")
t += grid([
    ("Gemini Notebook", "Бывший NotebookLM. Отвечает только по вашим источникам, делает аудио- и видеопересказ, презентации, тесты.", "https://notebook.google.com"),
    ("Gamma", "Презентации, документы и сайты по описанию. Экспорт в PowerPoint и PDF.", "https://gamma.app"),
    ("Napkin AI", "Превращает текст в схемы и инфографику.", "https://www.napkin.ai"),
    ("Julius AI", "Загрузите таблицу и задайте вопрос — сервис подготовит анализ и графики.", "https://julius.ai"),
])
t += h3("Протоколы встреч", "Сначала проверьте встроенные функции: Google Meet, Zoom и Teams уже умеют делать конспект встречи.")
t += grid([
    ("Granola", "Конспект встречи по звуку с компьютера, без бота в звонке.", "https://www.granola.ai"),
    ("Fireflies", "Бот записывает звонки и выгружает итоги в CRM.", "https://fireflies.ai"),
    ("tl;dv", "Запись и конспект встреч, хранение данных в ЕС.", "https://tldv.io"),
    ("Plaud", "Карманный диктофон с ИИ для офлайн-встреч.", "https://www.plaud.ai"),
])
out.append(sec("tools", "05", "Прикладные сервисы", None, tabify(t)))

# 7. company
c = ""
c += h3("Поставщики API")
c += grid([
    ("OpenAI", "Модели GPT. Вход через аккаунт ChatGPT.", "https://platform.openai.com"),
    ("Anthropic", "Модели Claude.", "https://platform.claude.com"),
    ("Google AI Studio", "Модели Gemini, есть бесплатный лимит.", "https://aistudio.google.com"),
    ("OpenRouter", "Один ключ для сотен моделей разных компаний.", "https://openrouter.ai"),
    ("Groq", "Очень быстрые ответы открытых моделей. Не путать с Grok от SpaceXAI: это разные компании.", "https://groq.com"),
    ("Cerebras", "Ещё одна платформа сверхбыстрых ответов, часто быстрее Groq по числу слов в секунду.", "https://www.cerebras.ai"),
    ("DeepSeek", "Одни из самых низких цен среди сильных моделей.", "https://platform.deepseek.com"),
])
c += h3("Свой стек на сервере", "Когда данные нельзя передавать за пределы компании, ИИ разворачивают во внутренней инфраструктуре. Стек собирают по слоям: "
        "интерфейс для сотрудников, база знаний по документам, шлюз с лимитами и сам движок моделей.")
c += grid([
    ("Open WebUI", "Интерфейс: привычный чат для сотрудников. Вход по логину, своя история, загрузка документов, права доступа.", "https://openwebui.com"),
    ("Qdrant", "База знаний: хранит документы в виде векторов. Промышленное решение для компании.", "https://qdrant.tech"),
    ("Chroma", "Более простая база знаний: встроена в Open WebUI по умолчанию и не требует настройки. Подходит для пилотного проекта.", "https://www.trychroma.com"),
    ("pgvector", "База знаний внутри PostgreSQL. Подходит, если PostgreSQL уже используется.", "https://github.com/pgvector/pgvector"),
    ("RAGFlow", "Готовый сервер базы знаний с интерфейсом. Подходит для сложных PDF и сканов, если в команде нет разработчиков.", "https://ragflow.io"),
    ("LiteLLM", "Шлюз: отдельный ключ каждому сотруднику, лимиты по расходам, переключение между моделями.", "https://www.litellm.ai"),
    ("vLLM", "Движок: обрабатывает сотни запросов одновременно. Ollama достаточно одному пользователю, компании нужен vLLM.", "https://docs.vllm.ai"),
    ("LlamaIndex", "Для разработчиков: сборка своей логики поиска по документам и агентов.", "https://www.llamaindex.ai"),
    ("LangChain", "Для разработчиков: каркас для цепочек запросов, инструментов и агентов.", "https://www.langchain.com"),
])
c += h3("Запуск на своём компьютере", "Открытые модели DeepSeek, GLM, Qwen, Kimi и Xiaomi MiMo можно скачать и запустить без интернета.")
c += grid([
    ("Hugging Face", "Главный каталог открытых моделей и датасетов.", "https://huggingface.co"),
    ("LM Studio", "Программа для запуска моделей на компьютере в несколько кликов.", "https://lmstudio.ai"),
    ("Ollama", "Запуск моделей из командной строки или приложения.", "https://ollama.com"),
    ("Jan", "Бесплатная программа с открытым кодом для Windows, Mac и Linux.", "https://www.jan.ai"),
    '<div class="card"><b>' + logo("PocketPal") + 'PocketPal</b><p>' + T("Небольшие модели на телефоне, без интернета.") + '</p><small><a href="https://play.google.com/store/apps/details?id=com.pocketpalai" target="_blank" rel="noopener" style="text-decoration:underline">Android</a> · <a href="https://apps.apple.com/kz/app/pocketpal-ai/id6502579498" target="_blank" rel="noopener" style="text-decoration:underline">iOS</a></small></div>',
])
c += h3("Оборудование", "Для работы модели на своём оборудовании нужна общая память: чем её больше, тем крупнее модель можно запустить.")
c += grid([
    ("NVIDIA DGX Spark", "Настольный ИИ-компьютер на Linux со 128 ГБ общей памяти.", "https://www.nvidia.com/en-us/products/workstations/dgx-spark/"),
    ("NVIDIA RTX Spark", "Ноутбуки и компактные ПК на Windows: чип Grace Blackwell, до 128 ГБ общей памяти.", "https://nvidianews.nvidia.com/news/nvidia-microsoft-windows-pcs-agents-rtx-spark", "новое"),
    ("Мини-ПК на AMD Ryzen AI Max+", "Более доступная альтернатива DGX Spark: до 128 ГБ памяти.", "https://www.amd.com/en/products/processors/laptop/ryzen/ai-300-series/amd-ryzen-ai-max-plus-395.html"),
    ("Mac Studio", "Apple Silicon с большой общей памятью: тихий вариант для небольшой команды.", "https://www.apple.com/mac-studio/"),
])
c += h3("Дообучение моделей", "Нужно, когда важен строгий формат ответа или свой стиль. Чтобы ИИ просто отвечал по вашим документам, "
        "дообучение не нужно — для этого есть база знаний.")
c += grid([
    ("Unsloth", "Дообучение на одной видеокарте: быстрее и экономнее обычного способа.", "https://unsloth.ai"),
    ("LLaMA Factory", "Дообучение открытых моделей через интерфейс, без своего кода.", "https://github.com/hiyouga/LLaMA-Factory"),
    ("OpenAI Fine-tuning", "Дообучение в облаке: достаточно загрузить примеры и запустить обучение, отдельные специалисты не нужны.", "https://platform.openai.com/docs/guides/fine-tuning", None, False, "platform.openai.com"),
    ("Google Vertex AI", "Дообучение и запуск моделей в облаке Google.", "https://cloud.google.com/vertex-ai"),
])
out.append(sec("company", "06", "Внедрение ИИ в компании", None, tabify(c)))

# 8. detect
d = h3("Изображения, видео и аудио", "Отсутствие метки не означает, что файл создан человеком.")
d += grid([
    ("SynthID Detector", "Проверяет фото, видео и аудио на скрытую метку ИИ от Google, OpenAI, NVIDIA и Kakao. Бесплатно, около 10 проверок в день.", "https://synthid.com", "новое"),
])
d += h3("Текст")
d += grid([
    ("Pangram", "Детектор с самой низкой долей ложных срабатываний в независимых исследованиях.", "https://www.pangram.com"),
    ("GPTZero", "Популярный детектор, теперь часть Superhuman (Grammarly).", "https://gptzero.me"),
    ("Originality.ai", "Детектор с настройкой допустимой доли ИИ-текста, проверка плагиата и фактов.", "https://originality.ai"),
    ("Turnitin", "Стандарт проверки в университетах.", "https://www.turnitin.com/solutions/topics/ai-writing/", None, False, "turnitin.com"),
    ("Copyleaks", "Детектор и проверка плагиата на 30+ языках.", "https://copyleaks.com/ai-content-detector"),
])
d += '<p class="note">' + T("<b>Результат детектора — не доказательство.</b> Детекторы часто принимают текст человека за ИИ-текст, особенно если автор пишет не на родном языке. Используйте его как основание для дополнительной проверки, а не как окончательный вывод.") + "</p>"
d += h3("Проверка на плагиат")
d += grid([
    ("Grammarly", "Проверка плагиата бесплатно, полная версия в Grammarly Pro.", "https://www.grammarly.com/plagiarism-checker"),
    ("QuillBot", "Проверка на 100+ языках, входит в Premium.", "https://quillbot.com/plagiarism-checker"),
    ("Scribbr", "Проверка академических работ на технологии Turnitin.", "https://www.scribbr.com"),
])
out.append(sec("detect", "07", "Детекторы ИИ-контента", None, tabify(d)))

out.append("</div>")
out.append(f'<div class="cta"><div class="w"><div><h2>{T("Корпоративное обучение работе с ИИ")}</h2>'
           f'<p>{T("Корпоративные тренинги Академии бизнеса EY под задачи вашей компании.")}</p></div>'
           f'<a class="btn" href="{T("https://eyacademyeurasia.com/ai")}?utm_source=ai-guide" target="_blank" rel="noopener">{T("Узнать о программах")} &rarr;</a></div></div>')
out.append("</div>")
BODY = "\n".join(out)
