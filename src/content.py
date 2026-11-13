import html, re
from urllib.parse import urlparse

def dom(u):
    d = urlparse(u).netloc.replace("www.", "")
    p = urlparse(u).path.strip("/")
    return d + ("/" + p if p and len(d + p) < 26 and p.count("/") == 0 else "")

import json, os
BASE = globals().get("BASE") or ""
LOGO = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cardlogos.json"), encoding="utf-8"))


def logo(name, cls="cl", size=20):
    f = LOGO.get(name)
    return f'<img class="{cls}" src="{BASE}logos/{f}" width="{size}" height="{size}" alt="" loading="lazy">' if f else ""


def card(name, desc, url, tag=None, gray=False, small=None):
    t = f'<span class="tag{" g" if gray else ""}">{tag}</span>' if tag else ""
    return (f'<a class="card" href="{url}" target="_blank" rel="noopener"><b>{logo(name)}{name}{t}</b>'
            f'<p>{desc}</p><small>{small or dom(url)}</small></a>')

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
        f'<li><a href="{u}" target="_blank" rel="noopener"><em>{row(t)}{t}</em> <span>{s}</span></a></li>' for t, u, s in items) + "</ul>"

MODELS = globals().get("MODELS") or {}


def models(creator, fallback, n=4):
    return (MODELS.get(creator) or fallback)[:n]


def model(creator, fallback):
    return models(creator, [fallback], 1)[0]


VENDORS = []


def vendor(by, name, text, pills, lk):
    # Each big assistant becomes a tab: description and models on the left, links on the right.
    p = "".join(f'<span class="pill{" top" if i == 0 else ""}">{x}</span>' for i, x in enumerate(pills))
    VENDORS.append((name, f'<div class="vd"><div><span class="by">{by}</span><p>{text}</p><div class="pills">{p}</div></div>{links(lk, name)}</div>'))
    return ""


def vendor_tabs(extra):
    tabs = VENDORS + extra
    btns = "".join(f'<button type="button"{" class=on" if i == 0 else ""}>{logo(n, "tl", 16)}{n}</button>' for i, (n, _) in enumerate(tabs))
    panels = "".join(f'<div class="pl-panel"{" hidden" if i else ""}>{b}</div>' for i, (_, b) in enumerate(tabs))
    return f'<div class="pl-box"><div class="pl-tabs">{btns}</div>{panels}</div>'

def sec(id_, num, title, lead, body):
    l = f'<p class="sec-lead">{lead}</p>' if lead else ""
    return f'<section id="eyai-{id_}">\n<div class="sec-h"><span class="num">{num}</span><h2>{title}</h2></div>\n{l}\n{body}\n</section>\n'

SHORT = {"Агенты в рабочих чатах команды": "В чатах команды", "Агенты на вашем компьютере": "На компьютере",
         "Агенты в облаке, 24/7": "В облаке, 24/7", "Агенты на сервере компании": "На сервере компании",
         "MCP: подключение ИИ к вашим системам": "MCP", "Автоматизация без программирования": "Автоматизация",
         "Аватары и перевод видео": "Аватары и перевод", "Сайты и приложения без программирования": "Сайты и приложения",
         "Документы, презентации, инфографика": "Документы и презентации", "Запуск моделей на своём оборудовании": "Свои модели",
         "Фото, видео и аудио": "Фото, видео, аудио", "Проверка на плагиат": "Плагиат"}


def tabify(body):
    """Turn a run of h3 + caption + cards into one framed block with a tab per subsection."""
    tabs = []
    for part in [x for x in re.split(r"(?=<h3>)", body) if x.strip()]:
        m = re.match(r'<h3>(.*?)</h3>(?:<p class="cap">(.*?)</p>)?', part, re.S)
        tabs.append((m.group(1), m.group(2), part[m.end():]))
    btns = "".join(f'<button type="button"{" class=on" if i == 0 else ""}>{SHORT.get(t, t)}</button>' for i, (t, _, _) in enumerate(tabs))
    panels = "".join(f'<div class="pl-panel"{" hidden" if i else ""}>' + (f'<p class="pcap">{c}</p>' if c else "") + b + "</div>"
                     for i, (_, c, b) in enumerate(tabs))
    return f'<div class="pl-box"><div class="pl-tabs">{btns}</div>{panels}</div>'


def h3(t, cap=None):
    return f"<h3>{t}</h3>" + (f'<p class="cap">{cap}</p>' if cap else "")

NAV = [("rating", "Рейтинг"), ("llm", "Чат-боты"), ("agents", "ИИ-агенты"),
       ("media", "Креативы"), ("tools", "Полезные сервисы"), ("company", "ИИ в компании"), ("detect", "Детекторы")]

out = ['<div id="eyai" data-v="{VERSION}">', '<div class="toc"><div class="w">' +
       "".join(f'<a href="#eyai-{i}"><span>{n}</span>{t}</a>' for n, (i, t) in enumerate(NAV, 1)) + "</div></div>",
       '<div class="w">']

# 2. rating
rating = ('<div class="chart">{RATING_TABS}<div class="rt-main"><div class="chart-top"><span class="rt-cap">Топ-{CHART_N} моделей, баллы из 100</span><span class="rt-date">{CHART_DATE}</span></div>'
          '<ol class="bars">{CHART_BARS}</ol><div class="legend">{CHART_LEGEND}</div></div><div class="rt-value" hidden>{COMPARE}</div></div>'
          '<p class="src">Источник: <a href="https://artificialanalysis.ai" target="_blank" rel="noopener">Artificial Analysis</a></p>')
out.append(sec("rating", "01", "Рейтинг моделей",
               "Artificial Analysis Intelligence Index. Независимая лаборатория прогоняет модели через 10 тестов: агентные задачи, программирование, знания, научное мышление. Чем выше балл, тем лучше модель справляется со сложной работой.",
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
            "Понимает задачу с полуслова и пишет живым языком, поэтому текст меньше приходится править. Силён в программировании, длинных документах и долгой самостоятельной работе.",
            models("Anthropic", ["Claude Opus 5.5", "Claude Sonnet 5.5", "Claude Fable 5.1", "Claude Haiku 4.5"]),
            [("Чат", "https://claude.ai", "claude.ai"),
             ("Приложение: Cowork и Claude Code", "https://claude.com/download", "claude.com/download"),
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
PLAN_ROWS = [("ChatGPT", "Free, Go $8, Plus $20, Pro от $100", "Да, можно отключить", "Business $20–25"),
             ("Claude", "Free, Pro $20, Max $100, Ultra $200", "По выбору пользователя, при согласии хранение до 5 лет", "Team $20–25"),
             ("Gemini", "Free, AI Plus $5, AI Pro $20, Ultra от $100", "Да, можно отключить", "Google Workspace от $7, Gemini включён"),
             ("Copilot", "Бесплатно, Microsoft 365 Personal $10, Premium $20", "В новом приложении нет",
              "Copilot Chat бесплатно с M365, Microsoft 365 Copilot $21–30 + лицензия M365")]
kinds = ('<p class="pcap">Личная подписка может обучать модели на вашей переписке, пока это не отключить, и не даёт компании контроля. '
         'Бизнес-подписка на данных не обучает, даёт администратора, вход через корпоративный аккаунт и один счёт, подключается от 2 пользователей.</p>'
         '<div class="pl-wrap"><table class="pl pl-k"><tbody><tr class="pl-h"><th>Сервис</th><th>Личная подписка</th><th>Обучение на данных</th><th>Бизнес-подписка</th></tr>'
         + "".join(f'<tr><td><b>{logo(n, "pl-lg", 16)}{n}</b></td><td>{a}</td><td>{t}</td><td>{b}</td></tr>' for n, a, t, b in PLAN_ROWS)
         + '<tr><td><b>API</b></td><td>Оплата за объём запросов, без подписки</td><td>Не обучают по умолчанию, кроме бесплатного уровня Gemini API</td><td>—</td></tr>'
         '</tbody></table></div><p class="src">Цены за пользователя в месяц в долларах США. У бизнес-тарифов меньшая цена при оплате за год.</p>')
privacy = '<div class="grid">' + "".join(f'<div class="card"><b>{logo(a)}{a}</b><p>{t}</p></div>' for a, t in [
    ("ChatGPT", "Settings → Data controls → выключить «Improve the model for everyone». Временные чаты не используются для обучения."),
    ("Claude", "Settings → Privacy → выключить «Help improve Claude». Чаты в режиме инкогнито не используются для обучения."),
    ("Gemini", "Activity → выключить «Keep Activity». Временные чаты не используются для обучения."),
]) + "</div>"
llm += h3("Подписки", "Какие бывают, сколько стоят и сколько работы дают. Для рабочих документов берите бизнес-подписку: "
          "она стоит почти как личная, а данные компании остаются под её контролем.")
llm += ('<div class="pl-box"><div class="pl-tabs"><button type="button" class="on">Какие бывают</button>{SUBS_TABS}'
        '<button type="button">Как отключить обучение</button></div>'
        f'<div class="pl-panel">{kinds}</div>' + "{SUBS_PANELS}" + f'<div class="pl-panel" hidden>{privacy}</div></div>')
others = grid([
    ("DeepSeek", f"Сильная китайская модель {model('DeepSeek', 'DeepSeek V4.1 Flash')}. Бесплатный чат, веса можно скачать и запустить у себя.", "https://chat.deepseek.com", "открытая"),
    ("Perplexity", "Поиск в интернете с источниками под каждым ответом.", "https://www.perplexity.ai"),
    ("Grok", f"Модель {model('SpaceXAI', 'Grok 4.7')} от SpaceXAI. Встроен в соцсеть X.", "https://grok.com"),
    ("Genspark", "Чат, презентации, таблицы и исследования в одном месте.", "https://www.genspark.ai"),
    ("Meta AI", f"Ассистент на модели {model('Meta', 'Muse Spark 1.3')}. В Казахстане удобнее всего через WhatsApp.", "https://www.meta.ai"),
    ("Mistral Vibe", "Европейский чат-бот, до мая 2026 назывался Le Chat.", "https://chat.mistral.ai", "открытая"),
    ("Qwen", f"Модели Alibaba. Флагман {model('Alibaba', 'Qwen3.8 Max')}.", "https://chat.qwen.ai", "открытая"),
    ("Z.ai (GLM)", f"{model('Z AI', 'GLM-5.3')}, одна из сильнейших открытых моделей.", "https://chat.z.ai", "открытая"),
    ("Kimi", f"{model('Kimi', 'Kimi K3')} от Moonshot AI. Умеет запускать рой агентов для больших задач.", "https://www.kimi.com", "открытая"),
    ("t3.chat", "Одна подписка на модели разных компаний в одном окне.", "https://t3.chat"),
])
llm = vendor_tabs([("Другие чат-боты", others)]) + llm
out.append(sec("llm", "02", "Чат-боты и модели",
               "Для большинства задач хватит одного из четырёх сервисов ниже. У всех есть бесплатный тариф, но самые сильные модели открываются только в платных.", llm))

# 4. agents
ag = h3("Агенты в рабочих чатах команды", "Агент живёт там, где работает команда, и выполняет задачи по запросу, расписанию или событию.")
ag += grid([
    ("ChatGPT Workspace Agents", "Общие агенты команды: отчёты, ответы, подготовка документов. Работают в ChatGPT и Slack, по расписанию.", "https://chatgpt.com", "Business", True, "chatgpt.com"),
    ("Claude Tag", "Claude как участник Slack-канала: любой пишет @Claude и поручает задачу. Помнит контекст канала, может сам напоминать о важном.", "https://claude.com/product/tag", "Team", True),
    ("Copilot Agent Builder", "Простой агент внутри Microsoft 365: отвечает на вопросы и выполняет задачи по расписанию.", "https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder", None, False, "learn.microsoft.com"),
    ("Copilot Studio", "Агенты, которые реагируют на события и выполняют действия во внешних системах.", "https://copilotstudio.microsoft.com"),
])
ag += h3("Агенты на вашем компьютере", "Работают с вашими файлами, программами и браузером. Вы видите, что делает агент, и подтверждаете важные шаги.")
ag += grid([
    ("ChatGPT Work", "Режим ChatGPT для длинных задач: исследует, собирает документы, таблицы и презентации.", "https://chatgpt.com"),
    ("Claude Cowork", "Агент для офисной работы: файлы, программы, браузер. Готовит docx, xlsx, pptx, выполняет задачи по расписанию.", "https://claude.com/product/cowork"),
    ("Manus", "Универсальный агент: исследования, отчёты, сайты по одной задаче.", "https://manus.im"),
])
ag += h3("Агенты в облаке, 24/7", "Новый класс агентов: у каждого свой облачный компьютер с браузером. Ничего не нужно устанавливать, задачи идут даже при закрытом ноутбуке. Данные хранятся у поставщика.")
ag += grid([
    ("dots", "OpenAI, сентябрь 2026. Постоянные агенты на самой сильной модели OpenAI в ChatGPT, Slack и Teams. В фоне ищут, чем помочь.", "https://openai.com/index/introducing-dots/", "Pro", True, "openai.com"),
    ("Grok Bot", "SpaceXAI, август 2026. Команда ботов на одном облачном компьютере. Задачу можно показать, и бот запомнит порядок действий.", "https://x.ai/bot", "SuperGrok", True, "x.ai/bot"),
    ("Muse", "Meta, сентябрь 2026. Личный агент с отдельной виртуальной машиной. Агент Sentinel пропускает в интернет только одобренные действия.", "https://muse.ai", "только США", True),
    ("Gemini Spark", "Google. Агент работает круглосуточно, задачи можно ставить письмом в Gmail.", "https://gemini.google/overview/agent/spark/", "не во всех странах", True, "gemini.google"),
])
ag += h3("Агенты на сервере компании", "Открытый код: ставятся на ваш сервер или ноутбук, данные не уходят к поставщику. Работают с любой моделью, в том числе локальной. Установку и безопасность обеспечивает ИТ-отдел.")
ag += grid([
    ("OpenClaw", "Самый популярный открытый агент, около 390 тыс. звёзд на GitHub. Браузер, файлы, терминал; общается через WhatsApp, Telegram, Slack и другие мессенджеры.", "https://openclaw.ai", "открытый", False),
    ("Hermes Agent", "Nous Research. Ставится одной командой, сам создаёт навыки из выполненных задач и помнит контекст. 20+ каналов, включая Telegram и Teams.", "https://hermes-agent.nousresearch.com", "открытый", False, "nousresearch.com"),
    ("NVIDIA NemoClaw", "OpenClaw в защищённой среде NVIDIA с моделями Nemotron и правилами безопасности.", "https://www.nvidia.com/en-us/ai/nemoclaw/", "открытый", False),
])
ag += h3("Для разработчиков")
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
    ("Smithery", "Каталог MCP-серверов с установкой в пару кликов.", "https://smithery.ai"),
    ("Glama", "Самый большой каталог MCP-серверов с поиском.", "https://glama.ai/mcp/servers"),
    ("mcp.so", "Большой открытый каталог MCP-серверов от сообщества.", "https://mcp.so"),
])
ag += '<p class="note"><b>Агенты и MCP-серверы действуют сами.</b> Перед подключением к рабочим данным ограничьте права доступа и проверьте, кто автор сервера.</p>'
ag += h3("Автоматизация без программирования", "Цепочки действий между сервисами: письмо пришло, ИИ разобрал, задача появилась в CRM.")
ag += grid([
    ("n8n", "Гибкий конструктор с ИИ-агентами. Можно развернуть на серверах компании.", "https://n8n.io"),
    ("Zapier", "Облачная автоматизация для 9000+ приложений, свои агенты и MCP.", "https://zapier.com"),
    ("Make", "Визуальный конструктор сценариев с ветками и условиями.", "https://www.make.com/en", None, False, "make.com"),
])
out.append(sec("agents", "03", "ИИ-агенты",
               "Чат-бот отвечает на вопросы. Агент сам выполняет задачу: планирует шаги, пользуется инструментами и доводит работу до результата.", tabify(ag)))

# 5. media
m = ""
m += h3("Изображения")
m += grid([
    ("ChatGPT Images 2.5", "Генерация и точное редактирование прямо в ChatGPT. Читаемый текст на картинках, в том числе на кириллице.", "https://chatgpt.com"),
    ("Nano Banana 2 и Pro", "Модели Google для изображений, работают в приложении Gemini.", "https://deepmind.google/models/gemini-image/"),
    ("Midjourney", "Художественная генерация с сильным стилем. Версия V8.2.", "https://www.midjourney.com"),
    ("Grok Imagine", "Картинки и видео от SpaceXAI, в топ-5 рейтинга Artificial Analysis.", "https://grok.com/imagine"),
    ("Adobe Firefly", "Модели Adobe, Google, OpenAI и FLUX в одной подписке, безопасно для коммерческого использования.", "https://firefly.adobe.com"),
    ("FLUX", "Модели Black Forest Labs. Есть открытые веса и API.", "https://bfl.ai"),
    ("Freepik", "Фотосток и набор ИИ-инструментов для картинок и видео.", "https://www.freepik.com"),
])
m += h3("Видео")
m += grid([
    ("Higgsfield", "Казахстанский единорог: лучшие модели (Seedance, Kling, Veo, Nano Banana, Wan) и свои инструменты Cinema Studio, Soul ID и Speak. Выбор маркетологов для роликов в соцсети.", "https://higgsfield.ai", "из Казахстана"),
    ("Veo 3.1 и Google Flow", "Видео со звуком по тексту и картинкам. Flow это студия Google для монтажа сцен.", "https://flow.google.com"),
    ("Gemini Omni Flash", "Создание и правка видео в диалоге: «убери человека слева», «сделай закат».", "https://deepmind.google/models/gemini-omni/"),
    ("Seedance 2.5", "Модель ByteDance: ролики до 30 секунд. Доступна в Dreamina (CapCut) и Higgsfield.", "https://dreamina.capcut.com"),
    ("Kling", "Реалистичное видео и «оживление» фото. Kling 3.0, версия 4.0 выходит в октябре.", "https://kling.ai"),
    ("Wan 3.0", "Модель Alibaba, первое место в рейтинге видео Artificial Analysis. Ролики до 30 секунд со звуком.", "https://wan.video"),
    ("Hailuo", "Модель MiniMax H3: ролики в 2K до 15 секунд со стереозвуком.", "https://hailuoai.video"),
    ("Runway", "Профессиональный видеоредактор с ИИ.", "https://runway.com"),
    ("CapCut", "Популярный видеоредактор с ИИ-инструментами: субтитры, эффекты, монтаж.", "https://www.capcut.com"),
    ("VEED", "Видеоредактор прямо в браузере: автосубтитры, перевод и озвучка, ИИ-аватары, чистка звука. Удобен для роликов в соцсети.", "https://www.veed.io"),
])
m += h3("Аватары и перевод видео")
m += grid([
    ("HeyGen", "Цифровые аватары, дубляж и перевод видео на 175+ языков.", "https://www.heygen.com"),
    ("Synthesia", "Корпоративные обучающие видео с аватарами на 140+ языках.", "https://www.synthesia.io"),
    ("D-ID", "Говорящие аватары из фотографии и ИИ-агенты с лицом для сайта.", "https://www.d-id.com"),
])
m += h3("Голос и музыка")
m += grid([
    ("ElevenLabs", "Озвучка, клонирование голоса, дубляж. Лучшая модель речи в рейтинге, распознаёт казахскую речь.", "https://elevenlabs.io"),
    ("Suno", "Песни и фоновая музыка по описанию. Версия v6.", "https://suno.com"),
])
m += h3("Дизайн")
m += grid([
    ("Canva", "Шаблоны и Canva AI: посты, баннеры, презентации.", "https://www.canva.com"),
    ("Claude Design", "Слайды, одностраничники и прототипы по описанию. Экспорт в PPTX, PDF и Canva.", "https://claude.ai/design", None, False, "claude.ai/design"),
    ("Figma Make", "Кликабельный прототип интерфейса по описанию.", "https://www.figma.com/make/"),
])
out.append(sec("media", "04", "Креативы: фото, видео, голос",
               "Многие сервисы дают доступ к чужим моделям, поэтому одна и та же модель встречается в разных местах. Выбирайте по удобству и цене.", tabify(m)))

# 6. tools
t = h3("Сайты и приложения без программирования")
t += grid([
    ("Lovable", "Описываете словами, получаете рабочий сайт с базой данных. Публикация в один клик.", "https://lovable.dev"),
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
    ("Julius AI", "Загружаете таблицу, задаёте вопрос, получаете анализ и графики.", "https://julius.ai"),
])
t += h3("Встречи", "Сначала проверьте встроенные функции: Google Meet, Zoom и Teams уже умеют делать конспект встречи.")
t += grid([
    ("Granola", "Конспект встречи по звуку с компьютера, без бота в звонке.", "https://www.granola.ai"),
    ("Fireflies", "Бот записывает звонки и выгружает итоги в CRM.", "https://fireflies.ai"),
    ("tl;dv", "Запись и конспект встреч, хранение данных в ЕС.", "https://tldv.io"),
    ("Plaud", "Карманный диктофон с ИИ для офлайн-встреч.", "https://www.plaud.ai"),
])
out.append(sec("tools", "05", "Полезные сервисы", None, tabify(t)))

# 7. company
c = ""
c += h3("Где взять API")
c += grid([
    ("OpenAI", "Модели GPT. Вход через аккаунт ChatGPT.", "https://platform.openai.com"),
    ("Anthropic", "Модели Claude.", "https://platform.claude.com"),
    ("Google AI Studio", "Модели Gemini, есть бесплатный лимит.", "https://aistudio.google.com"),
    ("OpenRouter", "Один ключ для сотен моделей разных компаний.", "https://openrouter.ai"),
    ("Groq", "Очень быстрые ответы открытых моделей.", "https://groq.com"),
    ("DeepSeek", "Одни из самых низких цен среди сильных моделей.", "https://platform.deepseek.com"),
])
c += h3("Запуск моделей на своём оборудовании", "Открытые модели DeepSeek, GLM, Qwen, Kimi и Xiaomi MiMo можно скачать и запустить внутри компании.")
c += grid([
    ("Hugging Face", "Главный каталог открытых моделей и датасетов.", "https://huggingface.co"),
    ("LM Studio", "Программа для запуска моделей на компьютере в пару кликов.", "https://lmstudio.ai"),
    ("Ollama", "Запуск моделей из командной строки или приложения.", "https://ollama.com"),
    ("Jan", "Бесплатная программа с открытым кодом для Windows, Mac и Linux.", "https://www.jan.ai"),
    ("NVIDIA DGX Spark", "Настольный ИИ-компьютер со 128 ГБ памяти для больших моделей.", "https://www.nvidia.com/en-us/products/workstations/dgx-spark/"),
    ("Мини-ПК на AMD Ryzen AI Max+", "Дешёвая альтернатива DGX Spark: до 128 ГБ памяти.", "https://www.amd.com/en/products/processors/laptop/ryzen/ai-300-series/amd-ryzen-ai-max-plus-395.html"),
    ("Olares", "Готовая операционная система для локального ИИ.", "https://www.olares.com"),
    '<div class="card"><b>PocketPal</b><p>Небольшие модели на телефоне, без интернета.</p><small><a href="https://play.google.com/store/apps/details?id=com.pocketpalai" target="_blank" rel="noopener" style="text-decoration:underline">Android</a> · <a href="https://apps.apple.com/kz/app/pocketpal-ai/id6502579498" target="_blank" rel="noopener" style="text-decoration:underline">iOS</a></small></div>',
])
out.append(sec("company", "06", "ИИ в своей компании", None, tabify(c)))

# 8. detect
d = h3("Фото, видео и аудио", "Если метки нет, это ещё не значит, что файл создал человек.")
d += grid([
    ("SynthID Detector", "Проверяет фото, видео и аудио на скрытую метку ИИ от Google, OpenAI, NVIDIA и Kakao. Бесплатно, около 10 проверок в день.", "https://synthid.com", "новое"),
])
d += h3("Текст")
d += grid([
    ("Pangram", "Детектор с самой низкой долей ложных срабатываний в независимых исследованиях.", "https://www.pangram.com"),
    ("GPTZero", "Популярный детектор, теперь часть Superhuman (Grammarly).", "https://gptzero.me"),
    ("Originality.ai", "Детектор с настройкой допустимой доли ИИ-текста, проверка плагиата и фактов.", "https://originality.ai"),
    ("Turnitin", "Стандарт в университетах.", "https://www.turnitin.com/solutions/topics/ai-writing/", None, False, "turnitin.com"),
    ("Copyleaks", "Детектор и проверка плагиата на 30+ языках.", "https://copyleaks.com/ai-content-detector"),
])
d += '<p class="note"><b>Детекторам нельзя верить на слово.</b> Они часто принимают текст человека за ИИ-текст, особенно если автор пишет не на родном языке. Используйте результат как повод присмотреться, а не как доказательство.</p>'
d += h3("Проверка на плагиат")
d += grid([
    ("Grammarly", "Проверка плагиата бесплатно, полная версия в Grammarly Pro.", "https://www.grammarly.com/plagiarism-checker"),
    ("QuillBot", "Проверка на 100+ языках, входит в Premium.", "https://quillbot.com/plagiarism-checker"),
    ("Scribbr", "Проверка академических работ на технологии Turnitin.", "https://www.scribbr.com"),
])
out.append(sec("detect", "07", "Проверка: ИИ или не ИИ", None, tabify(d)))

out.append("</div>")
out.append('<div class="cta"><div class="w"><div><h2>Хотите научить команду работать с ИИ?</h2><p>Корпоративные тренинги Академии бизнеса EY под задачи вашей компании.</p></div>'
           '<a class="btn" href="https://eyacademyeurasia.com/ai?utm_source=ai-guide" target="_blank" rel="noopener">Узнать о программах &rarr;</a></div></div>')
out.append("</div>")
BODY = "\n".join(out)
